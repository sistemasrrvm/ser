"""
Sincroniza cliente_id / equipamento_id a partir de campos lookup nas respostas.
O kickoff cria relatório sem FKs; o wizard preenche apenas respostas JSON.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from sqlmodel import Session, select

from ..models.form_field import FormField
from ..models.form_page import FormPage
from ..models.manut_cliente import ManutCliente
from ..models.manut_equipamento import ManutEquipamento
from ..models.report import Report

CLIENTE_VIEW = "vw_tab_clientes_lookup"
EQUIPAMENTO_VIEW = "vw_tab_equipamentos_lookup"


def _parse_lookup_id(raw) -> Optional[int]:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _is_cliente_lookup(campo: FormField) -> bool:
    config = campo.configuracao or {}
    if config.get("target_view") == CLIENTE_VIEW:
        return True
    return campo.rotulo.strip().lower() == "cliente"


def _is_equipamento_lookup(campo: FormField) -> bool:
    config = campo.configuracao or {}
    if config.get("target_view") == EQUIPAMENTO_VIEW:
        return True
    return campo.rotulo.strip().lower() == "equipamento"


def load_template_lookup_fields(session: Session, template_id: int) -> List[FormField]:
    pages = session.exec(
        select(FormPage)
        .where(FormPage.formulario_id == template_id)
        .order_by(FormPage.ordem)
    ).all()
    if not pages:
        return []

    page_ids = [p.id for p in pages]
    return list(
        session.exec(
            select(FormField)
            .where(FormField.pagina_id.in_(page_ids))
            .where(FormField.tipo == "lookup")
            .order_by(FormField.ordem)
        ).all()
    )


def sync_report_foreign_keys(report: Report, session: Session) -> None:
    """Atualiza cliente_id / equipamento_id com base nos lookups das respostas."""
    respostas = report.respostas or {}
    if not respostas:
        return

    for campo in load_template_lookup_fields(session, report.form_template_id):
        campo_key = f"campo_{campo.id}"
        lookup_id = _parse_lookup_id(respostas.get(campo_key))
        if lookup_id is None:
            continue
        if _is_cliente_lookup(campo):
            report.cliente_id = lookup_id
        elif _is_equipamento_lookup(campo):
            report.equipamento_id = lookup_id


def resolve_cliente_equipamento_names(
    report: Report,
    session: Session,
    lookup_fields: List[FormField],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Nome para listagem/kanban: FK quando existir; senão label/id nas respostas.
    """
    respostas = report.respostas or {}
    cliente_nome: Optional[str] = None
    equipamento_nome: Optional[str] = None

    if report.cliente_id:
        cliente = session.get(ManutCliente, report.cliente_id)
        if cliente and cliente.CLI_NOME:
            cliente_nome = cliente.CLI_NOME

    if report.equipamento_id:
        equipamento = session.get(ManutEquipamento, report.equipamento_id)
        if equipamento and equipamento.EQP_NOME:
            equipamento_nome = equipamento.EQP_NOME

    for campo in lookup_fields:
        campo_key = f"campo_{campo.id}"
        label_key = f"{campo_key}_label"
        label = respostas.get(label_key)
        if isinstance(label, str):
            label = label.strip() or None

        if _is_cliente_lookup(campo) and not cliente_nome:
            cliente_nome = label
            if not cliente_nome:
                lookup_id = _parse_lookup_id(respostas.get(campo_key))
                if lookup_id:
                    cliente = session.get(ManutCliente, lookup_id)
                    if cliente and cliente.CLI_NOME:
                        cliente_nome = cliente.CLI_NOME

        if _is_equipamento_lookup(campo) and not equipamento_nome:
            equipamento_nome = label
            if not equipamento_nome:
                lookup_id = _parse_lookup_id(respostas.get(campo_key))
                if lookup_id:
                    equipamento = session.get(ManutEquipamento, lookup_id)
                    if equipamento and equipamento.EQP_NOME:
                        equipamento_nome = equipamento.EQP_NOME

    return cliente_nome, equipamento_nome


def build_lookup_fields_cache(
    session: Session, template_ids: List[int]
) -> Dict[int, List[FormField]]:
    cache: Dict[int, List[FormField]] = {}
    for template_id in set(template_ids):
        cache[template_id] = load_template_lookup_fields(session, template_id)
    return cache

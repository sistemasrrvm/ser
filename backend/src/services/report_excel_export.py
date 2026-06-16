"""
Preenchimento do template Excel na exportação de relatórios (#304).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Literal, Optional

from sqlmodel import Session, select

from ..models.form_field import FormField
from ..models.form_page import FormPage
from ..models.report import Report

CellValueType = Literal["number", "string"]


@dataclass
class CellPatch:
    """Valor pronto para gravar em planilha + célula (fonte única para openpyxl e COM)."""

    sheet_name: str
    cell: str
    value: Any
    value_type: CellValueType = "string"
    raw_value: Any = None
    field_config: dict = field(default_factory=dict)


def _raw_number_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    raw = str(value).strip()
    return raw if raw else None


def infer_decimal_places_from_raw(value: Any) -> int:
    """
    Conta casas decimais do valor gravado (ex.: "8.06" → 2, "8.6" → 1, "8" → 0).
    Não usa decimal_places do formulário — exporta na íntegra conforme salvo.
    """
    raw = _raw_number_string(value)
    if not raw:
        return 0

    normalized = raw.replace(" ", "")
    if "," in normalized and "." in normalized:
        decimal_sep = "," if normalized.rfind(",") > normalized.rfind(".") else "."
    elif "," in normalized:
        decimal_sep = ","
    elif "." in normalized:
        decimal_sep = "."
    else:
        return 0

    fractional = normalized.split(decimal_sep, 1)[1]
    return len(fractional)


def parse_number_value(value: Any) -> Optional[Decimal]:
    """Converte valor de campo number para Decimal (preserva casas decimais do texto)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None

    raw = _raw_number_string(value)
    if not raw:
        return None

    normalized = raw.replace(" ", "")
    if "," in normalized and "." in normalized:
        if normalized.rfind(",") > normalized.rfind("."):
            normalized = normalized.replace(".", "").replace(",", ".")
        else:
            normalized = normalized.replace(",", "")
    elif "," in normalized:
        normalized = normalized.replace(",", ".")

    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def number_format_pt_br(decimal_places: int) -> str:
    """Formato Excel com vírgula decimal (pt-BR)."""
    if decimal_places <= 0:
        return "0"
    return "0," + ("0" * decimal_places)


def apply_number_to_cell(cell, field_value: Any, configuracao: dict) -> None:
    """
    Grava valor numérico na célula conforme gravado em respostas (sem arredondar).
    configuracao é ignorada para casas decimais — usa precisão do valor salvo.
    """
    _ = configuracao  # mantido na assinatura por compatibilidade
    parsed = parse_number_value(field_value)

    if parsed is None:
        cell.value = None
        return

    decimal_places = infer_decimal_places_from_raw(field_value)

    if decimal_places == 0:
        cell.value = int(parsed)
        cell.number_format = "0"
        return

    cell.value = float(parsed)
    cell.number_format = number_format_pt_br(decimal_places)


def format_cell_value_for_display(cell) -> str:
    """Formata valor da célula para exibição no PDF (vírgula em decimais)."""
    if cell.value is None:
        return ""

    if isinstance(cell.value, int):
        return str(cell.value)

    if isinstance(cell.value, float):
        number_format = cell.number_format or ""
        decimal_places = 0
        if "," in number_format:
            decimal_places = len(number_format.split(",")[-1])
        if decimal_places > 0:
            return f"{cell.value:.{decimal_places}f}".replace(".", ",")
        if cell.value == int(cell.value):
            return str(int(cell.value))
        return str(cell.value).replace(".", ",")

    return str(cell.value)


def _resolve_sheet_name(workbook, planilha: str) -> Optional[str]:
    name = planilha.strip()
    if not name:
        return None
    if name in workbook.sheetnames:
        return name
    for sheet_name in workbook.sheetnames:
        if sheet_name.upper() == name.upper():
            return sheet_name
    return None


def compute_cell_patch(
    field,
    field_value: Any,
    planilha: str,
    celula: str,
    session: Session,
    format_date: Callable,
    format_yes_no: Callable,
    format_lookup: Callable,
) -> Optional[CellPatch]:
    """Calcula valor exportável para uma célula mapeada."""
    config = field.configuracao or {}
    sheet_name = planilha.strip()
    cell = celula.strip().upper()
    if not sheet_name or not cell:
        return None

    if field.tipo == "date":
        date_format = config.get("date_format", "dd_mm_yyyy")
        return CellPatch(
            sheet_name=sheet_name,
            cell=cell,
            value=format_date(field_value, date_format),
            value_type="string",
            raw_value=field_value,
            field_config=config,
        )
    if field.tipo == "yes_no":
        export_format = config.get("export_yes_no_value", "sim_nao")
        return CellPatch(
            sheet_name=sheet_name,
            cell=cell,
            value=format_yes_no(field_value, export_format),
            value_type="string",
            raw_value=field_value,
            field_config=config,
        )
    if field.tipo == "lookup":
        return CellPatch(
            sheet_name=sheet_name,
            cell=cell,
            value=format_lookup(session, field, field_value),
            value_type="string",
            raw_value=field_value,
            field_config=config,
        )
    if field.tipo == "number":
        parsed = parse_number_value(field_value)
        if parsed is None:
            return CellPatch(
                sheet_name=sheet_name,
                cell=cell,
                value=None,
                value_type="number",
                raw_value=field_value,
                field_config=config,
            )
        decimal_places = infer_decimal_places_from_raw(field_value)
        if decimal_places == 0:
            numeric = int(parsed)
        else:
            numeric = float(parsed)
        return CellPatch(
            sheet_name=sheet_name,
            cell=cell,
            value=numeric,
            value_type="number",
            raw_value=field_value,
            field_config=config,
        )

    return CellPatch(
        sheet_name=sheet_name,
        cell=cell,
        value=str(field_value) if field_value is not None else "",
        value_type="string",
        raw_value=field_value,
        field_config=config,
    )


def build_export_patches(
    report: Report,
    session: Session,
    *,
    format_date: Callable,
    format_yes_no: Callable,
    format_lookup: Callable,
) -> list[CellPatch]:
    """Lista patches a partir do excel_mapping de todos os campos do formulário."""
    patches: list[CellPatch] = []
    pages = session.exec(
        select(FormPage)
        .where(FormPage.formulario_id == report.form_template_id)
        .order_by(FormPage.ordem)
    ).all()

    for page in pages:
        fields = session.exec(
            select(FormField)
            .where(FormField.pagina_id == page.id)
            .order_by(FormField.ordem)
        ).all()

        for fld in fields:
            field_value = report.respostas.get(f"campo_{fld.id}")
            if field_value is None:
                continue

            excel_mapping = (fld.configuracao or {}).get("excel_mapping", [])
            if not excel_mapping:
                continue

            for mapping in excel_mapping:
                planilha = (mapping.get("planilha") or "").strip()
                celula = (mapping.get("celula") or "").strip().upper()
                if not planilha or not celula:
                    continue
                patch = compute_cell_patch(
                    fld,
                    field_value,
                    planilha,
                    celula,
                    session,
                    format_date,
                    format_yes_no,
                    format_lookup,
                )
                if patch:
                    patches.append(patch)

    return patches


def apply_patch_to_openpyxl_sheet(sheet, patch: CellPatch) -> None:
    """Grava patch em worksheet openpyxl (números com formato pt-BR)."""
    if patch.value_type == "number":
        apply_number_to_cell(sheet[patch.cell], patch.raw_value, patch.field_config)
        return
    sheet[patch.cell] = patch.value


def fill_workbook_from_report(
    workbook,
    report: Report,
    session: Session,
    *,
    format_date: Callable,
    format_yes_no: Callable,
    format_lookup: Callable,
) -> None:
    """Preenche o workbook com os valores mapeados de excel_mapping."""
    patches = build_export_patches(
        report,
        session,
        format_date=format_date,
        format_yes_no=format_yes_no,
        format_lookup=format_lookup,
    )

    for patch in patches:
        try:
            resolved_sheet = _resolve_sheet_name(workbook, patch.sheet_name)
            if not resolved_sheet:
                continue
            apply_patch_to_openpyxl_sheet(workbook[resolved_sheet], patch)
        except Exception as e:
            print(
                f"Erro ao escrever na célula {patch.cell} da planilha {patch.sheet_name}: {str(e)}"
            )

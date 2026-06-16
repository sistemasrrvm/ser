"""
API v1: Equipamentos
Endpoints para gerenciar equipamentos (tab_equipamentos - NR13)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import asc, desc
from sqlmodel import Session, select, func
from typing import Optional, Literal
import math

from ...core import get_session, get_current_user
from ...core.dependencies import require_suporte_or_admin
from ...core.list_sort import apply_list_sort
from ...models import ManutEquipamento, ManutCliente, User
from ...schemas import (
    ManutEquipamentoResponse,
    ManutEquipamentoListResponse,
    SyncStatusResponse,
)
from ...schemas.nr13_sync import Nr13SyncResponse

router = APIRouter(prefix="/equipamentos", tags=["Equipamentos"])

EQUIPAMENTOS_SORT_COLUMNS = {
    "EQP_ID": "EQP_ID",
    "EQP_TAG": "EQP_TAG",
    "EQP_NOME": "EQP_NOME",
    "EQP_NUMERO_SERIE": "EQP_NUMERO_SERIE",
    "EQP_AREA": "EQP_AREA",
    "EQP_CLI_ID": "EQP_CLI_ID",
    "CLI_NOME": "CLI_NOME",
    "EQP_TEQP_ID": "EQP_TEQP_ID",
    "EQP_DT_INS": "EQP_DT_INS",
    "EQP_DT_UPD": "EQP_DT_UPD",
}


@router.get("", response_model=ManutEquipamentoListResponse, status_code=status.HTTP_200_OK)
async def list_equipamentos(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    equipamento_id: Optional[int] = Query(None, description="Filtrar por EQP_ID"),
    tag: Optional[str] = Query(None, description="Filtrar por TAG (contém)"),
    nome: Optional[str] = Query(None, description="Filtrar por nome do equipamento (contém)"),
    numero_serie: Optional[str] = Query(None, description="Filtrar por número de série (contém)"),
    area: Optional[str] = Query(None, description="Filtrar por área (contém)"),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente (CLI_ID)"),
    cliente_nome: Optional[str] = Query(None, description="Filtrar por nome do cliente (contém)"),
    tipo_equipamento_id: Optional[int] = Query(None, description="Filtrar por tipo (TEQP_ID)"),
    search: Optional[str] = Query(None, description="Busca legada por TAG, nome ou número de série"),
    sort_by: Optional[str] = Query(None, description="Campo para ordenação"),
    sort_dir: Literal["asc", "desc"] = Query("asc", description="Direção da ordenação"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Listar equipamentos (tab_equipamentos - NR13) com join em tab_clientes."""
    statement = (
        select(ManutEquipamento, ManutCliente.CLI_NOME)
        .join(ManutCliente, ManutEquipamento.EQP_CLI_ID == ManutCliente.CLI_ID, isouter=True)
    )

    if equipamento_id is not None:
        statement = statement.where(ManutEquipamento.EQP_ID == equipamento_id)

    if tag and tag.strip():
        statement = statement.where(ManutEquipamento.EQP_TAG.contains(tag.strip()))

    if nome and nome.strip():
        statement = statement.where(ManutEquipamento.EQP_NOME.contains(nome.strip()))

    if numero_serie and numero_serie.strip():
        statement = statement.where(ManutEquipamento.EQP_NUMERO_SERIE.contains(numero_serie.strip()))

    if area and area.strip():
        statement = statement.where(ManutEquipamento.EQP_AREA.contains(area.strip()))

    if cliente_id is not None:
        statement = statement.where(ManutEquipamento.EQP_CLI_ID == cliente_id)

    if cliente_nome and cliente_nome.strip():
        statement = statement.where(ManutCliente.CLI_NOME.contains(cliente_nome.strip()))

    if tipo_equipamento_id is not None:
        statement = statement.where(ManutEquipamento.EQP_TEQP_ID == tipo_equipamento_id)

    has_field_filters = any(
        [
            equipamento_id is not None,
            tag and tag.strip(),
            nome and nome.strip(),
            numero_serie and numero_serie.strip(),
            area and area.strip(),
            cliente_id is not None,
            cliente_nome and cliente_nome.strip(),
            tipo_equipamento_id is not None,
        ]
    )

    if search and not has_field_filters:
        search_filter = (
            (ManutEquipamento.EQP_TAG.contains(search))
            | (ManutEquipamento.EQP_NOME.contains(search))
            | (ManutEquipamento.EQP_NUMERO_SERIE.contains(search))
        )
        statement = statement.where(search_filter)

    count_statement = select(func.count()).select_from(statement.subquery())
    total = session.exec(count_statement).one()

    sort_key = sort_by or "EQP_TAG"
    if sort_key not in EQUIPAMENTOS_SORT_COLUMNS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": f"sort_by inválido: '{sort_by}'",
                "allowed": list(EQUIPAMENTOS_SORT_COLUMNS.keys()),
            },
        )

    if sort_key == "CLI_NOME":
        order_col = ManutCliente.CLI_NOME
        statement = statement.order_by(desc(order_col) if sort_dir == "desc" else asc(order_col))
    else:
        statement = apply_list_sort(
            statement,
            ManutEquipamento,
            sort_by,
            sort_dir,
            EQUIPAMENTOS_SORT_COLUMNS,
            "EQP_TAG",
        )

    offset = (page - 1) * page_size
    rows = session.exec(statement.offset(offset).limit(page_size)).all()
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    items = [
        ManutEquipamentoResponse.model_validate(equip).model_copy(update={"CLI_NOME": cli_nome})
        for equip, cli_nome in rows
    ]

    return ManutEquipamentoListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/status", response_model=SyncStatusResponse, status_code=status.HTTP_200_OK)
async def get_equipamentos_status(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Status da tabela tab_equipamentos."""
    from ...services.nr13_config import get_nr13_runtime_config

    total = session.exec(select(func.count()).select_from(ManutEquipamento)).one()
    ultima_sinc = session.exec(select(func.max(ManutEquipamento.EQP_DT_UPD))).one()
    nr13_cfg = get_nr13_runtime_config(session)

    return SyncStatusResponse(
        tabela="tab_equipamentos",
        total_registros=total,
        ultima_sinc=ultima_sinc,
        proxima_sinc=None,
        nr13_data_ref_days_back=nr13_cfg.data_ref_days_back,
    )


@router.get("/{equipamento_id}", response_model=ManutEquipamentoResponse, status_code=status.HTTP_200_OK)
async def get_equipamento(
    equipamento_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Obter equipamento por ID (EQP_ID)."""
    statement = select(ManutEquipamento).where(ManutEquipamento.EQP_ID == equipamento_id)
    equipamento = session.exec(statement).first()

    if not equipamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipamento com ID {equipamento_id} não encontrado",
        )

    return ManutEquipamentoResponse.model_validate(equipamento)


@router.post("/sync", response_model=Nr13SyncResponse, status_code=status.HTTP_200_OK)
async def sync_equipamentos_from_nr13(
    sem_filtro_data: bool = Query(False, description="Não envia dataRef — carga sem filtro de data"),
    cliente_id: Optional[int] = Query(None, description="Filtrar carga NR13 por cliente (clienteId na API Botset)"),
    current_user: User = Depends(require_suporte_or_admin),
    session: Session = Depends(get_session),
):
    """Carrega equipamentos via API NR13 (opcionalmente filtrado por cliente)."""
    from ...services.nr13_api_sync import sync_equipamentos

    if cliente_id is not None:
        cliente = session.get(ManutCliente, cliente_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente com ID {cliente_id} não encontrado",
            )

    return await sync_equipamentos(
        session,
        sem_filtro_data=sem_filtro_data,
        cliente_id=cliente_id,
    )

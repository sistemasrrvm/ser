"""
API v1: Tipos de Equipamento
Endpoints para listar tipos (tab_tipos_equipamento - NR13)
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from typing import Optional, Literal

from ...core import get_session, get_current_user
from ...core.list_query import paginate_sorted
from ...models import ManutTipoEquipamento, User
from ...schemas import (
    ManutTipoEquipamentoListResponse,
    ManutTipoEquipamentoResponse,
    SyncStatusResponse,
)

router = APIRouter(prefix="/tipos-equipamento", tags=["Tipos de Equipamento"])

TIPOS_SORT_COLUMNS = {
    "TEQP_ID": "TEQP_ID",
    "TEQP_NOME": "TEQP_NOME",
    "TEQP_VENC_CALIBRACAO": "TEQP_VENC_CALIBRACAO",
    "TEQP_REQUER_INSPECAO_EXTERNA": "TEQP_REQUER_INSPECAO_EXTERNA",
    "TEQP_REQUER_INSPECAO_INTERNA": "TEQP_REQUER_INSPECAO_INTERNA",
    "TEQP_DT_INS": "TEQP_DT_INS",
    "TEQP_DT_UPD": "TEQP_DT_UPD",
}


@router.get("", response_model=ManutTipoEquipamentoListResponse)
async def list_tipos_equipamento(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar por nome"),
    sort_by: Optional[str] = Query(None, description="Campo para ordenação"),
    sort_dir: Literal["asc", "desc"] = Query("asc", description="Direção da ordenação"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Listar tipos de equipamento (tab_tipos_equipamento - NR13)."""
    statement = select(ManutTipoEquipamento)

    if search:
        statement = statement.where(ManutTipoEquipamento.TEQP_NOME.contains(search))

    results, total, total_pages = paginate_sorted(
        session,
        statement,
        ManutTipoEquipamento,
        page,
        page_size,
        sort_by,
        sort_dir,
        TIPOS_SORT_COLUMNS,
        "TEQP_NOME",
    )

    return ManutTipoEquipamentoListResponse(
        items=[ManutTipoEquipamentoResponse.model_validate(item) for item in results],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/status", response_model=SyncStatusResponse)
async def get_tipos_equipamento_status(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Status da tabela tab_tipos_equipamento."""
    total = session.exec(select(func.count()).select_from(ManutTipoEquipamento)).one()
    ultima_sinc = session.exec(select(func.max(ManutTipoEquipamento.TEQP_DT_UPD))).one()

    return SyncStatusResponse(
        tabela="tab_tipos_equipamento",
        total_registros=total,
        ultima_sinc=ultima_sinc,
        proxima_sinc=None,
    )

"""
API v1 - Dados NR13 (legado /manut/*)
Mantido para compatibilidade; delega às mesmas tabelas tab_*.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, select, func
from typing import Optional, Literal

from ...core.dependencies import get_session, get_current_user, require_suporte_or_admin
from ...core.list_query import paginate_sorted
from ...models import User, ManutCliente, ManutTipoEquipamento, ManutEquipamento
from ...schemas import (
    ManutClienteListResponse,
    ManutClienteResponse,
    ManutTipoEquipamentoListResponse,
    ManutTipoEquipamentoResponse,
    ManutEquipamentoListResponse,
    ManutEquipamentoResponse,
    SyncStatusResponse,
)
from .clientes import CLIENTES_SORT_COLUMNS
from .equipamentos import EQUIPAMENTOS_SORT_COLUMNS
from .tipos_equipamento import TIPOS_SORT_COLUMNS

router = APIRouter(prefix="/manut", tags=["Dados NR13"])


@router.get("/clientes", response_model=ManutClienteListResponse)
async def list_manut_clientes(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_dir: Literal["asc", "desc"] = Query("asc"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = select(ManutCliente)
    if search:
        statement = statement.where(
            (ManutCliente.CLI_NOME.contains(search))
            | (ManutCliente.CLI_CNPJ.contains(search))
        )

    results, total, total_pages = paginate_sorted(
        session, statement, ManutCliente, page, page_size,
        sort_by, sort_dir, CLIENTES_SORT_COLUMNS, "CLI_NOME",
    )

    return ManutClienteListResponse(
        items=[ManutClienteResponse.model_validate(item) for item in results],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


@router.get("/clientes/status", response_model=SyncStatusResponse)
async def get_clientes_sync_status(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    total = session.exec(select(func.count()).select_from(ManutCliente)).one()
    ultima_sinc = session.exec(select(func.max(ManutCliente.CLI_DT_UPD))).one()
    return SyncStatusResponse(
        tabela="tab_clientes", total_registros=total,
        ultima_sinc=ultima_sinc, proxima_sinc=None,
    )


@router.get("/tipos-equipamento", response_model=ManutTipoEquipamentoListResponse)
async def list_manut_tipos_equipamento(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_dir: Literal["asc", "desc"] = Query("asc"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = select(ManutTipoEquipamento)
    if search:
        statement = statement.where(ManutTipoEquipamento.TEQP_NOME.contains(search))

    results, total, total_pages = paginate_sorted(
        session, statement, ManutTipoEquipamento, page, page_size,
        sort_by, sort_dir, TIPOS_SORT_COLUMNS, "TEQP_NOME",
    )

    return ManutTipoEquipamentoListResponse(
        items=[ManutTipoEquipamentoResponse.model_validate(item) for item in results],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


@router.get("/tipos-equipamento/status", response_model=SyncStatusResponse)
async def get_tipos_equipamento_sync_status(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    total = session.exec(select(func.count()).select_from(ManutTipoEquipamento)).one()
    ultima_sinc = session.exec(select(func.max(ManutTipoEquipamento.TEQP_DT_UPD))).one()
    return SyncStatusResponse(
        tabela="tab_tipos_equipamento", total_registros=total,
        ultima_sinc=ultima_sinc, proxima_sinc=None,
    )


@router.get("/equipamentos", response_model=ManutEquipamentoListResponse)
async def list_manut_equipamentos(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    cliente_id: Optional[int] = Query(None),
    tipo_equipamento_id: Optional[int] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_dir: Literal["asc", "desc"] = Query("asc"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    statement = select(ManutEquipamento)
    if search:
        statement = statement.where(
            (ManutEquipamento.EQP_TAG.contains(search))
            | (ManutEquipamento.EQP_NOME.contains(search))
            | (ManutEquipamento.EQP_NUMERO_SERIE.contains(search))
        )
    if cliente_id is not None:
        statement = statement.where(ManutEquipamento.EQP_CLI_ID == cliente_id)
    if tipo_equipamento_id is not None:
        statement = statement.where(ManutEquipamento.EQP_TEQP_ID == tipo_equipamento_id)

    results, total, total_pages = paginate_sorted(
        session, statement, ManutEquipamento, page, page_size,
        sort_by, sort_dir, EQUIPAMENTOS_SORT_COLUMNS, "EQP_TAG",
    )

    return ManutEquipamentoListResponse(
        items=[ManutEquipamentoResponse.model_validate(item) for item in results],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


@router.get("/equipamentos/status", response_model=SyncStatusResponse)
async def get_equipamentos_sync_status(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    total = session.exec(select(func.count()).select_from(ManutEquipamento)).one()
    ultima_sinc = session.exec(select(func.max(ManutEquipamento.EQP_DT_UPD))).one()
    return SyncStatusResponse(
        tabela="tab_equipamentos", total_registros=total,
        ultima_sinc=ultima_sinc, proxima_sinc=None,
    )


@router.post("/sync", status_code=status.HTTP_200_OK)
async def trigger_manut_sync(
    current_user: User = Depends(require_suporte_or_admin),
    session: Session = Depends(get_session),
):
    """Sincroniza clientes e equipamentos via API NR13 (compatibilidade legado)."""
    from ...services.nr13_api_sync import sync_nightly

    result = await sync_nightly(session)
    return {
        "success": result.success,
        "results": {
            "clientes": result.results["clientes"].model_dump(),
            "equipamentos": result.results["equipamentos"].model_dump(),
            "tipos_equipamento": {
                "success": True,
                "total": 0,
                "message": "Não aplicável — tipos não sincronizados via API NR13",
            },
        },
        "timestamp": result.timestamp.isoformat(),
        "message": result.message,
    }

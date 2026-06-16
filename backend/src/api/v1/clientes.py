"""
API v1: Clientes
Endpoints para gerenciar clientes (tab_clientes - NR13)
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import Optional, Literal

from ...core import get_session, get_current_user
from ...core.dependencies import require_suporte_or_admin
from ...core.list_query import paginate_sorted
from ...models import ManutCliente, User
from ...schemas import (
    ManutClienteResponse,
    ManutClienteListResponse,
    SyncStatusResponse,
)
from ...schemas.nr13_sync import Nr13SyncResponse

router = APIRouter(prefix="/clientes", tags=["Clientes"])

CLIENTES_SORT_COLUMNS = {
    "CLI_ID": "CLI_ID",
    "CLI_NOME": "CLI_NOME",
    "CLI_CNPJ": "CLI_CNPJ",
    "CLI_SITE": "CLI_SITE",
    "CLI_CONTATO": "CLI_CONTATO",
    "CLI_EMAIL": "CLI_EMAIL",
    "CLI_TELEFONE": "CLI_TELEFONE",
    "CLI_CIDADE": "CLI_CIDADE",
    "CLI_ESTADO": "CLI_ESTADO",
    "CLI_DT_INS": "CLI_DT_INS",
    "CLI_DT_UPD": "CLI_DT_UPD",
}


@router.get("", response_model=ManutClienteListResponse, status_code=status.HTTP_200_OK)
async def list_clientes(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Buscar por nome ou CNPJ (legado)"),
    cliente_id: Optional[int] = Query(None, description="Filtrar por CLI_ID"),
    nome: Optional[str] = Query(None, description="Filtrar por nome (contém)"),
    cnpj: Optional[str] = Query(None, description="Filtrar por CNPJ (contém)"),
    sort_by: Optional[str] = Query(None, description="Campo para ordenação"),
    sort_dir: Literal["asc", "desc"] = Query("asc", description="Direção da ordenação"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Listar clientes (tab_clientes - NR13)."""
    statement = select(ManutCliente)

    if cliente_id is not None:
        statement = statement.where(ManutCliente.CLI_ID == cliente_id)

    if nome and nome.strip():
        statement = statement.where(ManutCliente.CLI_NOME.contains(nome.strip()))

    if cnpj and cnpj.strip():
        cnpj_term = cnpj.strip()
        cnpj_digits = re.sub(r"\D", "", cnpj_term)
        if cnpj_digits:
            statement = statement.where(ManutCliente.CLI_CNPJ.contains(cnpj_digits))
        else:
            statement = statement.where(ManutCliente.CLI_CNPJ.contains(cnpj_term))

    if search and not (cliente_id is not None or nome or cnpj):
        search_filter = (
            (ManutCliente.CLI_NOME.contains(search))
            | (ManutCliente.CLI_CNPJ.contains(search))
        )
        statement = statement.where(search_filter)

    results, total, total_pages = paginate_sorted(
        session,
        statement,
        ManutCliente,
        page,
        page_size,
        sort_by,
        sort_dir,
        CLIENTES_SORT_COLUMNS,
        "CLI_NOME",
    )

    return ManutClienteListResponse(
        items=[ManutClienteResponse.model_validate(c) for c in results],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/status", response_model=SyncStatusResponse, status_code=status.HTTP_200_OK)
async def get_clientes_status(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Status da tabela tab_clientes."""
    from ...services.nr13_config import get_nr13_runtime_config

    total = session.exec(select(func.count()).select_from(ManutCliente)).one()
    ultima_sinc = session.exec(select(func.max(ManutCliente.CLI_DT_UPD))).one()
    nr13_cfg = get_nr13_runtime_config(session)

    return SyncStatusResponse(
        tabela="tab_clientes",
        total_registros=total,
        ultima_sinc=ultima_sinc,
        proxima_sinc=None,
        nr13_data_ref_days_back=nr13_cfg.data_ref_days_back,
    )


@router.get("/{cliente_id}", response_model=ManutClienteResponse, status_code=status.HTTP_200_OK)
async def get_cliente(
    cliente_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Obter cliente por ID (CLI_ID)."""
    statement = select(ManutCliente).where(ManutCliente.CLI_ID == cliente_id)
    cliente = session.exec(statement).first()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente com ID {cliente_id} não encontrado",
        )

    return ManutClienteResponse.model_validate(cliente)


@router.post("/sync", response_model=Nr13SyncResponse, status_code=status.HTTP_200_OK)
async def sync_clientes_from_nr13(
    sem_filtro_data: bool = Query(False, description="Não envia dataRef — carga sem filtro de data"),
    data_ref: Optional[str] = None,
    current_user: User = Depends(require_suporte_or_admin),
    session: Session = Depends(get_session),
):
    """Carrega clientes via API NR13 (incremental com dataRef ou carga completa)."""
    from ...services.nr13_api_sync import sync_clientes

    return await sync_clientes(session, data_ref, sem_filtro_data=sem_filtro_data)


@router.post(
    "/{cliente_id}/sync-equipamentos",
    response_model=Nr13SyncResponse,
    status_code=status.HTTP_200_OK,
)
async def sync_equipamentos_do_cliente(
    cliente_id: int,
    sem_filtro_data: bool = Query(False, description="Não envia dataRef na API Botset"),
    current_user: User = Depends(require_suporte_or_admin),
    session: Session = Depends(get_session),
):
    """Carrega equipamentos NR13 de um cliente (body Botset: clienteId + dataRef + equipamentoTipo)."""
    cliente = session.get(ManutCliente, cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente com ID {cliente_id} não encontrado",
        )

    from ...services.nr13_api_sync import sync_equipamentos

    return await sync_equipamentos(
        session,
        sem_filtro_data=sem_filtro_data,
        cliente_id=cliente_id,
    )

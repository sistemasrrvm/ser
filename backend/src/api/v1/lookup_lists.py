"""
Rotas para gerenciamento de Listas Lookup
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime
import httpx

from ...core.database import get_session
from ...core.dependencies import get_current_user, require_admin
from ...models.user import User
from ...models.lookup_list import LookupList
from ...schemas.lookup_list import (
    LookupListCreate,
    LookupListUpdate,
    LookupListUpdateOptions,
    LookupListResponse,
    LookupListListResponse,
    LookupListOptionsResponse
)
from ...core.colored_logging import log_info, log_error, log_warning

router = APIRouter(prefix="/lookup-lists", tags=["Lookup Lists"])


@router.get("", response_model=LookupListListResponse, status_code=status.HTTP_200_OK)
async def list_lookup_lists(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Listar todas as listas lookup
    Requer: autenticação
    """
    statement = select(LookupList).order_by(LookupList.nome)
    listas = session.exec(statement).all()

    return LookupListListResponse(
        total=len(listas),
        listas=listas
    )


@router.get("/{list_id}", response_model=LookupListResponse, status_code=status.HTTP_200_OK)
async def get_lookup_list(
    list_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Obter lista lookup específica
    Requer: autenticação
    """
    lista = session.get(LookupList, list_id)

    if not lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lista '{list_id}' não encontrada"
        )

    return lista


@router.post("", response_model=LookupListResponse, status_code=status.HTTP_201_CREATED)
async def create_lookup_list(
    lista_data: LookupListCreate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Criar nova lista lookup
    Requer: admin
    """
    # Verificar se ID já existe
    existing = session.get(LookupList, lista_data.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe uma lista com ID '{lista_data.id}'"
        )

    # Verificar se nome já existe
    statement = select(LookupList).where(LookupList.nome == lista_data.nome)
    existing_nome = session.exec(statement).first()
    if existing_nome:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe uma lista com nome '{lista_data.nome}'"
        )

    # Criar lista
    nova_lista = LookupList(**lista_data.model_dump())
    session.add(nova_lista)
    session.commit()
    session.refresh(nova_lista)

    log_info(f"[LOOKUP_LIST] Lista '{lista_data.id}' criada por {current_user.username}")

    return nova_lista


@router.put("/{list_id}", response_model=LookupListResponse, status_code=status.HTTP_200_OK)
async def update_lookup_list(
    list_id: str,
    lista_data: LookupListUpdate,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Atualizar lista lookup
    Requer: admin
    """
    lista = session.get(LookupList, list_id)

    if not lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lista '{list_id}' não encontrada"
        )

    # Verificar se nome já existe em outra lista
    if lista_data.nome and lista_data.nome != lista.nome:
        statement = select(LookupList).where(LookupList.nome == lista_data.nome)
        existing_nome = session.exec(statement).first()
        if existing_nome:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe uma lista com nome '{lista_data.nome}'"
            )

    # Atualizar campos
    update_data = lista_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(lista, key, value)

    lista.atualizado_em = datetime.utcnow()
    session.add(lista)
    session.commit()
    session.refresh(lista)

    log_info(f"[LOOKUP_LIST] Lista '{list_id}' atualizada por {current_user.username}")

    return lista


@router.delete("/{list_id}", status_code=status.HTTP_200_OK)
async def delete_lookup_list(
    list_id: str,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Deletar lista lookup
    Requer: admin
    """
    lista = session.get(LookupList, list_id)

    if not lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lista '{list_id}' não encontrada"
        )

    session.delete(lista)
    session.commit()

    log_info(f"[LOOKUP_LIST] Lista '{list_id}' deletada por {current_user.username}")

    return {
        "message": f"Lista '{lista.nome}' deletada com sucesso",
        "id": list_id
    }


@router.get("/{list_id}/options", response_model=LookupListOptionsResponse, status_code=status.HTTP_200_OK)
async def get_lookup_options(
    list_id: str,
    search: Optional[str] = None,
    filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Obter opções de uma lista, com filtros opcionais
    Requer: autenticação

    Query params:
    - search: termo de busca no campo 'label'
    - filter: valor para filtrar pelo campo 'filter' das opções (filtro dependente)
    """
    lista = session.get(LookupList, list_id)

    if not lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lista '{list_id}' não encontrada"
        )

    opcoes = lista.opcoes

    # Aplicar busca no label se fornecido
    if search:
        search_lower = search.lower()
        opcoes = [
            opt for opt in opcoes
            if search_lower in opt.get('label', '').lower()
        ]

    # Aplicar filtro dependente se fornecido
    if filter:
        opcoes = [
            opt for opt in opcoes
            if opt.get('filter') == filter
        ]

    return LookupListOptionsResponse(
        list_id=list_id,
        opcoes=opcoes,
        total=len(opcoes)
    )


@router.post("/{list_id}/refresh", response_model=LookupListResponse, status_code=status.HTTP_200_OK)
async def refresh_lookup_list(
    list_id: str,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Atualizar lista via API externa configurada
    Requer: admin
    """
    lista = session.get(LookupList, list_id)

    if not lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lista '{list_id}' não encontrada"
        )

    if not lista.config_api:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lista '{list_id}' não possui configuração de API"
        )

    try:
        config = lista.config_api
        url = config.get('url')
        method = config.get('method', 'GET').upper()
        headers = config.get('headers', {})
        mapping = config.get('mapping', {})

        log_info(f"[LOOKUP_LIST] Atualizando lista '{list_id}' via API: {url}")

        # Fazer requisição HTTP
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == 'GET':
                response = await client.get(url, headers=headers)
            elif method == 'POST':
                response = await client.post(url, headers=headers)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Método HTTP '{method}' não suportado"
                )

            response.raise_for_status()
            data = response.json()

        # Mapear resposta para formato de opções
        if not isinstance(data, list):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API retornou dados em formato inválido (esperado: array)"
            )

        novas_opcoes = []
        for item in data:
            try:
                opcao = {}
                # Mapear campos usando notação de ponto para acesso aninhado
                for field, path in mapping.items():
                    value = item
                    for key in path.split('.'):
                        value = value.get(key) if isinstance(value, dict) else None
                        if value is None:
                            break
                    if value is not None:
                        opcao[field] = str(value) if field in ['id', 'label'] else value

                # Validar que temos id e label
                if 'id' in opcao and 'label' in opcao:
                    novas_opcoes.append(opcao)
            except Exception as e:
                log_warning(f"[LOOKUP_LIST] Erro ao mapear item: {e}")
                continue

        if not novas_opcoes:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Nenhuma opção válida foi mapeada da resposta da API"
            )

        # Atualizar lista
        lista.opcoes = novas_opcoes
        lista.ultima_atualizacao = datetime.utcnow()
        lista.atualizado_em = datetime.utcnow()

        session.add(lista)
        session.commit()
        session.refresh(lista)

        log_info(f"[LOOKUP_LIST] Lista '{list_id}' atualizada com {len(novas_opcoes)} opções")

        return lista

    except httpx.HTTPError as e:
        log_error(f"[LOOKUP_LIST] Erro ao chamar API: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao chamar API externa: {str(e)}"
        )
    except Exception as e:
        log_error(f"[LOOKUP_LIST] Erro ao atualizar lista: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar atualização: {str(e)}"
        )


@router.post("/{list_id}/update", response_model=LookupListResponse, status_code=status.HTTP_200_OK)
async def webhook_update_lookup_list(
    list_id: str,
    update_data: LookupListUpdateOptions,
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
):
    """
    Webhook para atualização proativa de lista (sistemas externos)
    Requer: Bearer token no header Authorization

    Usado para integração com sistemas externos que enviam dados atualizados
    """
    # TODO: Implementar validação de token/API key
    # Por enquanto, qualquer requisição com Authorization é aceita
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido ou ausente"
        )

    lista = session.get(LookupList, list_id)

    if not lista:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lista '{list_id}' não encontrada"
        )

    # Atualizar opções
    lista.opcoes = update_data.opcoes
    lista.ultima_atualizacao = datetime.utcnow()
    lista.atualizado_em = datetime.utcnow()

    session.add(lista)
    session.commit()
    session.refresh(lista)

    log_info(f"[LOOKUP_LIST] Lista '{list_id}' atualizada via webhook com {len(update_data.opcoes)} opções")

    return lista

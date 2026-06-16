"""
API Endpoints para Lookup (Views e Listas)
"""

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, select, text
from typing import List, Optional
import json

from ...core.database import _ensure_engine
from ...models.configuracao import Configuracao

api_router = APIRouter()


@api_router.get("/lookup/views", tags=["Lookup"])
async def list_lookup_views():
    """
    Lista views homologadas para uso em campos Lookup

    Busca da tabela configuracoes (chave = 'lookup_views')

    Returns:
        List[dict]: Lista de views disponíveis
        [
            {"value": "vw_tab_clientes_lookup", "label": "Clientes (NR13)"},
            ...
        ]
    """
    try:
        db_engine = _ensure_engine()
        with Session(db_engine) as session:
            # Buscar configuração de lookup_views
            statement = select(Configuracao).where(Configuracao.chave == "lookup_views")
            config = session.exec(statement).first()

            if not config:
                raise HTTPException(
                    status_code=404,
                    detail="Configuração 'lookup_views' não encontrada"
                )

            # Parse JSON
            try:
                config_data = json.loads(config.valor)
                views_list = config_data.get("views", [])
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=500,
                    detail="Erro ao parsear configuração de views"
                )

            # Se views_list já contém objetos com value/label/description, retornar direto
            if views_list and isinstance(views_list[0], dict):
                return views_list

            # Caso contrário (backward compatibility), gerar labels automaticamente
            result = []
            for view_name in views_list:
                label = view_name.replace("vw_", "").replace("_lookup", "").replace("_", " ").title()
                result.append({
                    "value": view_name,
                    "label": label,
                    "description": f"View de lookup: {label}"
                })

            return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar views: {str(e)}")


@api_router.get("/lookup/views/{view_name}/data", tags=["Lookup"])
async def get_lookup_view_data(
    view_name: str,
    id: Optional[str] = Query(None, description="Buscar registro específico por id (restaurar valor salvo)"),
    search: Optional[str] = Query(None, description="Busca no campo 'label'"),
    filter: Optional[str] = Query(None, description="Filtro no campo 'filter' (filtro dependente)"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=1000, description="Itens por página")
):
    """
    Busca dados de uma view de lookup com filtros

    Args:
        view_name: Nome da view (ex: vw_tab_clientes_lookup)
        id: ID do registro para restaurar label de valor já salvo
        search: Termo de busca no campo 'label'
        filter: Valor para filtrar no campo 'filter' (filtro dependente)
        page: Página atual
        page_size: Itens por página

    Returns:
        dict: {
            "items": [{"id": ..., "label": ..., "filter": ...}],
            "total": int,
            "page": int,
            "page_size": int,
            "total_pages": int
        }
    """
    try:
        # Validar se view está homologada
        db_engine = _ensure_engine()
        with Session(db_engine) as session:
            statement = select(Configuracao).where(Configuracao.chave == "lookup_views")
            config = session.exec(statement).first()

            if not config:
                raise HTTPException(
                    status_code=404,
                    detail="Configuração de views não encontrada"
                )

            config_data = json.loads(config.valor)
            views_list = config_data.get("views", [])

            # Extrair apenas os valores (view names) para validação
            if views_list and isinstance(views_list[0], dict):
                allowed_views = [v["value"] for v in views_list]
            else:
                allowed_views = views_list

            if view_name not in allowed_views:
                raise HTTPException(
                    status_code=403,
                    detail=f"View '{view_name}' não está homologada para uso"
                )

            # Construir query base
            base_query = f"SELECT id, label, filter FROM {view_name} WHERE 1=1"
            count_query = f"SELECT COUNT(*) as total FROM {view_name} WHERE 1=1"
            params = {}

            # Busca por id específico (restaurar valor salvo no formulário)
            if id is not None and str(id).strip() != "":
                base_query += " AND id = :id"
                count_query += " AND id = :id"
                params["id"] = id

            # Filtro de busca no label
            if search:
                base_query += " AND label LIKE :search"
                count_query += " AND label LIKE :search"
                params["search"] = f"%{search}%"

            # Filtro dependente (filter field)
            if filter:
                base_query += " AND filter = :filter"
                count_query += " AND filter = :filter"
                params["filter"] = filter

            # Paginação
            offset = (page - 1) * page_size
            base_query += f" LIMIT :limit OFFSET :offset"
            params["limit"] = page_size
            params["offset"] = offset

            # Executar query de dados
            result = session.execute(text(base_query), params).fetchall()

            items = [
                {
                    "id": row[0],
                    "label": row[1],
                    "filter": row[2]
                }
                for row in result
            ]

            # Executar query de contagem
            # Remover LIMIT/OFFSET dos params para count
            count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
            total_row = session.execute(text(count_query), count_params).first()
            total = total_row[0] if total_row else 0

            total_pages = (total + page_size - 1) // page_size

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados da view: {str(e)}")

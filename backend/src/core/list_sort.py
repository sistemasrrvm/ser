"""
Helper para ordenação segura em listagens paginadas.
"""

from typing import Literal, Optional, Type

from fastapi import HTTPException, status
from sqlalchemy import asc, desc
from sqlmodel import SQLModel

SortDir = Literal["asc", "desc"]


def apply_list_sort(
    statement,
    model: Type[SQLModel],
    sort_by: Optional[str],
    sort_dir: SortDir,
    allowed: dict[str, str],
    default_column: str,
):
    """
    Aplica ORDER BY com whitelist de colunas.

    allowed: mapa {nome_api: nome_atributo_no_modelo}
    """
    column_key = sort_by if sort_by else default_column

    if column_key not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": f"sort_by inválido: '{sort_by}'",
                "allowed": list(allowed.keys()),
            },
        )

    attr_name = allowed[column_key]
    column = getattr(model, attr_name)

    if sort_dir == "desc":
        return statement.order_by(desc(column))
    return statement.order_by(asc(column))

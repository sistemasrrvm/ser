"""
Helper para listagens paginadas com ordenação.
"""

import math
from typing import Literal, Optional, Type

from sqlmodel import Session, SQLModel, func, select

from .list_sort import SortDir, apply_list_sort


def paginate_sorted(
    session: Session,
    statement,
    model: Type[SQLModel],
    page: int,
    page_size: int,
    sort_by: Optional[str],
    sort_dir: SortDir,
    allowed_sort: dict[str, str],
    default_sort: str,
):
    """Conta, ordena e pagina (order_by antes de offset/limit)."""
    count_statement = select(func.count()).select_from(statement.subquery())
    total = session.exec(count_statement).one()

    statement = apply_list_sort(
        statement,
        model,
        sort_by,
        sort_dir,
        allowed_sort,
        default_sort,
    )

    offset = (page - 1) * page_size
    statement = statement.offset(offset).limit(page_size)
    results = session.exec(statement).all()

    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return results, total, total_pages

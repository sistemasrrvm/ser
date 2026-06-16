"""
Model: Histórico de solicitações de correção (#246)
"""

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text, BigInteger, ForeignKey
from datetime import datetime
from typing import Optional


class ReportCorrecao(SQLModel, table=True):
    __tablename__ = "relatorios_correcoes"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    report_id: int = Field(sa_column=Column(BigInteger(), ForeignKey("reports.id"), index=True))
    solicitado_por_id: int = Field(sa_column=Column(BigInteger(), ForeignKey("users.id")))
    descricao: str = Field(sa_column=Column(Text))
    status_anterior: str = Field(max_length=20)
    status_novo: str = Field(max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)

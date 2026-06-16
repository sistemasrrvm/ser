"""
Model: Report (Relatório)
Representa relatórios de inspeção preenchidos pelos técnicos
"""

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Date, BigInteger, ForeignKey
from datetime import datetime, date
from typing import Optional, Dict, Any


class Report(SQLModel, table=True):
    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger(), primary_key=True))
    numero: str = Field(max_length=50, unique=True, index=True)
    form_template_id: int = Field(sa_column=Column(BigInteger(), ForeignKey("formularios.id")))
    cliente_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger()), description="FK para tab_clientes.CLI_ID")
    equipamento_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger()), description="FK para tab_equipamentos.EQP_ID")
    tipo_inspecao: Optional[str] = Field(default=None, max_length=100)
    tecnico_id: int = Field(sa_column=Column(BigInteger(), ForeignKey("users.id")))
    status: str = Field(default="rascunho", max_length=20)
    respostas: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    observacoes: Optional[str] = Field(default=None)
    data_inspecao: Optional[date] = Field(default=None, sa_column=Column(Date))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

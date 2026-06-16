"""
Model: FormField
Campos de formulários
"""

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON, BigInteger, ForeignKey
from typing import Optional, TYPE_CHECKING, Dict, Any
from datetime import datetime

if TYPE_CHECKING:
    from .form_page import FormPage


class FormField(SQLModel, table=True):
    """
    FormField (Campo de Formulário)
    Um campo pertence a uma página e tem configurações específicas
    """
    __tablename__ = "formularios_campos"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger(), primary_key=True))
    pagina_id: int = Field(sa_column=Column(BigInteger(), ForeignKey("formularios_paginas.id"), index=True))
    rotulo: str = Field(max_length=100, index=True)
    ordem: int = Field(ge=1, index=True)
    tipo: str = Field(max_length=20, index=True)  # textbox, date, number, yes_no, choice, lookup, separator
    configuracao: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # JSONB com configurações específicas
    regra_exibicao_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    pagina: "FormPage" = Relationship(back_populates="campos")

    class Config:
        json_schema_extra = {
            "example": {
                "pagina_id": 1,
                "rotulo": "Nome Completo",
                "ordem": 1,
                "tipo": "textbox",
                "configuracao": {
                    "format_validation": "none",
                    "min_characters": 3,
                    "max_characters": 100,
                    "require": True,
                    "read_only": False,
                    "unique": False
                },
                "regra_exibicao_id": None
            }
        }

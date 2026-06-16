"""
Model: FormPage
Páginas de formulários
"""

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON, BigInteger, ForeignKey
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime

if TYPE_CHECKING:
    from .formulario import Formulario
    from .form_field import FormField


class FormPage(SQLModel, table=True):
    """
    FormPage (Página de Formulário)
    Uma página contém múltiplos campos e pertence a um formulário
    """
    __tablename__ = "formularios_paginas"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger(), primary_key=True))
    formulario_id: int = Field(sa_column=Column(BigInteger(), ForeignKey("formularios.id"), index=True))
    nome: str = Field(max_length=100, index=True)
    ordem: int = Field(ge=1, index=True)
    regra_exibicao_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    formulario: "Formulario" = Relationship(back_populates="paginas")
    campos: List["FormField"] = Relationship(
        back_populates="pagina",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "formulario_id": 1,
                "nome": "Dados Básicos",
                "ordem": 1,
                "regra_exibicao_id": None
            }
        }

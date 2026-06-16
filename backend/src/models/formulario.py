"""
Model: Formulario
Cadastro de formulários (templates)
"""

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy import BigInteger, ForeignKey
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime
from ..core.timezone import now_brazil

if TYPE_CHECKING:
    from .user import User
    from .form_page import FormPage


class Formulario(SQLModel, table=True):
    """
    Formulario (Template de Formulário)
    """
    __tablename__ = "formularios"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger(), primary_key=True, autoincrement=True))
    nome: str = Field(max_length=100, index=True)
    descricao: Optional[str] = Field(default=None, max_length=500)
    excel_template: Optional[str] = Field(default=None, sa_column=Column(MEDIUMTEXT), description="Template Excel em base64 para mesclagem (MEDIUMTEXT 16MB)")
    criado_em: datetime = Field(default_factory=now_brazil)
    criado_por: int = Field(sa_column=Column(BigInteger(), ForeignKey("users.id"), index=True))
    atualizado_em: datetime = Field(default_factory=now_brazil)
    atualizado_por: Optional[int] = Field(default=None, sa_column=Column(BigInteger(), ForeignKey("users.id"), index=True))

    # Relationships
    criador: "User" = Relationship(
        back_populates="formularios_criados",
        sa_relationship_kwargs={"foreign_keys": "[Formulario.criado_por]"}
    )
    paginas: List["FormPage"] = Relationship(
        back_populates="formulario",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Cadastro de Cliente",
                "descricao": "Formulário para cadastro de novos clientes",
                "criado_por": 1
            }
        }

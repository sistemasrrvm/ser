"""
Model: User
Usuários do sistema
"""

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import BigInteger
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .role import Role
    from .formulario import Formulario


class User(SQLModel, table=True):
    """
    User (Usuário do Sistema)
    """
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger(), primary_key=True, autoincrement=True))
    username: str = Field(max_length=50, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    full_name: str = Field(max_length=100)
    email: Optional[str] = Field(default=None, max_length=100, unique=True, index=True)
    role_id: int = Field(foreign_key="roles.id", index=True)
    is_active: bool = Field(default=True, index=True)
    last_login: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    role: "Role" = Relationship(back_populates="users")
    formularios_criados: list["Formulario"] = Relationship(
        back_populates="criador",
        sa_relationship_kwargs={"foreign_keys": "Formulario.criado_por"}
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "full_name": "Administrador do Sistema",
                "email": "admin@ser.local",
                "role_id": 1,
                "is_active": True
            }
        }

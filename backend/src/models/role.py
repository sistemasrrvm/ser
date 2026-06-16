"""
Model: Role
Perfis de acesso do sistema
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import User


class Role(SQLModel, table=True):
    """
    Role (Perfil de Acesso)

    Níveis:
    - 100: admin (administrador do sistema - acesso total)
    - 40: revisor (pode revisar e aprovar relatórios)
    - 20: usuario (pode criar e editar relatórios)
    """
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    level: int = Field(index=True, description="Nível hierárquico do role")
    description: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    users: List["User"] = Relationship(back_populates="role")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "admin",
                "level": 100,
                "description": "Administrador do sistema - acesso total"
            }
        }

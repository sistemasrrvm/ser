"""
Schemas para usuários
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Union
from datetime import datetime


class RoleResponse(BaseModel):
    """Response com dados do role"""
    id: int
    name: str
    level: int
    description: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "admin",
                "level": 100,
                "description": "Administrador do sistema - acesso total"
            }
        }


class RoleListResponse(BaseModel):
    """Response com lista de roles"""
    total: int
    roles: list[RoleResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 3,
                "roles": [
                    {
                        "id": 1,
                        "name": "Administrador",
                        "level": 100,
                        "description": "Acesso total ao sistema"
                    }
                ]
            }
        }


class UserResponse(BaseModel):
    """Response com dados do usuário (sem senha)"""
    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    role: RoleResponse
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "admin",
                "full_name": "Administrador do Sistema",
                "email": "admin@ser.local",
                "role": {
                    "id": 1,
                    "name": "admin",
                    "level": 100
                },
                "is_active": True,
                "last_login": "2025-10-29T20:50:10",
                "created_at": "2025-10-29T20:00:00"
            }
        }


class UserCreate(BaseModel):
    """Request para criar usuário"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr = Field(..., description="Email do usuário (obrigatório)")
    role_id: int
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "username": "joao.silva",
                "password": "Senha@123",
                "full_name": "João Silva",
                "email": "joao@example.com",
                "role_id": 2,
                "is_active": True
            }
        }


class UserUpdate(BaseModel):
    """Request para atualizar usuário"""
    full_name: Optional[str] = Field(None, min_length=3, max_length=100)
    email: EmailStr = Field(..., description="Email do usuário (obrigatório)")
    password: Optional[str] = Field(None, min_length=8, description="Nova senha (opcional, apenas para redefinir)")
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "João Silva Santos",
                "email": "joao.santos@example.com",
                "is_active": True
            }
        }


class UserListResponse(BaseModel):
    """Response com lista de usuários"""
    total: int
    users: list[UserResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "users": [
                    {
                        "id": 1,
                        "username": "admin",
                        "full_name": "Administrador do Sistema",
                        "email": "admin@ser.local",
                        "role": {
                            "id": 1,
                            "name": "admin",
                            "level": 100
                        },
                        "is_active": True
                    }
                ]
            }
        }

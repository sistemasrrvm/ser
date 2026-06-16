"""
Schemas para autenticação
"""

from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Request para login"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    remember_me: bool = Field(default=False, description="Manter conectado (refresh token de longa duração)")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "Admin@123",
                "remember_me": False
            }
        }


class TokenResponse(BaseModel):
    """Response com tokens de acesso"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "full_name": "Administrador do Sistema",
                    "email": "admin@ser.local",
                    "role": {
                        "id": 1,
                        "name": "admin",
                        "level": 100
                    }
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request para renovar access token"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Request para solicitar recuperação de senha"""
    username: str = Field(..., min_length=3, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin"
            }
        }


class PasswordResetResponse(BaseModel):
    """Response com token de recuperação de senha"""
    message: str
    reset_token: str
    expires_in_hours: int = 1

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Token de recuperação gerado com sucesso",
                "reset_token": "abc123def456...",
                "expires_in_hours": 1
            }
        }


class PasswordResetConfirm(BaseModel):
    """Request para confirmar nova senha"""
    token: str
    new_password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456...",
                "new_password": "NewPass@123"
            }
        }


class PasswordChangeRequest(BaseModel):
    """Request para trocar senha (usuário autenticado)"""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPass@123",
                "new_password": "NewPass@123"
            }
        }


# Import necessário para evitar circular import
from .user import UserResponse
TokenResponse.model_rebuild()

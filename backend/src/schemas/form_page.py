"""
Schemas para páginas de formulários
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FormPageCreate(BaseModel):
    """Request para criar página"""
    nome: str = Field(..., min_length=1, max_length=100)
    ordem: int = Field(..., ge=1)
    regra_exibicao_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Dados Básicos",
                "ordem": 1,
                "regra_exibicao_id": None
            }
        }


class FormPageUpdate(BaseModel):
    """Request para atualizar página"""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    ordem: Optional[int] = Field(None, ge=1)
    regra_exibicao_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Dados Pessoais",
                "ordem": 2
            }
        }


class FormPageResponse(BaseModel):
    """Response com dados da página"""
    id: int
    formulario_id: int
    nome: str
    ordem: int
    regra_exibicao_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "formulario_id": 1,
                "nome": "Dados Básicos",
                "ordem": 1,
                "regra_exibicao_id": None,
                "created_at": "2025-11-12T01:00:00",
                "updated_at": "2025-11-12T01:00:00"
            }
        }


class FormPageListResponse(BaseModel):
    """Response com lista de páginas"""
    total: int
    paginas: list[FormPageResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "paginas": [
                    {
                        "id": 1,
                        "formulario_id": 1,
                        "nome": "Dados Básicos",
                        "ordem": 1,
                        "regra_exibicao_id": None,
                        "created_at": "2025-11-12T01:00:00",
                        "updated_at": "2025-11-12T01:00:00"
                    },
                    {
                        "id": 2,
                        "formulario_id": 1,
                        "nome": "Endereço",
                        "ordem": 2,
                        "regra_exibicao_id": None,
                        "created_at": "2025-11-12T01:00:00",
                        "updated_at": "2025-11-12T01:00:00"
                    }
                ]
            }
        }

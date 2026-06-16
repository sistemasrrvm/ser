"""
Schemas para formulários
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FormularioCreate(BaseModel):
    """Request para criar formulário"""
    nome: str = Field(..., min_length=3, max_length=100)
    descricao: Optional[str] = Field(None, max_length=500)

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Cadastro de Cliente",
                "descricao": "Formulário para cadastro de novos clientes"
            }
        }


class FormularioUpdate(BaseModel):
    """Request para atualizar formulário"""
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    descricao: Optional[str] = Field(None, max_length=500)
    excel_template: Optional[str] = Field(None, description="Template Excel em base64")

    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Cadastro de Cliente - Atualizado",
                "descricao": "Formulário atualizado para cadastro de clientes"
            }
        }


class FormularioResponse(BaseModel):
    """Response com dados do formulário"""
    id: int
    nome: str
    descricao: Optional[str] = None
    excel_template: Optional[str] = None
    criado_em: datetime
    criado_por: int
    atualizado_em: datetime
    atualizado_por: Optional[int] = None
    total_paginas: Optional[int] = 0
    total_campos: Optional[int] = 0

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "nome": "Cadastro de Cliente",
                "descricao": "Formulário para cadastro de novos clientes",
                "criado_em": "2025-10-29T20:50:10",
                "criado_por": 1,
                "atualizado_em": "2025-10-29T20:50:10",
                "atualizado_por": 1
            }
        }


class FormularioListResponse(BaseModel):
    """Response com lista de formulários"""
    total: int
    formularios: list[FormularioResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "formularios": [
                    {
                        "id": 1,
                        "nome": "Cadastro de Cliente",
                        "descricao": "Formulário para cadastro de novos clientes",
                        "criado_em": "2025-10-29T20:50:10",
                        "criado_por": 1
                    },
                    {
                        "id": 2,
                        "nome": "Cadastro de Fornecedor",
                        "descricao": "Formulário para cadastro de fornecedores",
                        "criado_em": "2025-10-29T21:00:00",
                        "criado_por": 1
                    }
                ]
            }
        }

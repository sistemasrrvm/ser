"""
Schemas para campos de formulários
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime


class FormFieldCreate(BaseModel):
    """Request para criar campo"""
    rotulo: str = Field(..., min_length=1, max_length=100)
    ordem: int = Field(..., ge=1)
    tipo: str = Field(..., pattern="^(textbox|date|number|yes_no|choice|lookup|separator)$")
    configuracao: Dict[str, Any] = Field(default_factory=dict)
    regra_exibicao_id: Optional[int] = None

    @field_validator('tipo')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validar tipo de campo"""
        valid_types = ['textbox', 'date', 'number', 'yes_no', 'choice', 'lookup', 'separator']
        if v not in valid_types:
            raise ValueError(f'Tipo deve ser um de: {", ".join(valid_types)}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
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


class FormFieldUpdate(BaseModel):
    """Request para atualizar campo"""
    rotulo: Optional[str] = Field(None, min_length=1, max_length=100)
    ordem: Optional[int] = Field(None, ge=1)
    tipo: Optional[str] = Field(None, pattern="^(textbox|date|number|yes_no|choice|lookup|separator)$")
    configuracao: Optional[Dict[str, Any]] = None
    regra_exibicao_id: Optional[int] = None

    @field_validator('tipo')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validar tipo de campo"""
        if v is not None:
            valid_types = ['textbox', 'date', 'number', 'yes_no', 'choice', 'lookup', 'separator']
            if v not in valid_types:
                raise ValueError(f'Tipo deve ser um de: {", ".join(valid_types)}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "rotulo": "Nome do Cliente",
                "ordem": 2,
                "configuracao": {
                    "max_characters": 150
                }
            }
        }


class FormFieldResponse(BaseModel):
    """Response com dados do campo"""
    id: int
    pagina_id: int
    rotulo: str
    ordem: int
    tipo: str
    configuracao: Dict[str, Any]
    regra_exibicao_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "pagina_id": 1,
                "rotulo": "Nome Completo",
                "ordem": 1,
                "tipo": "textbox",
                "configuracao": {
                    "format_validation": "none",
                    "min_characters": 3,
                    "max_characters": 100,
                    "require": True
                },
                "regra_exibicao_id": None,
                "created_at": "2025-11-12T01:00:00",
                "updated_at": "2025-11-12T01:00:00"
            }
        }


class FormFieldListResponse(BaseModel):
    """Response com lista de campos"""
    total: int
    campos: list[FormFieldResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 3,
                "campos": [
                    {
                        "id": 1,
                        "pagina_id": 1,
                        "rotulo": "Nome Completo",
                        "ordem": 1,
                        "tipo": "textbox",
                        "configuracao": {"format_validation": "none", "max_characters": 100},
                        "regra_exibicao_id": None,
                        "created_at": "2025-11-12T01:00:00",
                        "updated_at": "2025-11-12T01:00:00"
                    },
                    {
                        "id": 2,
                        "pagina_id": 1,
                        "rotulo": "CPF",
                        "ordem": 2,
                        "tipo": "textbox",
                        "configuracao": {"format_validation": "cpf"},
                        "regra_exibicao_id": None,
                        "created_at": "2025-11-12T01:00:00",
                        "updated_at": "2025-11-12T01:00:00"
                    },
                    {
                        "id": 3,
                        "pagina_id": 1,
                        "rotulo": "Data de Nascimento",
                        "ordem": 3,
                        "tipo": "date",
                        "configuracao": {"tipo": "date"},
                        "regra_exibicao_id": None,
                        "created_at": "2025-11-12T01:00:00",
                        "updated_at": "2025-11-12T01:00:00"
                    }
                ]
            }
        }

"""
Schemas para Configuracao
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re


class ConfiguracaoCreate(BaseModel):
    """Schema para criar configuração"""
    chave: str = Field(..., min_length=1, max_length=100)
    valor: Optional[str] = None
    tipo: str = Field(default="texto", pattern="^(texto|numero|json|boolean)$")
    descricao: Optional[str] = Field(None, max_length=255)
    categoria: str = Field(default="geral", max_length=100)

    @validator('chave')
    def validate_chave(cls, v):
        """Validar formato da chave: apenas letras, números, underscore e hífen"""
        if not re.match(r'^[a-z0-9_-]+$', v):
            raise ValueError('Chave deve conter apenas letras minúsculas, números, underscore (_) e hífen (-)')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "chave": "smtp_host",
                "valor": "smtp.gmail.com",
                "tipo": "texto",
                "descricao": "Servidor SMTP para envio de emails",
                "categoria": "email"
            }
        }


class ConfiguracaoUpdate(BaseModel):
    """Schema para atualizar configuração (campos opcionais)"""
    valor: Optional[str] = None
    tipo: Optional[str] = Field(None, pattern="^(texto|numero|json|boolean)$")
    descricao: Optional[str] = Field(None, max_length=255)
    categoria: Optional[str] = Field(None, max_length=100)


class ConfiguracaoResponse(BaseModel):
    """Schema de resposta de configuração"""
    id: int
    chave: str
    valor: Optional[str]
    tipo: str
    descricao: Optional[str]
    categoria: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConfiguracaoListResponse(BaseModel):
    """Schema de resposta para listagem"""
    total: int
    configuracoes: List[ConfiguracaoResponse]

"""
Schemas para LookupList
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class LookupListOptionSchema(BaseModel):
    """Schema para uma opção da lista"""
    id: str
    label: str
    filter: Optional[str] = None


class LookupListAPIConfigSchema(BaseModel):
    """Schema para configuração de API externa"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    mapping: Dict[str, str]  # {id: 'field_name', label: 'field_name', filter: 'field_name'}
    cache_ttl: Optional[int] = None


class LookupListCreate(BaseModel):
    """Schema para criar lista"""
    id: str = Field(..., min_length=1, max_length=50)
    nome: str = Field(..., min_length=1, max_length=100)
    descricao: Optional[str] = None
    opcoes: List[Dict[str, Any]] = Field(...)
    config_api: Optional[Dict[str, Any]] = None

    @validator('id')
    def validate_id(cls, v):
        """Validar formato do ID: apenas letras minúsculas, números, underscore e hífen"""
        if not re.match(r'^[a-z0-9_-]+$', v):
            raise ValueError('ID deve conter apenas letras minúsculas, números, underscore (_) e hífen (-)')
        return v

    @validator('opcoes')
    def validate_opcoes(cls, v):
        """Validar estrutura das opções"""
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError('opcoes deve ser um array não vazio')

        for idx, option in enumerate(v):
            if not isinstance(option, dict):
                raise ValueError(f'opcoes[{idx}] deve ser um objeto')
            if 'id' not in option or 'label' not in option:
                raise ValueError(f'opcoes[{idx}] deve ter campos "id" e "label"')
            if not isinstance(option['id'], (str, int)):
                raise ValueError(f'opcoes[{idx}].id deve ser string ou número')
            if not isinstance(option['label'], str):
                raise ValueError(f'opcoes[{idx}].label deve ser string')

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "status_servico",
                "nome": "Status de Serviço",
                "descricao": "Status possíveis para um serviço",
                "opcoes": [
                    {"id": "pendente", "label": "Pendente"},
                    {"id": "em_andamento", "label": "Em Andamento"},
                    {"id": "concluido", "label": "Concluído"}
                ],
                "config_api": None
            }
        }


class LookupListUpdate(BaseModel):
    """Schema para atualizar lista (campos opcionais)"""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    opcoes: Optional[List[Dict[str, Any]]] = None
    config_api: Optional[Dict[str, Any]] = None

    @validator('opcoes')
    def validate_opcoes(cls, v):
        """Validar estrutura das opções se fornecido"""
        if v is None:
            return v

        if not isinstance(v, list) or len(v) == 0:
            raise ValueError('opcoes deve ser um array não vazio')

        for idx, option in enumerate(v):
            if not isinstance(option, dict):
                raise ValueError(f'opcoes[{idx}] deve ser um objeto')
            if 'id' not in option or 'label' not in option:
                raise ValueError(f'opcoes[{idx}] deve ter campos "id" e "label"')

        return v


class LookupListUpdateOptions(BaseModel):
    """Schema para atualizar apenas as opções (endpoint /update webhook)"""
    opcoes: List[Dict[str, Any]]

    @validator('opcoes')
    def validate_opcoes(cls, v):
        """Validar estrutura das opções"""
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError('opcoes deve ser um array não vazio')

        for idx, option in enumerate(v):
            if not isinstance(option, dict):
                raise ValueError(f'opcoes[{idx}] deve ser um objeto')
            if 'id' not in option or 'label' not in option:
                raise ValueError(f'opcoes[{idx}] deve ter campos "id" e "label"')

        return v


class LookupListResponse(BaseModel):
    """Schema de resposta de lista"""
    id: str
    nome: str
    descricao: Optional[str]
    opcoes: List[Dict[str, Any]]
    config_api: Optional[Dict[str, Any]]
    ultima_atualizacao: Optional[datetime]
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


class LookupListListResponse(BaseModel):
    """Schema de resposta para listagem"""
    total: int
    listas: List[LookupListResponse]


class LookupListOptionsResponse(BaseModel):
    """Schema de resposta para opções filtradas"""
    list_id: str
    opcoes: List[Dict[str, Any]]
    total: int

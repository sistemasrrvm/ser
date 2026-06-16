"""
Model: LookupList
Listas de opções para campos tipo Lookup
"""

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, Text
from typing import Optional, Dict, Any, List
from datetime import datetime


class LookupListOption(SQLModel):
    """Estrutura de uma opção na lista"""
    id: str
    label: str
    filter: Optional[str] = None


class LookupListAPIConfig(SQLModel):
    """Configuração para atualização via API externa"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    mapping: Dict[str, str]  # Como mapear resposta para {id, label, filter}
    cache_ttl: Optional[int] = None  # Tempo de cache em segundos


class LookupList(SQLModel, table=True):
    """
    LookupList (Lista de Opções para Lookup)
    Tabela para gerenciar listas reutilizáveis de opções
    """
    __tablename__ = "listas"

    id: str = Field(primary_key=True, max_length=50)
    nome: str = Field(max_length=100, unique=True, index=True)
    descricao: Optional[str] = Field(default=None, sa_column=Column(Text))
    opcoes: List[Dict[str, Any]] = Field(sa_column=Column(JSON))  # Array de {id, label, filter}
    config_api: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    ultima_atualizacao: Optional[datetime] = None
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "uf",
                "nome": "Estados do Brasil",
                "descricao": "Lista de Unidades Federativas do Brasil",
                "opcoes": [
                    {"id": "sp", "label": "São Paulo", "filter": "sudeste"},
                    {"id": "rj", "label": "Rio de Janeiro", "filter": "sudeste"}
                ],
                "config_api": {
                    "url": "https://servicodados.ibge.gov.br/api/v1/localidades/estados",
                    "method": "GET",
                    "headers": {},
                    "mapping": {
                        "id": "sigla",
                        "label": "nome",
                        "filter": "regiao.nome"
                    },
                    "cache_ttl": 86400
                },
                "ultima_atualizacao": None
            }
        }

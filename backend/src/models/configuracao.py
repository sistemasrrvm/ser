"""
Model: Configuracao
Armazena configurações do sistema
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Configuracao(SQLModel, table=True):
    """
    Tabela de configurações do sistema

    Usada para armazenar:
    - Views homologadas para Lookup (chave: lookup_views)
    - Outras configurações gerais do sistema
    """
    __tablename__ = "configuracoes"

    id: int = Field(primary_key=True)
    chave: str = Field(max_length=100, unique=True, index=True, description="Chave única da configuração")
    valor: Optional[str] = Field(default=None, description="Valor da configuração (pode ser texto, número ou JSON)")
    tipo: str = Field(default="texto", max_length=20, description="Tipo: texto, numero, json, boolean")
    descricao: Optional[str] = Field(default=None, max_length=255, description="Descrição da configuração")
    categoria: str = Field(default="geral", max_length=100, index=True, description="Categoria para agrupar")
    created_at: Optional[datetime] = Field(default=None, description="Data de criação")
    updated_at: Optional[datetime] = Field(default=None, description="Data de atualização")

"""
Model: ManutCliente (Cache SQL Server)
Réplica da tabela MANUT_CLIENTE do SQL Server
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class ManutCliente(SQLModel, table=True):
    """
    ManutCliente - Réplica cache da tabela MANUT_CLIENTE do SQL Server
    Tabela de clientes do sistema NR13
    """
    __tablename__ = "tab_clientes"

    CLI_ID: int = Field(primary_key=True, description="ID do cliente")
    CLI_NOME: Optional[str] = Field(default=None, max_length=200, index=True, description="Nome do cliente")
    CLI_CNPJ: Optional[str] = Field(default=None, max_length=14, description="CNPJ do cliente")
    CLI_SITE: Optional[str] = Field(default=None, max_length=100, description="Site do cliente")
    CLI_CONTATO: Optional[str] = Field(default=None, max_length=100, description="Contato do cliente")
    CLI_EMAIL: Optional[str] = Field(default=None, max_length=100, description="Email do cliente")
    CLI_TELEFONE: Optional[str] = Field(default=None, max_length=50, description="Telefone do cliente")
    CLI_ENDERECO: Optional[str] = Field(default=None, max_length=200, description="Endereço (logradouro)")
    CLI_NUMERO: Optional[str] = Field(default=None, max_length=20, description="Número do endereço")
    CLI_BAIRRO: Optional[str] = Field(default=None, max_length=100, description="Bairro")
    CLI_CEP: Optional[str] = Field(default=None, max_length=10, description="CEP")
    CLI_CIDADE: Optional[str] = Field(default=None, max_length=100, description="Cidade")
    CLI_ESTADO: Optional[str] = Field(default=None, max_length=2, description="Estado (UF)")
    CLI_DT_INS: Optional[datetime] = Field(default=None, description="Data de inserção")
    CLI_DT_UPD: Optional[datetime] = Field(default=None, description="Data de atualização")

    class Config:
        json_schema_extra = {
            "example": {
                "CLI_ID": 1,
                "CLI_NOME": "Cliente Exemplo Ltda",
                "CLI_CNPJ": "12345678000190",
                "CLI_SITE": "www.exemplo.com.br",
                "CLI_CONTATO": "João Silva",
                "CLI_EMAIL": "contato@exemplo.com.br",
                "CLI_TELEFONE": "11999999999",
                "CLI_ENDERECO": "Rua das Flores",
                "CLI_NUMERO": "123",
                "CLI_BAIRRO": "Centro",
                "CLI_CEP": "01234-567",
                "CLI_CIDADE": "São Paulo",
                "CLI_ESTADO": "SP",
                "CLI_DT_INS": "2024-01-01T10:00:00",
                "CLI_DT_UPD": "2024-01-15T14:30:00"
            }
        }

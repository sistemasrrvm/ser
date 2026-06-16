"""
Model: ManutTipoEquipamento (Cache SQL Server)
Réplica da tabela MANUT_TIPO_EQUIPAMENTO do SQL Server
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class ManutTipoEquipamento(SQLModel, table=True):
    """
    ManutTipoEquipamento - Réplica cache da tabela MANUT_TIPO_EQUIPAMENTO do SQL Server
    Tipos de equipamentos do sistema NR13
    """
    __tablename__ = "tab_tipos_equipamento"

    TEQP_ID: int = Field(primary_key=True, description="ID do tipo de equipamento")
    TEQP_NOME: Optional[str] = Field(default=None, max_length=100, index=True, description="Nome do tipo")
    TEQP_VENC_CALIBRACAO: Optional[int] = Field(default=None, description="Vencimento calibração (dias)")
    TEQP_REQUER_INSPECAO_EXTERNA: int = Field(default=0, description="Requer inspeção externa (0/1)")
    TEQP_REQUER_INSPECAO_INTERNA: int = Field(default=0, description="Requer inspeção interna (0/1)")
    TEQP_DT_INS: Optional[datetime] = Field(default=None, description="Data de inserção")
    TEQP_DT_UPD: Optional[datetime] = Field(default=None, description="Data de atualização")

    class Config:
        json_schema_extra = {
            "example": {
                "TEQP_ID": 1,
                "TEQP_NOME": "Caldeira",
                "TEQP_VENC_CALIBRACAO": 365,
                "TEQP_REQUER_INSPECAO_EXTERNA": 1,
                "TEQP_REQUER_INSPECAO_INTERNA": 1,
                "TEQP_DT_INS": "2024-01-01T10:00:00",
                "TEQP_DT_UPD": "2024-01-15T14:30:00"
            }
        }

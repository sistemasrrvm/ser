"""
Model: ManutEquipamento (Cache SQL Server)
Réplica da tabela MANUT_EQUIPAMENTO do SQL Server
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class ManutEquipamento(SQLModel, table=True):
    """
    ManutEquipamento - Réplica cache da tabela MANUT_EQUIPAMENTO do SQL Server
    Equipamentos do sistema NR13
    """
    __tablename__ = "tab_equipamentos"

    EQP_ID: int = Field(primary_key=True, description="ID do equipamento")
    EQP_CLI_ID: int = Field(index=True, description="FK para tab_clientes")
    EQP_TEQP_ID: Optional[int] = Field(default=None, index=True, description="FK para tab_tipos_equipamento")
    EQP_TAG: str = Field(max_length=200, index=True, description="Tag do equipamento")
    EQP_NUMERO_SERIE: Optional[str] = Field(default=None, max_length=50, description="Número de série")
    EQP_NOME: Optional[str] = Field(default=None, max_length=200, description="Nome do equipamento")
    EQP_AREA: Optional[str] = Field(default=None, max_length=200, description="Área do equipamento")
    EQP_QTD_EQPI: Optional[int] = Field(default=None, description="Quantidade de EPI")
    EQP_QTD_EQPI_VENCIDO: Optional[int] = Field(default=None, description="Quantidade de EPI vencido")
    EQP_QTD_INST: Optional[int] = Field(default=None, description="Quantidade de instrumentos")
    EQP_QTD_INSC: Optional[int] = Field(default=None, description="Quantidade de inspeções")
    EQP_QTD_INSC_CLASS_0: Optional[int] = Field(default=None, description="Inspeções classe 0")
    EQP_QTD_INSC_CLASS_1: Optional[int] = Field(default=None, description="Inspeções classe 1")
    EQP_QTD_INSC_CLASS_2: Optional[int] = Field(default=None, description="Inspeções classe 2")
    EQP_QTD_INSC_CLASS_3: Optional[int] = Field(default=None, description="Inspeções classe 3")
    EQP_QTD_INSC_CLASS_9: Optional[int] = Field(default=None, description="Inspeções classe 9")
    EQP_DT_INS: Optional[datetime] = Field(default=None, description="Data de inserção")
    EQP_DT_UPD: Optional[datetime] = Field(default=None, description="Data de atualização")

    class Config:
        json_schema_extra = {
            "example": {
                "EQP_ID": 1,
                "EQP_CLI_ID": 1,
                "EQP_TEQP_ID": 1,
                "EQP_TAG": "CAL-001",
                "EQP_NUMERO_SERIE": "CAL-2024-001",
                "EQP_NOME": "Caldeira Principal",
                "EQP_AREA": "Sala de Máquinas - Bloco A",
                "EQP_QTD_EQPI": 10,
                "EQP_QTD_EQPI_VENCIDO": 2,
                "EQP_QTD_INST": 5,
                "EQP_QTD_INSC": 15,
                "EQP_QTD_INSC_CLASS_0": 3,
                "EQP_QTD_INSC_CLASS_1": 5,
                "EQP_QTD_INSC_CLASS_2": 4,
                "EQP_QTD_INSC_CLASS_3": 2,
                "EQP_QTD_INSC_CLASS_9": 1,
                "EQP_DT_INS": "2024-01-01T10:00:00",
                "EQP_DT_UPD": "2024-01-15T14:30:00"
            }
        }

"""
Schemas para dados do sistema NR13 (cache SQL Server)
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# CLIENTES
# ============================================================================

class ManutClienteResponse(BaseModel):
    """Schema de resposta para ManutCliente"""
    CLI_ID: int
    CLI_NOME: Optional[str] = None
    CLI_CNPJ: Optional[str] = None
    CLI_SITE: Optional[str] = None
    CLI_CONTATO: Optional[str] = None
    CLI_EMAIL: Optional[str] = None
    CLI_TELEFONE: Optional[str] = None
    CLI_ENDERECO: Optional[str] = None
    CLI_NUMERO: Optional[str] = None
    CLI_BAIRRO: Optional[str] = None
    CLI_CEP: Optional[str] = None
    CLI_CIDADE: Optional[str] = None
    CLI_ESTADO: Optional[str] = None
    CLI_DT_INS: Optional[datetime] = None
    CLI_DT_UPD: Optional[datetime] = None

    class Config:
        from_attributes = True


class ManutClienteListResponse(BaseModel):
    """Schema de resposta para lista de ManutCliente"""
    items: List[ManutClienteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# TIPOS DE EQUIPAMENTO
# ============================================================================

class ManutTipoEquipamentoResponse(BaseModel):
    """Schema de resposta para ManutTipoEquipamento"""
    TEQP_ID: int
    TEQP_NOME: Optional[str] = None
    TEQP_VENC_CALIBRACAO: Optional[int] = None
    TEQP_REQUER_INSPECAO_EXTERNA: int = 0
    TEQP_REQUER_INSPECAO_INTERNA: int = 0
    TEQP_DT_INS: Optional[datetime] = None
    TEQP_DT_UPD: Optional[datetime] = None

    class Config:
        from_attributes = True


class ManutTipoEquipamentoListResponse(BaseModel):
    """Schema de resposta para lista de ManutTipoEquipamento"""
    items: List[ManutTipoEquipamentoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# EQUIPAMENTOS
# ============================================================================

class ManutEquipamentoResponse(BaseModel):
    """Schema de resposta para ManutEquipamento"""
    EQP_ID: int
    EQP_CLI_ID: int
    CLI_NOME: Optional[str] = None
    EQP_TEQP_ID: Optional[int] = None
    EQP_TAG: str
    EQP_NUMERO_SERIE: Optional[str] = None
    EQP_NOME: Optional[str] = None
    EQP_AREA: Optional[str] = None
    EQP_QTD_EQPI: Optional[int] = None
    EQP_QTD_EQPI_VENCIDO: Optional[int] = None
    EQP_QTD_INST: Optional[int] = None
    EQP_QTD_INSC: Optional[int] = None
    EQP_QTD_INSC_CLASS_0: Optional[int] = None
    EQP_QTD_INSC_CLASS_1: Optional[int] = None
    EQP_QTD_INSC_CLASS_2: Optional[int] = None
    EQP_QTD_INSC_CLASS_3: Optional[int] = None
    EQP_QTD_INSC_CLASS_9: Optional[int] = None
    EQP_DT_INS: Optional[datetime] = None
    EQP_DT_UPD: Optional[datetime] = None

    class Config:
        from_attributes = True


class ManutEquipamentoListResponse(BaseModel):
    """Schema de resposta para lista de ManutEquipamento"""
    items: List[ManutEquipamentoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# STATUS DE SINCRONIZACAO
# ============================================================================

class SyncStatusResponse(BaseModel):
    """Status da última sincronização"""
    tabela: str
    total_registros: int
    ultima_sinc: Optional[datetime] = None
    proxima_sinc: Optional[datetime] = None
    nr13_data_ref_days_back: Optional[int] = None

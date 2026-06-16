"""
Schemas Pydantic para Reports
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Dict, Any, List


# ===== Schemas de Cliente e Equipamento (NR13) =====

class ClienteResponse(BaseModel):
    """Schema para cliente (tab_clientes - NR13)"""
    CLI_ID: int
    CLI_NOME: Optional[str] = None
    CLI_CNPJ: Optional[str] = None
    CLI_SITE: Optional[str] = None
    CLI_CONTATO: Optional[str] = None
    CLI_EMAIL: Optional[str] = None
    CLI_TELEFONE: Optional[str] = None
    CLI_CIDADE: Optional[str] = None
    CLI_ESTADO: Optional[str] = None

    class Config:
        from_attributes = True


class EquipamentoResponse(BaseModel):
    """Schema para equipamento (tab_equipamentos - NR13)"""
    EQP_ID: int
    EQP_CLI_ID: int
    EQP_TEQP_ID: Optional[int] = None
    EQP_TAG: str
    EQP_NUMERO_SERIE: Optional[str] = None
    EQP_NOME: Optional[str] = None
    EQP_AREA: Optional[str] = None

    class Config:
        from_attributes = True


class TecnicoResponse(BaseModel):
    id: int
    username: str
    nome: str
    email: str

    class Config:
        from_attributes = True


class FormTemplateResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None

    class Config:
        from_attributes = True


# ===== Schemas de Report =====

class ReportCreate(BaseModel):
    """Schema para criar novo relatório (KICKOFF) - Versão Simplificada"""
    form_template_id: int = Field(..., description="ID do template de formulário")
    cliente_id: Optional[int] = Field(None, description="ID do cliente (CLI_ID - tab_clientes)")
    equipamento_id: Optional[int] = Field(None, description="ID do equipamento (EQP_ID - tab_equipamentos)")
    tipo_inspecao: Optional[str] = Field(None, max_length=100, description="Tipo de inspeção (preenchido no formulário)")
    data_inspecao: Optional[date] = Field(None, description="Data da inspeção")
    observacoes: Optional[str] = Field(None, description="Observações iniciais")


class ReportUpdate(BaseModel):
    """Schema para atualizar respostas do relatório"""
    respostas: Dict[str, Any] = Field(..., description="Respostas do formulário em JSON")
    observacoes: Optional[str] = Field(None, description="Observações")
    data_inspecao: Optional[date] = Field(None, description="Data da inspeção")


class ReportStatusUpdate(BaseModel):
    """Schema para atualizar status do relatório"""
    status: str = Field(
        ...,
        description="Novo status",
        pattern="^(rascunho|em_revisao|em_correcao|aprovado|cancelado)$",
    )


class SolicitarCorrecaoRequest(BaseModel):
    """Solicitar devolução ao técnico (#246)"""
    descricao: str = Field(..., min_length=10, max_length=2000)


class ReportCorrecaoResponse(BaseModel):
    id: int
    report_id: int
    solicitado_por_id: int
    solicitado_por_nome: str
    descricao: str
    status_anterior: str
    status_novo: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReportCorrecaoListResponse(BaseModel):
    correcoes: List[ReportCorrecaoResponse]


class ReportResponse(BaseModel):
    """Schema de resposta completa do relatório"""
    id: int
    numero: str
    form_template_id: int
    cliente_id: Optional[int] = None
    equipamento_id: Optional[int] = None
    tipo_inspecao: Optional[str] = None
    tecnico_id: int
    status: str
    respostas: Dict[str, Any]
    observacoes: Optional[str] = None
    data_inspecao: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    # Relacionamentos (opcional)
    cliente: Optional[ClienteResponse] = None
    equipamento: Optional[EquipamentoResponse] = None
    tecnico: Optional[TecnicoResponse] = None
    form_template: Optional[FormTemplateResponse] = None

    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    """Schema simplificado para listagem"""
    id: int
    numero: str
    cliente_nome: Optional[str] = None
    equipamento_nome: Optional[str] = None
    tipo_inspecao: Optional[str] = None
    form_template_nome: Optional[str] = None
    tecnico_nome: str
    tecnico_id: int
    status: str
    data_inspecao: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema de resposta paginada"""
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página atual")
    limit: int = Field(..., description="Itens por página")
    reports: List[ReportListItem] = Field(..., description="Lista de relatórios")

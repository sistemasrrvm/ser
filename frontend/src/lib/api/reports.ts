import { api, apiExport } from './client'
import { Cliente } from './clientes'
import { Equipamento } from './equipamentos'

export interface Report {
  id: number
  numero: string
  form_template_id: number
  cliente_id: number | null
  equipamento_id: number | null
  tipo_inspecao: string | null
  tecnico_id: number
  status: 'rascunho' | 'em_revisao' | 'em_correcao' | 'aprovado' | 'cancelado'
  respostas: Record<string, any>
  observacoes: string | null
  data_inspecao: string | null
  created_at: string
  updated_at: string

  // Relacionamentos
  cliente?: Cliente
  equipamento?: Equipamento
  tecnico?: {
    id: number
    username: string
    nome: string
    email: string
  }
  form_template?: {
    id: number
    nome: string
    descricao: string | null
  }
}

export interface ReportCreate {
  form_template_id: number
  cliente_id?: number | null
  equipamento_id?: number | null
  tipo_inspecao?: string | null
  data_inspecao?: string | null
  observacoes?: string | null
}

export interface ReportUpdate {
  respostas: Record<string, any>
  observacoes?: string | null
  data_inspecao?: string | null
}

export interface ReportStatusUpdate {
  status: 'rascunho' | 'em_revisao' | 'em_correcao' | 'aprovado' | 'cancelado'
}

export interface ReportListItem {
  id: number
  numero: string
  cliente_nome: string | null
  equipamento_nome: string | null
  tipo_inspecao: string | null
  form_template_nome: string | null
  tecnico_nome: string
  tecnico_id: number
  status: string
  data_inspecao: string | null
  created_at: string
}

export interface ReportListResponse {
  total: number
  page: number
  limit: number
  reports: ReportListItem[]
}

export interface ReportCorrecao {
  id: number
  report_id: number
  solicitado_por_id: number
  solicitado_por_nome: string
  descricao: string
  status_anterior: string
  status_novo: string
  created_at: string
}

export interface ReportCorrecaoListResponse {
  correcoes: ReportCorrecao[]
}

export interface SolicitarCorrecaoRequest {
  descricao: string
}

export interface ReportFilters {
  status?: string
  cliente_id?: number
  equipamento_id?: number
  tecnico_id?: number
  data_inicio?: string
  data_fim?: string
  page?: number
  limit?: number
}

export const reportsApi = {
  /**
   * Criar novo relatório (KICKOFF)
   */
  create: async (data: ReportCreate): Promise<Report> => {
    const response = await api.post<Report>('/reports', data)
    return response.data
  },

  /**
   * Listar relatórios com filtros
   */
  list: async (filters?: ReportFilters): Promise<ReportListResponse> => {
    const response = await api.get<ReportListResponse>('/reports', {
      params: filters,
    })
    return response.data
  },

  /**
   * Obter relatório por ID
   */
  get: async (reportId: number): Promise<Report> => {
    const response = await api.get<Report>(`/reports/${reportId}`)
    return response.data
  },

  /**
   * Atualizar respostas do relatório
   */
  update: async (reportId: number, data: ReportUpdate): Promise<Report> => {
    const response = await api.put<Report>(`/reports/${reportId}`, data)
    return response.data
  },

  /**
   * Atualizar status do relatório
   */
  updateStatus: async (reportId: number, data: ReportStatusUpdate): Promise<Report> => {
    const response = await api.put<Report>(`/reports/${reportId}/status`, data)
    return response.data
  },

  requestCorrection: async (
    reportId: number,
    data: SolicitarCorrecaoRequest
  ): Promise<Report> => {
    const response = await api.post<Report>(`/reports/${reportId}/solicitar-correcao`, data)
    return response.data
  },

  listCorrecoes: async (reportId: number): Promise<ReportCorrecaoListResponse> => {
    const response = await api.get<ReportCorrecaoListResponse>(`/reports/${reportId}/correcoes`)
    return response.data
  },

  /**
   * Excluir relatório
   */
  delete: async (reportId: number): Promise<void> => {
    await api.delete(`/reports/${reportId}`)
  },

  /**
   * Exportar relatório para Excel
   * Usa apiExport com timeout estendido (2 minutos)
   */
  exportToExcel: async (reportId: number): Promise<Blob> => {
    const response = await apiExport.get(`/reports/${reportId}/export-excel`, {
      responseType: 'blob',
    })
    return response.data
  },

  /**
   * Exportar relatório para PDF
   * Usa apiExport com timeout estendido (2 minutos)
   */
  exportToPdf: async (reportId: number): Promise<Blob> => {
    const response = await apiExport.get(`/reports/${reportId}/export-pdf`, {
      responseType: 'blob',
    })
    return response.data
  },
}

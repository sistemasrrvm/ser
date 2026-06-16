/**
 * API Client - Dados NR13 (Cache SQL Server)
 */

import { api } from './client'

// ============================================================================
// TYPES
// ============================================================================

export interface ManutCliente {
  CLI_ID: number
  CLI_NOME: string | null
  CLI_CNPJ: string | null
  CLI_SITE: string | null
  CLI_CONTATO: string | null
  CLI_EMAIL: string | null
  CLI_TELEFONE: string | null
  CLI_ENDERECO: string | null
  CLI_NUMERO: string | null
  CLI_BAIRRO: string | null
  CLI_CEP: string | null
  CLI_CIDADE: string | null
  CLI_ESTADO: string | null
  CLI_DT_INS: string | null
  CLI_DT_UPD: string | null
}

export interface ManutClienteListResponse {
  items: ManutCliente[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ManutTipoEquipamento {
  TEQP_ID: number
  TEQP_NOME: string | null
  TEQP_VENC_CALIBRACAO: number | null
  TEQP_REQUER_INSPECAO_EXTERNA: number
  TEQP_REQUER_INSPECAO_INTERNA: number
  TEQP_DT_INS: string | null
  TEQP_DT_UPD: string | null
}

export interface ManutTipoEquipamentoListResponse {
  items: ManutTipoEquipamento[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ManutEquipamento {
  EQP_ID: number
  EQP_CLI_ID: number
  EQP_TEQP_ID: number | null
  EQP_TAG: string
  EQP_NUMERO_SERIE: string | null
  EQP_NOME: string | null
  EQP_AREA: string | null
  EQP_QTD_EQPI: number | null
  EQP_QTD_EQPI_VENCIDO: number | null
  EQP_QTD_INST: number | null
  EQP_QTD_INSC: number | null
  EQP_QTD_INSC_CLASS_0: number | null
  EQP_QTD_INSC_CLASS_1: number | null
  EQP_QTD_INSC_CLASS_2: number | null
  EQP_QTD_INSC_CLASS_3: number | null
  EQP_QTD_INSC_CLASS_9: number | null
  EQP_DT_INS: string | null
  EQP_DT_UPD: string | null
}

export interface ManutEquipamentoListResponse {
  items: ManutEquipamento[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface SyncStatus {
  tabela: string
  total_registros: number
  ultima_sinc: string | null
  proxima_sinc: string | null
}

export interface SyncResult {
  success: boolean
  results?: {
    clientes: { success: boolean; total?: number; inserted?: number; updated?: number; message?: string }
    tipos_equipamento: { success: boolean; total?: number; inserted?: number; updated?: number; message?: string }
    equipamentos: { success: boolean; total?: number; inserted?: number; updated?: number; message?: string }
  }
  timestamp?: string
  message?: string
}

// ============================================================================
// API FUNCTIONS
// ============================================================================

export const manutApi = {
  // Clientes
  listClientes: async (params?: {
    page?: number
    page_size?: number
    search?: string
    sort_by?: string
    sort_dir?: 'asc' | 'desc'
    ativo?: boolean
  }): Promise<ManutClienteListResponse> => {
    const response = await api.get<ManutClienteListResponse>('/manut/clientes', { params })
    return response.data
  },

  getClientesStatus: async (): Promise<SyncStatus> => {
    const response = await api.get<SyncStatus>('/manut/clientes/status')
    return response.data
  },

  // Tipos de Equipamento
  listTiposEquipamento: async (params?: {
    page?: number
    page_size?: number
    search?: string
    sort_by?: string
    sort_dir?: 'asc' | 'desc'
    ativo?: boolean
  }): Promise<ManutTipoEquipamentoListResponse> => {
    const response = await api.get<ManutTipoEquipamentoListResponse>('/manut/tipos-equipamento', { params })
    return response.data
  },

  getTiposEquipamentoStatus: async (): Promise<SyncStatus> => {
    const response = await api.get<SyncStatus>('/manut/tipos-equipamento/status')
    return response.data
  },

  // Equipamentos
  listEquipamentos: async (params?: {
    page?: number
    page_size?: number
    search?: string
    cliente_id?: number
    tipo_equipamento_id?: number
    sort_by?: string
    sort_dir?: 'asc' | 'desc'
    ativo?: boolean
  }): Promise<ManutEquipamentoListResponse> => {
    const response = await api.get<ManutEquipamentoListResponse>('/manut/equipamentos', { params })
    return response.data
  },

  getEquipamentosStatus: async (): Promise<SyncStatus> => {
    const response = await api.get<SyncStatus>('/manut/equipamentos/status')
    return response.data
  },

  // Sincronização
  triggerSync: async (): Promise<SyncResult> => {
    const response = await api.post<SyncResult>('/manut/sync')
    return response.data
  },

  testConnection: async (): Promise<{ connected: boolean; configured: boolean; config: any }> => {
    const response = await api.get('/manut/sync/test-connection')
    return response.data
  },
}

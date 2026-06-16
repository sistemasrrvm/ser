import { api } from './client'
import type { SortDirection } from '@/hooks/useTableSort'

/**
 * Cliente (tab_clientes - NR13)
 */
export interface Cliente {
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

export interface ClienteListResponse {
  items: Cliente[]
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
  nr13_data_ref_days_back?: number | null
}

export interface Nr13SyncOptions {
  semFiltroData?: boolean
  cliente_id?: number
}

export interface Nr13SyncEntityResult {
  success: boolean
  total: number
  inserted: number
  updated: number
  skipped: number
  message?: string | null
}

export interface Nr13SyncResponse {
  success: boolean
  data_ref: string
  results: Nr13SyncEntityResult
  timestamp: string
}

export interface ClienteListParams {
  page?: number
  page_size?: number
  search?: string
  cliente_id?: number
  nome?: string
  cnpj?: string
  sort_by?: string
  sort_dir?: SortDirection
}

export const clientesApi = {
  list: async (params?: ClienteListParams): Promise<ClienteListResponse> => {
    const response = await api.get<ClienteListResponse>('/clientes', { params })
    return response.data
  },

  get: async (clienteId: number): Promise<Cliente> => {
    const response = await api.get<Cliente>(`/clientes/${clienteId}`)
    return response.data
  },

  getStatus: async (): Promise<SyncStatus> => {
    const response = await api.get<SyncStatus>('/clientes/status')
    return response.data
  },

  sync: async (options?: Nr13SyncOptions): Promise<Nr13SyncResponse> => {
    const params: Record<string, string | number | boolean> = {}
    if (options?.semFiltroData) params.sem_filtro_data = true
    const response = await api.post<Nr13SyncResponse>('/clientes/sync', null, { params })
    return response.data
  },

  syncEquipamentos: async (
    clienteId: number,
    options?: Pick<Nr13SyncOptions, 'semFiltroData'>
  ): Promise<Nr13SyncResponse> => {
    const params: Record<string, boolean> = {}
    if (options?.semFiltroData) params.sem_filtro_data = true
    const response = await api.post<Nr13SyncResponse>(
      `/clientes/${clienteId}/sync-equipamentos`,
      null,
      { params }
    )
    return response.data
  },
}

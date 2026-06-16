import { api } from './client'
import type { SortDirection } from '@/hooks/useTableSort'
import type { SyncStatus, Nr13SyncResponse, Nr13SyncOptions } from './clientes'

/**
 * Equipamento (tab_equipamentos - NR13)
 */
export interface Equipamento {
  EQP_ID: number
  EQP_CLI_ID: number
  CLI_NOME?: string | null
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

export interface EquipamentoListResponse {
  items: Equipamento[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface EquipamentoListParams {
  page?: number
  page_size?: number
  equipamento_id?: number
  tag?: string
  nome?: string
  numero_serie?: string
  area?: string
  cliente_id?: number
  cliente_nome?: string
  tipo_equipamento_id?: number
  search?: string
  sort_by?: string
  sort_dir?: SortDirection
}

/** Filtros serializados na query ?filtros={...} ao abrir /equipamentos */
export interface EquipamentosFiltrosJson {
  cliente_id?: number
  cliente_nome?: string
  equipamento_id?: number
  tag?: string
  nome?: string
  numero_serie?: string
  area?: string
  tipo_equipamento_id?: number
}

export function parseEquipamentosFiltros(raw: string | null): EquipamentosFiltrosJson | null {
  if (!raw) return null
  try {
    const data = JSON.parse(raw) as EquipamentosFiltrosJson
    return data && typeof data === 'object' ? data : null
  } catch {
    return null
  }
}

export function buildEquipamentosUrl(filtros: EquipamentosFiltrosJson): string {
  return `/equipamentos?filtros=${encodeURIComponent(JSON.stringify(filtros))}`
}

export const equipamentosApi = {
  list: async (params?: EquipamentoListParams): Promise<EquipamentoListResponse> => {
    const response = await api.get<EquipamentoListResponse>('/equipamentos', { params })
    return response.data
  },

  get: async (equipamentoId: number): Promise<Equipamento> => {
    const response = await api.get<Equipamento>(`/equipamentos/${equipamentoId}`)
    return response.data
  },

  getStatus: async (): Promise<SyncStatus> => {
    const response = await api.get<SyncStatus>('/equipamentos/status')
    return response.data
  },

  sync: async (options?: Nr13SyncOptions): Promise<Nr13SyncResponse> => {
    const params: Record<string, string | number | boolean> = {}
    if (options?.semFiltroData) params.sem_filtro_data = true
    if (options?.cliente_id != null) params.cliente_id = options.cliente_id
    const response = await api.post<Nr13SyncResponse>('/equipamentos/sync', null, { params })
    return response.data
  },
}

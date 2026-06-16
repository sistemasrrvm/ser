import { api } from './client'
import type { SortDirection } from '@/hooks/useTableSort'
import type { SyncStatus } from './clientes'

/**
 * Tipo de equipamento (tab_tipos_equipamento - NR13)
 */
export interface TipoEquipamento {
  TEQP_ID: number
  TEQP_NOME: string | null
  TEQP_VENC_CALIBRACAO: number | null
  TEQP_REQUER_INSPECAO_EXTERNA: number
  TEQP_REQUER_INSPECAO_INTERNA: number
  TEQP_DT_INS: string | null
  TEQP_DT_UPD: string | null
}

export interface TipoEquipamentoListResponse {
  items: TipoEquipamento[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TipoEquipamentoListParams {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_dir?: SortDirection
}

export const tiposEquipamentoApi = {
  list: async (params?: TipoEquipamentoListParams): Promise<TipoEquipamentoListResponse> => {
    const response = await api.get<TipoEquipamentoListResponse>('/tipos-equipamento', { params })
    return response.data
  },

  getStatus: async (): Promise<SyncStatus> => {
    const response = await api.get<SyncStatus>('/tipos-equipamento/status')
    return response.data
  },
}

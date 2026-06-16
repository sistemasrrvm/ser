/**
 * API Client para Listas Lookup
 */

import { api } from './client'

export interface LookupListOption {
  id: string
  label: string
  filter?: string
}

export interface LookupListAPIConfig {
  url: string
  method?: string
  headers?: Record<string, string>
  mapping: Record<string, string>
  cache_ttl?: number
}

export interface LookupList {
  id: string
  nome: string
  descricao?: string
  opcoes: any[]
  config_api?: LookupListAPIConfig
  ultima_atualizacao?: string
  criado_em: string
  atualizado_em: string
}

export interface LookupListCreate {
  id: string
  nome: string
  descricao?: string
  opcoes: any[]
  config_api?: LookupListAPIConfig
}

export interface LookupListUpdate {
  nome?: string
  descricao?: string
  opcoes?: any[]
  config_api?: LookupListAPIConfig
}

export const lookupListsApi = {
  /**
   * Listar todas as listas
   */
  list: async (): Promise<{ total: number; listas: LookupList[] }> => {
    const response = await api.get('/lookup-lists')
    return response.data
  },

  /**
   * Obter lista específica
   */
  get: async (listId: string): Promise<LookupList> => {
    const response = await api.get(`/lookup-lists/${listId}`)
    return response.data
  },

  /**
   * Criar nova lista
   */
  create: async (data: LookupListCreate): Promise<LookupList> => {
    const response = await api.post('/lookup-lists', data)
    return response.data
  },

  /**
   * Atualizar lista
   */
  update: async (listId: string, data: LookupListUpdate): Promise<LookupList> => {
    const response = await api.put(`/lookup-lists/${listId}`, data)
    return response.data
  },

  /**
   * Deletar lista
   */
  delete: async (listId: string): Promise<{ message: string; id: string }> => {
    const response = await api.delete(`/lookup-lists/${listId}`)
    return response.data
  },

  /**
   * Obter opções de uma lista com filtro opcional
   */
  getOptions: async (listId: string, filter?: string): Promise<{ list_id: string; opcoes: LookupListOption[]; total: number }> => {
    const params = filter ? { filter } : {}
    const response = await api.get(`/lookup-lists/${listId}/options`, { params })
    return response.data
  },

  /**
   * Atualizar lista via API externa (botão refresh)
   */
  refresh: async (listId: string): Promise<LookupList> => {
    const response = await api.post(`/lookup-lists/${listId}/refresh`)
    return response.data
  },

  /**
   * Atualizar opções de lista (webhook)
   */
  updateOptions: async (listId: string, opcoes: LookupListOption[], token: string): Promise<LookupList> => {
    const response = await api.post(
      `/lookup-lists/${listId}/update`,
      { opcoes },
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    )
    return response.data
  }
}

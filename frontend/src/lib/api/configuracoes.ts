/**
 * API Client para Configurações
 */

import { api } from './client'

export interface Configuracao {
  id: number
  chave: string
  valor: string | null
  tipo: 'texto' | 'numero' | 'json' | 'boolean'
  descricao: string | null
  categoria: string
  created_at: string | null
  updated_at: string | null
}

export interface ConfiguracaoCreate {
  chave: string
  valor?: string | null
  tipo: 'texto' | 'numero' | 'json' | 'boolean'
  descricao?: string | null
  categoria: string
}

export interface ConfiguracaoUpdate {
  valor?: string | null
  tipo?: 'texto' | 'numero' | 'json' | 'boolean'
  descricao?: string | null
  categoria?: string
}

export interface ConfiguracaoListResponse {
  total: number
  configuracoes: Configuracao[]
}

export interface Nr13IntegracaoSettings {
  api_base_url: string
  api_base_url_resolved?: string
  basic_user: string
  basic_password: string
  basic_password_configured: boolean
  equipamento_tipo: string
  data_ref_days_back: number
  cron_secret: string
  cron_secret_configured: boolean
  timeout_seconds: number
  enabled: boolean
  configured: boolean
  source: 'env' | 'database' | 'mixed' | string
}

export interface Nr13IntegracaoSettingsUpdate {
  api_base_url: string
  basic_user: string
  basic_password?: string
  equipamento_tipo?: string
  data_ref_days_back?: number
  cron_secret?: string
  timeout_seconds?: number
  enabled?: boolean
}

export interface Nr13IntegracaoTestResult {
  success: boolean
  data_ref: string
  record_count: number
  request_url: string
  message: string
}

export interface EmailIntegracaoSettings {
  enabled: boolean
  smtp_host: string
  smtp_port: number
  smtp_use_ssl: boolean
  smtp_user: string
  smtp_password: string
  smtp_password_configured: boolean
  from_email: string
  from_name: string
  frontend_base_url: string
  configured: boolean
  source: 'env' | 'database' | 'mixed' | string
}

export interface EmailIntegracaoSettingsUpdate {
  enabled?: boolean
  smtp_host: string
  smtp_port?: number
  smtp_use_ssl?: boolean
  smtp_user: string
  smtp_password?: string
  from_email: string
  from_name?: string
  frontend_base_url?: string
}

export interface EmailIntegracaoTestRequest {
  report_id: number
  evento: 'finalizar' | 'solicitar_correcao' | 'aprovar'
  destinatario_teste: string
}

export interface EmailIntegracaoTestResult {
  success: boolean
  message: string
  subject: string
  destinatario: string
  log: string[]
}

export const configuracoesApi = {
  /**
   * Listar todas as configurações (com filtro opcional por categoria)
   */
  async list(categoria?: string): Promise<ConfiguracaoListResponse> {
    const params = categoria ? { categoria } : {}
    const response = await api.get('/configuracoes', { params })
    return response.data
  },

  /**
   * Obter configuração por ID
   */
  async get(id: number): Promise<Configuracao> {
    const response = await api.get(`/configuracoes/${id}`)
    return response.data
  },

  /**
   * Obter configuração por chave
   */
  async getByChave(chave: string): Promise<Configuracao> {
    const response = await api.get(`/configuracoes/chave/${chave}`)
    return response.data
  },

  /**
   * Criar nova configuração
   */
  async create(data: ConfiguracaoCreate): Promise<Configuracao> {
    const response = await api.post('/configuracoes', data)
    return response.data
  },

  /**
   * Atualizar configuração
   */
  async update(id: number, data: ConfiguracaoUpdate): Promise<Configuracao> {
    const response = await api.put(`/configuracoes/${id}`, data)
    return response.data
  },

  /**
   * Excluir configuração
   */
  async delete(id: number): Promise<{ message: string; id: number }> {
    const response = await api.delete(`/configuracoes/${id}`)
    return response.data
  },

  async getNr13Integracao(): Promise<Nr13IntegracaoSettings> {
    const response = await api.get('/configuracoes/nr13-integracao')
    return response.data
  },

  async updateNr13Integracao(data: Nr13IntegracaoSettingsUpdate): Promise<Nr13IntegracaoSettings> {
    const response = await api.put('/configuracoes/nr13-integracao', data)
    return response.data
  },

  async testNr13Integracao(dataRef?: string): Promise<Nr13IntegracaoTestResult> {
    const params = dataRef ? { data_ref: dataRef } : {}
    const response = await api.post('/configuracoes/nr13-integracao/test', null, { params })
    return response.data
  },

  async getEmailIntegracao(): Promise<EmailIntegracaoSettings> {
    const response = await api.get('/configuracoes/email-integracao')
    return response.data
  },

  async updateEmailIntegracao(data: EmailIntegracaoSettingsUpdate): Promise<EmailIntegracaoSettings> {
    const response = await api.put('/configuracoes/email-integracao', data)
    return response.data
  },

  async testEmailIntegracao(data: EmailIntegracaoTestRequest): Promise<EmailIntegracaoTestResult> {
    const response = await api.post('/configuracoes/email-integracao/test', data)
    return response.data
  },
}

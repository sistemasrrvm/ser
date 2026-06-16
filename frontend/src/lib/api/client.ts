/**
 * API Client - Axios configurado
 * Usa httpOnly cookies para autenticação
 */

import axios from 'axios'

// Criar instância do axios
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 60000,  // 60 segundos para operações normais
  withCredentials: true,  // IMPORTANTE: envia cookies automaticamente
  headers: {
    'Content-Type': 'application/json',
  },
})

// Instância específica para exportação de arquivos (Excel/PDF)
// com timeout maior devido ao processamento de arquivos grandes
export const apiExport = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 120000,  // 2 minutos para exports
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - adicionar token ao header
const requestInterceptor = (config: any) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}

const requestErrorInterceptor = (error: any) => {
  console.error('[axios] ERRO no request:', error)
  return Promise.reject(error)
}

// Response interceptor - tratamento de erros
const responseSuccessInterceptor = (response: any) => response

export function getApiErrorMessage(error: unknown, fallback = 'Erro desconhecido'): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const detail = (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (typeof item === 'string' ? item : (item as { msg?: string }).msg || String(item)))
        .join(', ')
    }
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}

const responseErrorInterceptor = async (error: any) => {
  const url = error.config?.url || 'URL desconhecida'
  const status = error.response?.status || 'Sem status'

  console.error(`[axios] ERRO - ${error.config?.method?.toUpperCase()} ${url} - Status: ${status}`)
  console.error('[axios] Detalhes:', error.response?.data?.detail || error.message)

  // Se 401 em endpoint que NÃO seja /auth/me, redirecionar para login
  const isAuthMeEndpoint = error.config?.url?.includes('/auth/me')

  if (error.response?.status === 401 && !isAuthMeEndpoint) {
    window.location.href = '/login'
  }

  return Promise.reject(error)
}

// Aplicar interceptors nas duas instâncias
api.interceptors.request.use(requestInterceptor, requestErrorInterceptor)
api.interceptors.response.use(responseSuccessInterceptor, responseErrorInterceptor)

apiExport.interceptors.request.use(requestInterceptor, requestErrorInterceptor)
apiExport.interceptors.response.use(responseSuccessInterceptor, responseErrorInterceptor)

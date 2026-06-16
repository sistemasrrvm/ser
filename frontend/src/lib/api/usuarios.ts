import { api } from './client'

export interface Role {
  id: number
  name: string
  level: number
  description?: string
}

export interface Usuario {
  id: number
  username: string
  full_name: string
  email?: string | null
  role: Role
  is_active: boolean
  last_login?: string | null
  created_at: string
  updated_at?: string
}

export interface UsuarioCreate {
  username: string
  password: string
  full_name: string
  email?: string | null
  role_id: number
  is_active?: boolean
}

export interface UsuarioUpdate {
  full_name?: string
  email?: string | null
  password?: string
  role_id?: number
  is_active?: boolean
}

export interface UsuarioListResponse {
  total: number
  users: Usuario[]
}

export const usuariosApi = {
  /**
   * Listar usuários
   * @param isActive true (apenas ativos), false (apenas inativos), undefined (todos)
   */
  list: async (isActive?: boolean): Promise<UsuarioListResponse> => {
    const params = isActive !== undefined ? { is_active: isActive } : {}
    const response = await api.get<UsuarioListResponse>('/usuarios', { params })
    return response.data
  },

  /**
   * Obter usuário por ID
   */
  get: async (usuarioId: number): Promise<Usuario> => {
    const response = await api.get<Usuario>(`/usuarios/${usuarioId}`)
    return response.data
  },

  /**
   * Criar novo usuário
   */
  create: async (data: UsuarioCreate): Promise<Usuario> => {
    const response = await api.post<Usuario>('/usuarios', data)
    return response.data
  },

  /**
   * Atualizar usuário
   */
  update: async (usuarioId: number, data: UsuarioUpdate): Promise<Usuario> => {
    const response = await api.put<Usuario>(`/usuarios/${usuarioId}`, data)
    return response.data
  },

  /**
   * Deletar usuário (soft delete)
   */
  delete: async (usuarioId: number): Promise<{ message: string; id: number }> => {
    const response = await api.delete(`/usuarios/${usuarioId}`)
    return response.data
  },

  /**
   * Excluir usuário definitivamente (hard delete)
   */
  deletePermanent: async (usuarioId: number): Promise<{ message: string; id: number }> => {
    const response = await api.delete(`/usuarios/${usuarioId}?permanent=true`)
    return response.data
  },

  /**
   * Reativar usuário inativo
   */
  reactivate: async (usuarioId: number): Promise<Usuario> => {
    const response = await api.patch<Usuario>(`/usuarios/${usuarioId}/reactivate`)
    return response.data
  },
}

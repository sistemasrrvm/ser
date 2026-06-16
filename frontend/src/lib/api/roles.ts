import { api } from './client'

export interface Role {
  id: number
  name: string
  level: number
  description?: string
}

export interface RoleListResponse {
  total: number
  roles: Role[]
}

export const rolesApi = {
  /**
   * Listar todos os roles/perfis disponíveis
   */
  list: async (): Promise<RoleListResponse> => {
    const response = await api.get<RoleListResponse>('/roles')
    return response.data
  },
}


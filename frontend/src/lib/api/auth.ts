/**
 * API - Autenticação
 */

import { api } from './client'
import type {
  LoginRequest,
  TokenResponse,
  PasswordResetRequest,
  PasswordResetResponse,
  PasswordResetConfirm,
  User,
} from './types'

export const authApi = {
  /**
   * Login (retorna tokens no corpo da resposta)
   */
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const { data } = await api.post<TokenResponse>('/auth/login', credentials)
    return data
  },

  /**
   * Logout (limpa cookies httpOnly)
   */
  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },

  /**
   * Obter usuário atual (autentica via cookie)
   */
  async getCurrentUser(): Promise<User> {
    const { data } = await api.get<User>('/auth/me')
    return data
  },

  /**
   * Solicitar recuperação de senha
   */
  async requestPasswordReset(
    request: PasswordResetRequest
  ): Promise<PasswordResetResponse> {
    const { data } = await api.post<PasswordResetResponse>(
      '/auth/password-reset/request',
      request
    )
    return data
  },

  /**
   * Confirmar nova senha
   */
  async confirmPasswordReset(request: PasswordResetConfirm): Promise<void> {
    await api.post('/auth/password-reset/confirm', request)
  },

  /**
   * Trocar senha (autenticado)
   */
  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<void> {
    await api.post('/auth/password/change', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },
}

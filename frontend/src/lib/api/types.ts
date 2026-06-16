/**
 * Tipos TypeScript para a API
 */

// Role
export interface Role {
  id: number
  name: string
  level: number
  description?: string
}

// User
export interface User {
  id: number
  username: string
  full_name: string
  email?: string
  role: Role
  is_active: boolean
  last_login?: string
  created_at: string
}

// Login
export interface LoginRequest {
  username: string
  password: string
  remember_me: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// Formulário
export interface Formulario {
  id: number
  nome: string
  descricao?: string
  excel_template?: string
  criado_em: string
  criado_por: number
  atualizado_em: string
  atualizado_por?: number
  total_paginas?: number
  total_campos?: number
}

export interface FormularioCreate {
  nome: string
  descricao?: string
}

export interface FormularioUpdate {
  nome?: string
  descricao?: string
  excel_template?: string
}

export interface FormularioListResponse {
  total: number
  formularios: Formulario[]
}

// Password Reset
export interface PasswordResetRequest {
  username: string
}

export interface PasswordResetResponse {
  message: string
  reset_token: string
  expires_in_hours: number
}

export interface PasswordResetConfirm {
  token: string
  new_password: string
}

// API Error
export interface ApiError {
  detail: string | { msg: string; type: string }[]
}

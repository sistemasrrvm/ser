/**
 * Auth Context - Gerenciamento de autenticação
 */

import React, { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/auth'
import type { User, LoginRequest } from '../api/types'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => void
  isAdmin: () => boolean
  hasMinLevel: (minLevel: number) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  // Carregar usuário via API (autenticação por token em localStorage)
  useEffect(() => {
    const loadUser = async () => {
      try {
        const token = localStorage.getItem('access_token')
        if (!token) {
          setUser(null)
          setIsLoading(false)
          return
        }

        const user = await authApi.getCurrentUser()
        setUser(user)
      } catch (error: any) {
        if (error?.response?.status === 401) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        }
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    loadUser()
  }, [])

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authApi.login(credentials)
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      setUser(response.user)
      setTimeout(() => navigate('/dashboard'), 0)
    } catch (error: any) {
      throw error
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch {
      // ignora erro
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
      navigate('/login')
    }
  }

  const isAdmin = () => {
    return user?.role.level === 100
  }

  const hasMinLevel = (minLevel: number) => {
    return (user?.role.level ?? 0) >= minLevel
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    isAdmin,
    hasMinLevel,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

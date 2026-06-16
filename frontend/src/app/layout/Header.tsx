/**
 * Header - Barra superior com informações do usuário
 */

import { useState } from 'react'
import { useAuth } from '@/lib/auth/AuthContext'
import { LogOut, ChevronDown, User } from 'lucide-react'

export const Header = () => {
  const { user, logout } = useAuth()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const getInitials = (name: string) => {
    const parts = name.split(' ')
    return parts.length >= 2
      ? `${parts[0][0]}${parts[1][0]}`.toUpperCase()
      : name.slice(0, 2).toUpperCase()
  }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Título da página ou breadcrumb */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            Bem-vindo, {user?.full_name.split(' ')[0]}
          </h2>
          <p className="text-sm text-gray-500">
            Sistema de coleta de dados para laudos técnicos industriais
          </p>
        </div>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="flex items-center space-x-3 hover:bg-gray-100 rounded-lg px-3 py-2 transition-colors"
          >
            {/* Avatar */}
            <div className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center font-semibold">
              {getInitials(user?.full_name || '')}
            </div>

            {/* User info */}
            <div className="text-left hidden sm:block">
              <p className="text-sm font-medium text-gray-900">
                {user?.full_name}
              </p>
              <p className="text-xs text-gray-500">{user?.role.name}</p>
            </div>

            <ChevronDown size={16} className="text-gray-500" />
          </button>

          {/* Dropdown menu */}
          {isMenuOpen && (
            <>
              {/* Overlay para fechar ao clicar fora */}
              <div
                className="fixed inset-0 z-10"
                onClick={() => setIsMenuOpen(false)}
              />

              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
                <div className="px-4 py-2 border-b border-gray-200">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.full_name}
                  </p>
                  <p className="text-xs text-gray-500">{user?.email}</p>
                </div>

                <button
                  onClick={() => {
                    setIsMenuOpen(false)
                    // TODO: Navegar para perfil
                  }}
                  className="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  <User size={16} className="mr-2" />
                  Meu Perfil
                </button>

                <button
                  onClick={() => {
                    setIsMenuOpen(false)
                    logout()
                  }}
                  className="w-full flex items-center px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <LogOut size={16} className="mr-2" />
                  Sair
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

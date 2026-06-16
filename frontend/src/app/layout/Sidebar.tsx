/**
 * Sidebar - Menu lateral de navegação
 */

import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '@/lib/auth/AuthContext'
import { canAccessMenuItem } from '@/lib/auth/permissions'
import {
  LayoutDashboard,
  Users,
  Building2,
  Wrench,
  File,
  Settings,
  Database,
} from 'lucide-react'

interface MenuItem {
  label: string
  icon: React.ReactNode
  path: string
  adminOnly?: boolean // Deprecated - usar canAccessMenuItem
}

interface MenuSection {
  title?: string
  items: MenuItem[]
  adminOnly?: boolean // Deprecated - usar canAccessMenuItem
}

const menuSections: MenuSection[] = [
  // Sem agrupamento
  {
    items: [
      {
        label: 'Dashboard',
        icon: <LayoutDashboard size={20} />,
        path: '/dashboard',
      },
      {
        label: 'Relatórios',
        icon: <LayoutDashboard size={20} />,
        path: '/relatorios',
      },
    ],
  },
  // CADASTROS NR13
  {
    title: 'CADASTROS NR13',
    items: [
      {
        label: 'Clientes',
        icon: <Building2 size={20} className="text-[#56991f]" />,
        path: '/clientes',
      },
      {
        label: 'Equipamentos',
        icon: <Wrench size={20} className="text-[#56991f]" />,
        path: '/equipamentos',
      },
      {
        label: 'Tipos Equipamento',
        icon: <Settings size={20} className="text-[#56991f]" />,
        path: '/tipos',
      },
    ],
  },
  // FORMULÁRIO
  {
    title: 'FORMULÁRIO',
    items: [
      {
        label: 'Formulários',
        icon: <File size={20} className="text-[#56991f]" />,
        path: '/formularios',
      },
      {
        label: 'Listas',
        icon: <Database size={20} className="text-[#56991f]" />,
        path: '/listas',
      },
    ],
  },
  // ADMINISTRAÇÃO
  {
    title: 'ADMINISTRAÇÃO',
    items: [
      {
        label: 'Usuários',
        icon: <Users size={20} />,
        path: '/usuarios',
      },
      {
        label: 'Configurações',
        icon: <Settings size={20} />,
        path: '/configuracoes',
      },
    ],
  },
]

export const Sidebar = () => {
  const location = useLocation()
  const { user } = useAuth()

  const isActive = (path: string) => {
    if (path === location.pathname) return true
    // Para rotas dinâmicas como /relatorios/:id/preencher
    if (path.includes(':')) {
      const pathPattern = path.replace(/:[^/]+/g, '[^/]+')
      const regex = new RegExp(`^${pathPattern}$`)
      return regex.test(location.pathname)
    }
    return false
  }

  return (
    <div className="w-64 bg-sidebar border-r border-gray-300 flex flex-col">
      {/* Logo / Brand */}
      <div className="px-6 py-4 border-b border-gray-300">
        <div className="flex items-center space-x-3">
          <img
            src="/logo-rrvm.png"
            alt="RRVM Logo"
            className="h-12 w-auto object-contain"
          />
          <div>
            <h1 className="text-sm font-bold text-gray-900">SER</h1>
            <p className="text-xs text-gray-500">Sistema de Emissão de Relatórios</p>
          </div>
        </div>
      </div>

      {/* Navegação */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto">
        {menuSections.map((section, sectionIndex) => {
          // Filtrar itens que o usuário pode ver baseado em permissões
          const visibleItems = section.items.filter((item) =>
            canAccessMenuItem(user, item.path)
          )

          // Se não há itens visíveis, não renderizar a seção
          if (visibleItems.length === 0) return null

          return (
            <div
              key={sectionIndex}
              className={sectionIndex > 0 ? 'mt-6 space-y-1' : 'space-y-1'}
            >
              {/* Título da seção (se existir) */}
              {section.title && (
                <p className="px-3 text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#366595' }}>
                  {section.title}
                </p>
              )}

              {/* Itens da seção */}
              {visibleItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`sidebar-item ${isActive(item.path) ? 'active' : ''}`}
                >
                  {item.icon}
                  <span className="ml-3">{item.label}</span>
                </Link>
              ))}
            </div>
          )
        })}
      </nav>
    </div>
  )
}

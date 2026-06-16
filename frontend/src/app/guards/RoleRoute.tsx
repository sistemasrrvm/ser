/**
 * Role Route - Guarda de rota baseada em perfil/role
 */

import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/lib/auth/AuthContext'
import { hasPermission, RoleName, isAdministrador, isSuporte, isTecnico, canCreateReport } from '@/lib/auth/permissions'

interface RoleRouteProps {
  children: React.ReactNode
  allowedRoles?: RoleName[]
  requiredRole?: RoleName
}

export const RoleRoute: React.FC<RoleRouteProps> = ({
  children,
  allowedRoles,
  requiredRole,
}) => {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-gray-600">Carregando...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Kickoff de relatório: somente Técnico (#244)
  if (location.pathname === '/novo-relatorio' && !canCreateReport(user)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="card text-center max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-2">Acesso Negado</h2>
          <p className="text-gray-600 mb-4">
            Você não tem permissão para acessar esta página.
          </p>
        </div>
      </div>
    )
  }

  // Verificar se o usuário tem o role requerido
  if (requiredRole) {
    // Se requer Administrador, verificar de forma flexível
    if (requiredRole === RoleName.ADMINISTRADOR && !isAdministrador(user)) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="card text-center max-w-md">
            <h2 className="text-2xl font-bold text-red-600 mb-2">Acesso Negado</h2>
            <p className="text-gray-600 mb-4">
              Você não tem permissão para acessar esta página.
            </p>
            <p className="text-sm text-gray-500">
              Requer: {requiredRole}
              <br />
              Seu perfil: {user.role.name} (nível {user.role.level})
            </p>
          </div>
        </div>
      )
    } else if (user.role.name !== requiredRole && 
               !(requiredRole === RoleName.ADMINISTRADOR && isAdministrador(user))) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="card text-center max-w-md">
            <h2 className="text-2xl font-bold text-red-600 mb-2">Acesso Negado</h2>
            <p className="text-gray-600 mb-4">
              Você não tem permissão para acessar esta página.
            </p>
            <p className="text-sm text-gray-500">
              Requer: {requiredRole}
              <br />
              Seu perfil: {user.role.name} (nível {user.role.level})
            </p>
          </div>
        </div>
      )
    }
  }

  // Verificar se o usuário tem um dos roles permitidos
  if (allowedRoles && allowedRoles.length > 0) {
    // Se é administrador, sempre permite
    if (isAdministrador(user)) {
      // Administrador tem acesso total - pode passar direto
    } else {
      // Verificar se o usuário tem algum dos roles permitidos usando funções de verificação
      const hasAllowedRole = allowedRoles.some((role) => {
        if (role === RoleName.ADMINISTRADOR) {
          return isAdministrador(user)
        }
        if (role === RoleName.SUPORTE) {
          return isSuporte(user) // isSuporte já verifica se é admin também
        }
        if (role === RoleName.TECNICO) {
          return isTecnico(user) // isTecnico já verifica se é suporte ou admin também
        }
        
        // Fallback: verificar por nome exato (case-insensitive)
        const normalizedRoleName = user.role.name.toLowerCase()
        const normalizedAllowedRole = role.toLowerCase()
        return normalizedRoleName === normalizedAllowedRole
      })
      
      if (!hasAllowedRole) {
        return (
          <div className="flex items-center justify-center min-h-screen">
            <div className="card text-center max-w-md">
              <h2 className="text-2xl font-bold text-red-600 mb-2">Acesso Negado</h2>
              <p className="text-gray-600 mb-4">
                Você não tem permissão para acessar esta página.
              </p>
              <p className="text-sm text-gray-500">
                Perfis permitidos: {allowedRoles.join(', ')}
                <br />
                Seu perfil: {user.role.name} (nível {user.role.level})
              </p>
            </div>
          </div>
        )
      }
    }
  }

  // Verificar permissão para a rota atual (apenas se não for administrador)
  // Se passou pela verificação de allowedRoles, já garantiu o acesso
  if (!isAdministrador(user) && !hasPermission(user, location.pathname)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="card text-center max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-2">Acesso Negado</h2>
          <p className="text-gray-600 mb-4">
            Você não tem permissão para acessar esta página.
          </p>
          <p className="text-sm text-gray-500">
            Rota: {location.pathname}
            <br />
            Seu perfil: {user.role.name} (nível {user.role.level})
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}


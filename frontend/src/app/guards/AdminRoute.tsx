/**
 * Admin Route - Guarda de rota para administradores
 */

import { RoleRoute } from './RoleRoute'
import { RoleName } from '@/lib/auth/permissions'

interface AdminRouteProps {
  children: React.ReactNode
}

export const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  return (
    <RoleRoute requiredRole={RoleName.ADMINISTRADOR}>
      {children}
    </RoleRoute>
  )
}

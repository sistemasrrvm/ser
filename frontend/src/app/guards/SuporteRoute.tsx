/**
 * Suporte Route - Guarda de rota para perfil Suporte ou Administrador
 */

import { RoleRoute } from './RoleRoute'
import { RoleName } from '@/lib/auth/permissions'

interface SuporteRouteProps {
  children: React.ReactNode
}

export const SuporteRoute: React.FC<SuporteRouteProps> = ({ children }) => {
  return (
    <RoleRoute allowedRoles={[RoleName.SUPORTE, RoleName.ADMINISTRADOR]}>
      {children}
    </RoleRoute>
  )
}


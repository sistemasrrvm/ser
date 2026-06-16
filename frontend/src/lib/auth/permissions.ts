/**
 * Permissões e controle de acesso baseado em perfis
 */

import type { User } from '../api/types'

// Perfis do sistema
export enum RoleName {
  TECNICO = 'Tecnico',
  SUPORTE = 'Suporte',
  ADMINISTRADOR = 'Administrador',
}

/** Nomes normalizados que equivalem ao perfil Suporte (Suporte ao Cliente) */
export const SUPORTE_ROLE_ALIASES = ['suporte', 'suporte ao cliente', 'revisor'] as const

/** Nomes normalizados do perfil Técnico (único que pode criar relatório) */
export const TECNICO_ROLE_ALIASES = ['tecnico', 'usuario'] as const

function normalizeRoleName(name: string): string {
  return name.trim().toLowerCase()
}

// Definição de permissões por perfil
// Aceita tanto nomes normalizados quanto nomes do banco (minúsculos)
export const ROLE_PERMISSIONS: Record<string, string[]> = {
  [RoleName.TECNICO]: [
    '/dashboard',
    '/relatorios',
    '/novo-relatorio',
    '/relatorios/:id/preencher',
  ],
  'tecnico': [
    '/dashboard',
    '/relatorios',
    '/novo-relatorio',
    '/relatorios/:id/preencher',
  ],
  [RoleName.SUPORTE]: [
    '/dashboard',
    '/relatorios',
    '/relatorios/:id/preencher',
    '/clientes',
    '/clientes/:id',
    '/equipamentos',
    '/tipos',
    '/nr13/equipamentos',
    '/nr13/tipos',
    '/nr13/clientes',
  ],
  'suporte': [
    '/dashboard',
    '/relatorios',
    '/relatorios/:id/preencher',
    '/clientes',
    '/clientes/:id',
    '/equipamentos',
    '/tipos',
    '/nr13/equipamentos',
    '/nr13/tipos',
    '/nr13/clientes',
  ],
  [RoleName.ADMINISTRADOR]: [
    // Acesso total - todos os caminhos são permitidos
    '*',
  ],
  'admin': [
    // Acesso total - todos os caminhos são permitidos
    '*',
  ],
  'administrador': [
    // Acesso total - todos os caminhos são permitidos
    '*',
  ],
}

/**
 * Verifica se o usuário tem permissão para acessar uma rota
 */
export function hasPermission(user: User | null, path: string): boolean {
  if (!user) return false

  // Criação de relatório: somente Técnico puro (#244)
  if (path === '/novo-relatorio' || path.endsWith('/novo-relatorio')) {
    return canCreateReport(user)
  }

  const roleName = user.role.name
  const roleLevel = user.role.level

  // Verificar se é administrador (pode ser "admin" ou "Administrador" ou level >= 100)
  const isAdmin = 
    roleName === RoleName.ADMINISTRADOR || 
    roleName === 'admin' || 
    roleName === 'Administrador' ||
    roleLevel >= 100

  // Administrador tem acesso total
  if (isAdmin) return true

  // Normalizar nome do role (aceitar maiúsculas/minúsculas)
  const normalizedRoleName = roleName.toLowerCase()
  
  // Buscar permissões pelo nome do role (tentar várias variações)
  let permissions = 
    ROLE_PERMISSIONS[roleName] || 
    ROLE_PERMISSIONS[normalizedRoleName] ||
    ROLE_PERMISSIONS[roleName.charAt(0).toUpperCase() + roleName.slice(1).toLowerCase()]
  
  // Se não encontrou, tentar mapear roles por nome normalizado ou level
  if (!permissions) {
    if (normalizedRoleName === 'admin' || normalizedRoleName === 'administrador' || roleLevel >= 100) {
      permissions = ROLE_PERMISSIONS[RoleName.ADMINISTRADOR] || ROLE_PERMISSIONS['admin']
    } else if (normalizedRoleName === 'suporte' || normalizedRoleName === 'revisor' || (roleLevel >= 50 && roleLevel < 100)) {
      permissions = ROLE_PERMISSIONS[RoleName.SUPORTE] || ROLE_PERMISSIONS['suporte']
    } else if (normalizedRoleName === 'tecnico' || normalizedRoleName === 'usuario' || (roleLevel >= 20 && roleLevel < 50)) {
      permissions = ROLE_PERMISSIONS[RoleName.TECNICO] || ROLE_PERMISSIONS['tecnico']
    }
  }

  if (!permissions) return false

  // Verificar se o path exato está nas permissões
  if (permissions.includes(path)) return true

  // Verificar se algum padrão de permissão corresponde ao path
  // Ex: /relatorios/123/preencher corresponde a /relatorios/:id/preencher
  return permissions.some((permission) => {
    const pattern = permission.replace(/:[^/]+/g, '[^/]+')
    const regex = new RegExp(`^${pattern}$`)
    return regex.test(path)
  })
}

/**
 * Verifica se o usuário tem um perfil específico
 */
export function hasRole(user: User | null, roleName: RoleName | string): boolean {
  if (!user) return false
  return user.role.name === roleName
}

/**
 * Verifica se o usuário é Administrador
 */
export function isAdministrador(user: User | null): boolean {
  if (!user) return false
  return (
    hasRole(user, RoleName.ADMINISTRADOR) ||
    hasRole(user, 'admin') ||
    hasRole(user, 'Administrador') ||
    user.role.level >= 100
  )
}

/**
 * Verifica se o usuário é Suporte
 */
export function isSuporte(user: User | null): boolean {
  if (!user) return false
  const normalizedRoleName = normalizeRoleName(user.role.name)
  return (
    hasRole(user, RoleName.SUPORTE) ||
    hasRole(user, 'Suporte') ||
    (SUPORTE_ROLE_ALIASES as readonly string[]).includes(normalizedRoleName) ||
    (user.role.level >= 50 && user.role.level < 100) ||
    isAdministrador(user) // Administrador também tem acesso de Suporte
  )
}

/** Suporte sem perfil Administrador (#275 — matriz de relatórios) */
export function isSuportePuro(user: User | null): boolean {
  if (!user || isAdministrador(user)) return false
  const normalizedRoleName = normalizeRoleName(user.role.name)
  return (
    hasRole(user, RoleName.SUPORTE) ||
    hasRole(user, 'Suporte') ||
    (SUPORTE_ROLE_ALIASES as readonly string[]).includes(normalizedRoleName) ||
    (user.role.level >= 50 && user.role.level < 100)
  )
}

/**
 * Técnico sem perfis elevados (não Admin, não Suporte).
 * Único perfil que pode criar novo relatório (#244).
 */
export function isTecnicoPuro(user: User | null): boolean {
  if (!user) return false
  if (isAdministrador(user) || isSuportePuro(user)) return false

  const normalizedRoleName = normalizeRoleName(user.role.name)
  return (
    hasRole(user, RoleName.TECNICO) ||
    hasRole(user, 'Tecnico') ||
    (TECNICO_ROLE_ALIASES as readonly string[]).includes(normalizedRoleName) ||
    (user.role.level >= 20 && user.role.level < 50)
  )
}

/** Apenas Técnico pode criar relatório (Suporte e Administrador: não) */
export function canCreateReport(user: User | null): boolean {
  return isTecnicoPuro(user)
}

/**
 * Verifica se o usuário é Tecnico
 */
export function isTecnico(user: User | null): boolean {
  if (!user) return false
  
  // Primeiro verificar se é admin ou suporte (que têm acesso de técnico também)
  if (isAdministrador(user) || isSuporte(user)) {
    return true
  }
  
  // Verificar se é técnico diretamente
  const normalizedRoleName = user.role.name.toLowerCase()
  return (
    hasRole(user, RoleName.TECNICO) ||
    hasRole(user, 'Tecnico') ||
    normalizedRoleName === 'tecnico' ||
    normalizedRoleName === 'usuario' ||
    (user.role.level >= 20 && user.role.level < 50)
  )
}

/**
 * Verifica se o usuário tem permissão para acessar um item de menu
 */
export function canAccessMenuItem(user: User | null, path: string): boolean {
  if (!user) return false

  const roleName = user.role.name
  const roleLevel = user.role.level

  // Verificar se é administrador (pode ser "admin" ou "Administrador" ou level >= 100)
  const isAdmin = 
    roleName === RoleName.ADMINISTRADOR || 
    roleName === 'admin' || 
    roleName === 'Administrador' ||
    roleLevel >= 100

  // Normalizar nome do role
  const normalizedRoleName = roleName.toLowerCase()

  // Verificar se é suporte (pode ser "suporte", "Suporte" ou level >= 50)
  const isSuporte = 
    roleName === RoleName.SUPORTE || 
    roleName === 'Suporte' ||
    normalizedRoleName === 'suporte' ||
    normalizedRoleName === 'revisor' ||
    (roleLevel >= 50 && roleLevel < 100) ||
    isAdmin

  // Verificar se é tecnico (pode ser "tecnico", "Tecnico", "usuario" ou level >= 20)
  const isTecnico = 
    roleName === RoleName.TECNICO || 
    roleName === 'Tecnico' ||
    normalizedRoleName === 'tecnico' ||
    normalizedRoleName === 'usuario' ||
    (roleLevel >= 20 && roleLevel < 50) ||
    isSuporte ||
    isAdmin

  // Mapeamento de rotas para verificações de permissão
  const routePermissions: Record<string, string[]> = {
    '/dashboard': [RoleName.TECNICO, RoleName.SUPORTE, RoleName.ADMINISTRADOR],
    '/relatorios': [RoleName.TECNICO, RoleName.SUPORTE, RoleName.ADMINISTRADOR],
    '/novo-relatorio': [RoleName.TECNICO],
    '/clientes': [RoleName.SUPORTE, RoleName.ADMINISTRADOR],
    '/clientes/:id': [RoleName.SUPORTE, RoleName.ADMINISTRADOR],
    '/equipamentos': [RoleName.SUPORTE, RoleName.ADMINISTRADOR],
    '/tipos': [RoleName.SUPORTE, RoleName.ADMINISTRADOR],
    '/nr13/clientes': [RoleName.SUPORTE, RoleName.ADMINISTRADOR],
    '/nr13/equipamentos': [RoleName.SUPORTE, RoleName.ADMINISTRADOR],
    '/nr13/tipos': [RoleName.SUPORTE, RoleName.ADMINISTRADOR],
    '/formularios': [RoleName.ADMINISTRADOR],
    '/listas': [RoleName.ADMINISTRADOR],
    '/usuarios': [RoleName.ADMINISTRADOR],
    '/configuracoes': [RoleName.ADMINISTRADOR],
  }

  const allowedRoles = routePermissions[path]
  if (!allowedRoles) {
    // Se a rota não está mapeada, apenas administrador pode acessar
    return isAdmin
  }

  // Kickoff: somente Técnico puro
  if (path === '/novo-relatorio') {
    return canCreateReport(user)
  }

  // Verificar acesso baseado em roles ou levels
  for (const allowedRole of allowedRoles) {
    if (allowedRole === RoleName.ADMINISTRADOR && isAdmin) return true
    if (allowedRole === RoleName.SUPORTE && (isSuporte || isAdmin)) return true
    if (allowedRole === RoleName.TECNICO && (isTecnico || isSuporte || isAdmin)) return true
  }

  return false
}


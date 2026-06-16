/**
 * Permissões de relatório por perfil e status (#275 / #246).
 */

import type { User } from '../api/types'
import {
  isAdministrador,
  isSuportePuro,
  isTecnicoPuro,
} from '../auth/permissions'

export type ReportStatus =
  | 'rascunho'
  | 'em_revisao'
  | 'em_correcao'
  | 'aprovado'
  | 'cancelado'

export interface ReportPermissionContext {
  status: ReportStatus | string
  tecnico_id: number
}

function isOwner(user: User, report: ReportPermissionContext): boolean {
  return report.tecnico_id === user.id
}

export function canViewReport(
  user: User | null,
  report: ReportPermissionContext
): boolean {
  if (!user) return false
  if (isAdministrador(user)) return true
  if (isSuportePuro(user)) return report.status !== 'rascunho'
  if (isTecnicoPuro(user)) return isOwner(user, report)
  return false
}

export function canEditReport(
  user: User | null,
  report: ReportPermissionContext
): boolean {
  if (!user) return false
  if (isSuportePuro(user)) return report.status === 'em_revisao'
  if (isTecnicoPuro(user)) {
    return (
      isOwner(user, report) &&
      (report.status === 'rascunho' || report.status === 'em_correcao')
    )
  }
  return false
}

export function canDeleteReport(
  user: User | null,
  report: ReportPermissionContext
): boolean {
  if (!user) return false
  return (
    isTecnicoPuro(user) &&
    isOwner(user, report) &&
    report.status === 'rascunho'
  )
}

export function canFinalizeReport(
  user: User | null,
  report: ReportPermissionContext
): boolean {
  if (!user || !isTecnicoPuro(user) || !isOwner(user, report)) return false
  return report.status === 'rascunho' || report.status === 'em_correcao'
}

export function canExportReportExcel(
  user: User | null,
  report: ReportPermissionContext
): boolean {
  if (!user || !isSuportePuro(user)) return false
  return report.status === 'em_revisao' || report.status === 'aprovado'
}

export function canApproveReport(
  user: User | null,
  report: ReportPermissionContext
): boolean {
  if (!user || !isSuportePuro(user)) return false
  return report.status === 'em_revisao'
}

export function canRequestCorrection(
  user: User | null,
  report: ReportPermissionContext
): boolean {
  if (!user || !isSuportePuro(user)) return false
  return report.status === 'em_revisao'
}

export function shouldHideElaboracaoStats(user: User | null): boolean {
  return isSuportePuro(user)
}

export function filterReportsForDashboard<T extends { status: string }>(
  user: User | null,
  reports: T[]
): T[] {
  if (!user || !shouldHideElaboracaoStats(user)) return reports
  return reports.filter((r) => r.status !== 'rascunho')
}

export function getReportListActionLabel(
  user: User | null,
  report: ReportPermissionContext
): 'Editar' | 'Visualizar' {
  return canEditReport(user, report) ? 'Editar' : 'Visualizar'
}

import type { ReportStatus } from './statusLabels'

export const REPORT_STATUS_BADGE_CLASSES: Record<ReportStatus, string> = {
  rascunho: 'bg-gray-100 text-gray-800',
  em_revisao: 'bg-blue-100 text-blue-800',
  em_correcao: 'bg-orange-100 text-orange-800',
  aprovado: 'bg-green-100 text-green-800',
  cancelado: 'bg-red-100 text-red-800',
}

export const REPORT_STATUS_COLUMN_BORDER: Record<ReportStatus, string> = {
  rascunho: 'border-t-gray-400',
  em_correcao: 'border-t-orange-500',
  em_revisao: 'border-t-blue-500',
  aprovado: 'border-t-green-500',
  cancelado: 'border-t-red-400',
}

export function getReportStatusBadgeClass(status: string): string {
  return (
    REPORT_STATUS_BADGE_CLASSES[status as ReportStatus] ??
    REPORT_STATUS_BADGE_CLASSES.rascunho
  )
}

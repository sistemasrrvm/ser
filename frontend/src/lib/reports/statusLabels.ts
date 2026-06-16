import type { Report } from '@/lib/api/reports'

export type ReportStatus = Report['status']

export const REPORT_STATUS_LABELS: Record<ReportStatus, string> = {
  rascunho: 'Em Elaboração',
  em_revisao: 'Em Revisão',
  em_correcao: 'Em Correção',
  aprovado: 'Aprovado',
  cancelado: 'Cancelado',
}

export function getReportStatusLabel(status: string): string {
  return REPORT_STATUS_LABELS[status as ReportStatus] ?? status
}

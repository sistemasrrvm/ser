import type { ReportListItem } from '@/lib/api/reports'
import type { ReportStatus } from './statusLabels'
import { REPORT_STATUS_LABELS } from './statusLabels'

/** Ordem do fluxo no quadro (#298). */
export const KANBAN_STATUS_ORDER: ReportStatus[] = [
  'rascunho',
  'em_correcao',
  'em_revisao',
  'aprovado',
  'cancelado',
]

export type ReportKanbanColumn = {
  status: ReportStatus
  label: string
  reports: ReportListItem[]
}

export function buildReportKanbanColumns(
  reports: ReportListItem[],
  options?: { hideRascunho?: boolean }
): ReportKanbanColumn[] {
  const statuses = KANBAN_STATUS_ORDER.filter(
    (s) => !(options?.hideRascunho && s === 'rascunho')
  )

  const byStatus = new Map<ReportStatus, ReportListItem[]>()
  for (const status of statuses) {
    byStatus.set(status, [])
  }

  for (const report of reports) {
    const status = report.status as ReportStatus
    const list = byStatus.get(status)
    if (list) list.push(report)
  }

  return statuses.map((status) => ({
    status,
    label: REPORT_STATUS_LABELS[status],
    reports: byStatus.get(status) ?? [],
  }))
}

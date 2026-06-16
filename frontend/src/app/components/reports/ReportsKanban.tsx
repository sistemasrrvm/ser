import { useMemo } from 'react'
import type { ReportListItem } from '@/lib/api/reports'
import type { User } from '@/lib/api/types'
import {
  canDeleteReport,
  canViewReport,
  getReportListActionLabel,
} from '@/lib/reports/reportPermissions'
import { buildReportKanbanColumns } from '@/lib/reports/reportsKanbanLayout'
import { REPORT_STATUS_COLUMN_BORDER } from '@/lib/reports/reportStatusStyles'
import { Button } from '@/components/ui/button'
import { Trash2 } from 'lucide-react'

type Props = {
  reports: ReportListItem[]
  user: User | null
  hideRascunho?: boolean
  onOpen: (reportId: number) => void
  onDelete?: (reportId: number, numero: string) => void
}

function ReportKanbanCard({
  report,
  user,
  onOpen,
  onDelete,
}: {
  report: ReportListItem
  user: User | null
  onOpen: (reportId: number) => void
  onDelete?: (reportId: number, numero: string) => void
}) {
  const ctx = { status: report.status, tecnico_id: report.tecnico_id }
  const canOpen = canViewReport(user, ctx)
  const actionLabel = getReportListActionLabel(user, ctx)
  const showDelete = canDeleteReport(user, ctx)

  return (
    <div className="rounded-md border border-gray-200 bg-white p-3 shadow-sm hover:shadow-md transition-shadow">
      <button
        type="button"
        disabled={!canOpen}
        onClick={() => canOpen && onOpen(report.id)}
        className="w-full text-left disabled:cursor-not-allowed disabled:opacity-60"
        title={canOpen ? actionLabel : undefined}
      >
        <p className="font-semibold text-gray-900 text-sm truncate">{report.numero}</p>
        <p className="text-xs text-gray-600 mt-1 truncate">{report.cliente_nome || 'Cliente N/A'}</p>
        <p className="text-xs text-gray-500 truncate">{report.equipamento_nome || 'Equipamento N/A'}</p>
        <p className="text-xs text-gray-500 mt-2 truncate">{report.tecnico_nome}</p>
        <p className="text-xs text-gray-400 mt-1">
          {new Date(report.created_at).toLocaleDateString('pt-BR')}
        </p>
      </button>
      {showDelete && onDelete && (
        <div className="mt-2 pt-2 border-t border-gray-100 flex justify-end">
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={() => onDelete(report.id, report.numero)}
            title="Excluir"
          >
            <Trash2 className="h-3.5 w-3.5 text-red-500" />
          </Button>
        </div>
      )}
    </div>
  )
}

function KanbanColumn({
  label,
  status,
  reports,
  user,
  onOpen,
  onDelete,
}: {
  label: string
  status: string
  reports: ReportListItem[]
  user: User | null
  onOpen: (reportId: number) => void
  onDelete?: (reportId: number, numero: string) => void
}) {
  const borderClass =
    REPORT_STATUS_COLUMN_BORDER[status as keyof typeof REPORT_STATUS_COLUMN_BORDER] ??
    'border-t-gray-400'

  return (
    <div
      className={`flex w-72 shrink-0 flex-col rounded-lg border border-gray-200 bg-gray-50/80 border-t-4 ${borderClass}`}
    >
      <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-gray-200 bg-white/80 rounded-t-lg">
        <h3 className="text-sm font-semibold text-gray-800 truncate">{label}</h3>
        <span className="text-xs font-medium text-gray-500 bg-gray-100 rounded-full px-2 py-0.5">
          {reports.length}
        </span>
      </div>
      <div className="flex flex-col gap-2 p-2 min-h-[120px] max-h-[calc(100vh-280px)] overflow-y-auto">
        {reports.length === 0 ? (
          <p className="text-xs text-gray-400 text-center py-6 px-2">Nenhum relatório</p>
        ) : (
          reports.map((report) => (
            <ReportKanbanCard
              key={report.id}
              report={report}
              user={user}
              onOpen={onOpen}
              onDelete={onDelete}
            />
          ))
        )}
      </div>
    </div>
  )
}

export function ReportsKanban({ reports, user, hideRascunho, onOpen, onDelete }: Props) {
  const columns = useMemo(
    () => buildReportKanbanColumns(reports, { hideRascunho }),
    [reports, hideRascunho]
  )

  return (
    <div className="overflow-x-auto pb-2">
      <div className="flex items-start gap-4 min-w-min">
        {columns.map((column) => (
          <KanbanColumn
            key={column.status}
            status={column.status}
            label={column.label}
            reports={column.reports}
            user={user}
            onOpen={onOpen}
            onDelete={onDelete}
          />
        ))}
      </div>
    </div>
  )
}

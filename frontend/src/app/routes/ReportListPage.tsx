/**
 * ReportListPage - Lista de Relatórios
 * Sprint 004 - Listagem com filtros
 * #298 - Visão Kanban (read-only)
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@/lib/auth/AuthContext'
import { canCreateReport } from '@/lib/auth/permissions'
import {
  canDeleteReport,
  canViewReport,
  getReportListActionLabel,
  shouldHideElaboracaoStats,
} from '@/lib/reports/reportPermissions'
import { getReportStatusBadgeClass } from '@/lib/reports/reportStatusStyles'
import { reportsApi } from '@/lib/api/reports'
import { ReportListViewToggle } from '@/app/components/reports/ReportListViewToggle'
import { ReportsKanban } from '@/app/components/reports/ReportsKanban'
import { useReportListingPrefs } from '@/hooks/useReportListingPrefs'
import { Button } from '@/components/ui/button'
import { Plus, Edit2, Trash2, FileText } from 'lucide-react'
import { getReportStatusLabel, REPORT_STATUS_LABELS } from '@/lib/reports/statusLabels'
import type { ReportStatus } from '@/lib/reports/statusLabels'

const KANBAN_LIMIT = 100

export default function ReportListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { viewMode, setViewMode } = useReportListingPrefs()

  const [statusFilter, setStatusFilter] = useState<string>('')
  const [page, setPage] = useState(1)

  const hideRascunho = shouldHideElaboracaoStats(user)

  const listQuery = useQuery({
    queryKey: ['reports', 'list', statusFilter, page, user?.id],
    queryFn: () =>
      reportsApi.list({
        status: statusFilter || undefined,
        page,
        limit: 20,
      }),
    enabled: !!user?.id && viewMode === 'list',
  })

  const kanbanQuery = useQuery({
    queryKey: ['reports', 'kanban', user?.id],
    queryFn: () =>
      reportsApi.list({
        page: 1,
        limit: KANBAN_LIMIT,
      }),
    enabled: !!user?.id && viewMode === 'kanban',
  })

  const data = viewMode === 'kanban' ? kanbanQuery.data : listQuery.data
  const isLoading = viewMode === 'kanban' ? kanbanQuery.isLoading : listQuery.isLoading

  const deleteMutation = useMutation({
    mutationFn: reportsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao excluir relatório')
    },
  })

  const handleDelete = (id: number, numero: string) => {
    if (confirm(`Deseja realmente excluir o relatório ${numero}?`)) {
      deleteMutation.mutate(id)
    }
  }

  const openReport = (reportId: number) => {
    navigate(`/relatorios/${reportId}/preencher`)
  }

  if (isLoading) {
    return <div className="p-6 text-center">Carregando...</div>
  }

  const kanbanTruncated =
    viewMode === 'kanban' && data && data.total > KANBAN_LIMIT

  return (
    <div className="p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Relatórios</h1>
          <p className="text-sm text-gray-500 mt-1">
            {data?.total || 0} relatório(s) encontrado(s)
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ReportListViewToggle viewMode={viewMode} onViewModeChange={setViewMode} />
          {canCreateReport(user) && (
            <Button onClick={() => navigate('/novo-relatorio')}>
              <Plus className="h-4 w-4 mr-2" />
              Novo Relatório
            </Button>
          )}
        </div>
      </div>

      {viewMode === 'list' && (
        <div className="mb-4 flex gap-3">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value)
              setPage(1)
            }}
            className="border rounded-md px-3 py-2"
          >
            <option value="">Todos os status</option>
            {(Object.keys(REPORT_STATUS_LABELS) as ReportStatus[])
              .filter((status) => !(hideRascunho && status === 'rascunho'))
              .map((status) => (
                <option key={status} value={status}>
                  {REPORT_STATUS_LABELS[status]}
                </option>
              ))}
          </select>
        </div>
      )}

      {kanbanTruncated && (
        <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          Exibindo os {KANBAN_LIMIT} relatórios mais recentes no kanban. Use a visão Lista para
          ver todos ou filtrar por status.
        </div>
      )}

      {viewMode === 'kanban' ? (
        <ReportsKanban
          reports={data?.reports ?? []}
          user={user}
          hideRascunho={hideRascunho}
          onOpen={openReport}
          onDelete={handleDelete}
        />
      ) : (
        <>
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Número
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Formulário
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Cliente
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Equipamento
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Técnico
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Data
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data?.reports.map((report) => {
                  const ctx = {
                    status: report.status,
                    tecnico_id: report.tecnico_id,
                  }
                  const actionLabel = getReportListActionLabel(user, ctx)
                  const showDelete = canDeleteReport(user, ctx)

                  return (
                    <tr key={report.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {report.numero}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {report.form_template_nome || 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {report.cliente_nome || 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {report.equipamento_nome || 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">{report.tecnico_nome}</td>
                      <td className="px-4 py-3 text-sm">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${getReportStatusBadgeClass(report.status)}`}
                        >
                          {getReportStatusLabel(report.status)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {new Date(report.created_at).toLocaleDateString('pt-BR')}
                      </td>
                      <td className="px-4 py-3 text-sm text-right">
                        <div className="flex gap-2 justify-end">
                          {canViewReport(user, ctx) && (
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => openReport(report.id)}
                              title={actionLabel}
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                          )}
                          {showDelete && (
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleDelete(report.id, report.numero)}
                              title="Excluir"
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>

            {data?.reports.length === 0 && (
              <div className="p-12 text-center text-gray-500">
                <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>Nenhum relatório encontrado</p>
                {canCreateReport(user) && (
                  <Button
                    className="mt-4"
                    variant="outline"
                    onClick={() => navigate('/novo-relatorio')}
                  >
                    Criar Primeiro Relatório
                  </Button>
                )}
              </div>
            )}
          </div>

          {data && data.total > data.limit && (
            <div className="mt-4 flex justify-center gap-2">
              <Button
                variant="outline"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Anterior
              </Button>
              <span className="px-4 py-2">
                Página {page} de {Math.ceil(data.total / data.limit)}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil(data.total / data.limit)}
              >
                Próxima
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

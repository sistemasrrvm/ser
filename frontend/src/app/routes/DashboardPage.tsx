/**
 * Dashboard Page
 */

import { useAuth } from '@/lib/auth/AuthContext'
import { canCreateReport } from '@/lib/auth/permissions'
import {
  filterReportsForDashboard,
  shouldHideElaboracaoStats,
  canEditReport,
} from '@/lib/reports/reportPermissions'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { reportsApi } from '@/lib/api/reports'
import { FileText, Clock, CheckCircle, Calendar, ClipboardEdit, AlertCircle } from 'lucide-react'
import { getReportStatusLabel } from '@/lib/reports/statusLabels'

interface StatCard {
  title: string
  value: number
  icon: React.ReactNode
  color: string
}

function getStatusBadgeClass(status: string): string {
  switch (status) {
    case 'aprovado':
      return 'bg-green-100 text-green-800'
    case 'cancelado':
      return 'bg-red-100 text-red-800'
    case 'em_revisao':
      return 'bg-blue-100 text-blue-800'
    case 'em_correcao':
      return 'bg-orange-100 text-orange-800'
    case 'rascunho':
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('pt-BR')
}

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  // Buscar relatórios recentes (apenas os últimos 5)
  // Incluir user.id na queryKey para evitar cache compartilhado entre usuários
  const { data: reportsData, isLoading: isLoadingReports } = useQuery({
    queryKey: ['reports', 'recent', user?.id],
    queryFn: () =>
      reportsApi.list({
        page: 1,
        limit: 5,
      }),
    enabled: !!user?.id, // Só buscar quando tiver usuário
  })

  // Calcular estatísticas baseadas nos relatórios do usuário
  // Usar o máximo permitido pelo backend (100) para calcular estatísticas
  // Incluir user.id na queryKey para evitar cache compartilhado entre usuários
  const allReportsQuery = useQuery({
    queryKey: ['reports', 'stats', user?.id],
    queryFn: () =>
      reportsApi.list({
        page: 1,
        limit: 100, // Máximo permitido pelo backend
      }),
    enabled: !!user?.id, // Só buscar quando tiver usuário
  })

  const allReportsRaw = allReportsQuery.data?.reports || []
  const allReports = filterReportsForDashboard(user, allReportsRaw)
  const totalReportsFromApi = shouldHideElaboracaoStats(user)
    ? allReports.length
    : allReportsQuery.data?.total || 0
  const recentReports = filterReportsForDashboard(user, reportsData?.reports || [])

  const emElaboracao = allReports.filter((r) => r.status === 'rascunho').length
  const emRevisao = allReports.filter((r) => r.status === 'em_revisao').length
  const emCorrecao = allReports.filter((r) => r.status === 'em_correcao').length
  const aprovados = allReports.filter((r) => r.status === 'aprovado').length

  const currentMonth = new Date().getMonth()
  const currentYear = new Date().getFullYear()
  const esteMes = allReports.filter((r) => {
    const reportDate = new Date(r.created_at)
    return (
      reportDate.getMonth() === currentMonth &&
      reportDate.getFullYear() === currentYear
    )
  }).length

  const stats: StatCard[] = [
    {
      title: 'Total de Relatórios',
      value: totalReportsFromApi,
      icon: <FileText size={24} />,
      color: 'border-blue-500',
    },
    ...(!shouldHideElaboracaoStats(user)
      ? [
          {
            title: 'Em Elaboração',
            value: emElaboracao,
            icon: <ClipboardEdit size={24} />,
            color: 'border-gray-500',
          },
        ]
      : []),
    {
      title: 'Em Revisão',
      value: emRevisao,
      icon: <Clock size={24} />,
      color: 'border-yellow-500',
    },
    {
      title: 'Em Correção',
      value: emCorrecao,
      icon: <AlertCircle size={24} />,
      color: 'border-orange-500',
    },
    {
      title: 'Aprovados',
      value: aprovados,
      icon: <CheckCircle size={24} />,
      color: 'border-green-500',
    },
    {
      title: 'Este Mês',
      value: esteMes,
      icon: <Calendar size={24} />,
      color: 'border-purple-500',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-primary to-primary-hover rounded-lg shadow-lg p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">
          Bem-vindo, {user?.full_name}
        </h1>
        <p className="text-blue-100">
          Sistema de coleta de dados para laudos técnicos industriais
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.title}
            className={`card border-l-4 ${stat.color}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm mb-1">{stat.title}</p>
                <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <div className="text-gray-400">{stat.icon}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Reports */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reports List */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 flex items-center">
                <FileText size={24} className="mr-2" />
                Relatórios Recentes
              </h2>
            </div>

            <div className="space-y-3">
              {isLoadingReports ? (
                <div className="text-center py-4 text-gray-500">
                  Carregando relatórios...
                </div>
              ) : recentReports.length === 0 ? (
                <div className="text-center py-4 text-gray-500">
                  Nenhum relatório encontrado
                </div>
              ) : (
                recentReports.map((report) => {
                  const ctx = {
                    status: report.status,
                    tecnico_id: report.tecnico_id,
                  }
                  const isReadOnly = !canEditReport(user, ctx)
                  return (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                      onClick={() => navigate(`/relatorios/${report.id}/preencher`)}
                    >
                      <div>
                        <p className="font-semibold text-gray-900">
                          {report.numero}
                        </p>
                        <p className="text-sm text-gray-500">
                          Criado em {formatDate(report.created_at)}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(report.status)}`}
                        >
                          {getReportStatusLabel(report.status)}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/relatorios/${report.id}/preencher`)
                          }}
                          className="text-primary hover:text-primary-hover text-sm font-medium"
                        >
                          {isReadOnly ? 'Visualizar' : 'Continuar'}
                        </button>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div>
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Ações Rápidas
            </h2>
            <div className="space-y-2">
              {canCreateReport(user) && (
                <button
                  onClick={() => navigate('/novo-relatorio')}
                  className="btn-primary w-full"
                >
                  + Novo Relatório
                </button>
              )}
              <button
                onClick={() => navigate('/formularios')}
                className="btn-secondary w-full"
              >
                Configurar Templates
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

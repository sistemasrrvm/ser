/**
 * Página: Tipos de Equipamento (tab_tipos_equipamento)
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { Search, RefreshCw, Database, CheckCircle, XCircle } from 'lucide-react'
import { tiposEquipamentoApi } from '@/lib/api/tipos_equipamento'
import { SortableTableHead } from '@/components/ui/SortableTableHead'
import { useTableSort } from '@/hooks/useTableSort'

export default function ManutTiposPage() {
  const [page, setPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const { sortBy, sortDir, toggleSort } = useTableSort('TEQP_NOME', 'asc')
  const pageSize = 50

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['tipos-equipamento', page, searchTerm, sortBy, sortDir],
    queryFn: () =>
      tiposEquipamentoApi.list({
        page,
        page_size: pageSize,
        search: searchTerm || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
      }),
  })

  const { data: syncStatus } = useQuery({
    queryKey: ['tipos-equipamento-status'],
    queryFn: () => tiposEquipamentoApi.getStatus(),
    refetchInterval: 60000,
  })

  const tipos = data?.items ?? []
  const totalPages = data?.total_pages ?? 0

  const handleSort = (column: string) => {
    toggleSort(column)
    setPage(1)
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tipos de Equipamento</h1>
          <p className="text-sm text-gray-500 mt-1">
            Listagem de tipos do sistema NR13 ({data?.total ?? 0} total)
          </p>
        </div>
        <button onClick={() => refetch()} className="btn-secondary flex items-center gap-2">
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      {syncStatus && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-center gap-3">
          <Database size={20} className="text-blue-600" />
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-900">
              {syncStatus.total_registros} tipos em tab_tipos_equipamento
            </p>
            {syncStatus.ultima_sinc && (
              <p className="text-xs text-blue-700">
                Última atualização:{' '}
                {formatDistanceToNow(new Date(syncStatus.ultima_sinc), {
                  addSuffix: true,
                  locale: ptBR,
                })}
              </p>
            )}
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
        <div className="relative">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value)
              setPage(1)
            }}
            placeholder="Nome do tipo de equipamento..."
            className="input pl-10"
          />
        </div>
      </div>

      {isLoading && <div className="text-center py-12 text-gray-500">Carregando...</div>}

      {!isLoading && tipos.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <SortableTableHead label="ID" column="TEQP_ID" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                <SortableTableHead label="Nome" column="TEQP_NOME" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                <SortableTableHead label="Venc. Calibração (dias)" column="TEQP_VENC_CALIBRACAO" activeColumn={sortBy} direction={sortDir} onSort={handleSort} align="center" />
                <SortableTableHead label="Req. Insp. Externa" column="TEQP_REQUER_INSPECAO_EXTERNA" activeColumn={sortBy} direction={sortDir} onSort={handleSort} align="center" />
                <SortableTableHead label="Req. Insp. Interna" column="TEQP_REQUER_INSPECAO_INTERNA" activeColumn={sortBy} direction={sortDir} onSort={handleSort} align="center" />
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tipos.map((tipo) => (
                <tr key={tipo.TEQP_ID} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{tipo.TEQP_ID}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{tipo.TEQP_NOME}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-mono text-gray-500">
                    {tipo.TEQP_VENC_CALIBRACAO ?? '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    {tipo.TEQP_REQUER_INSPECAO_EXTERNA ? (
                      <CheckCircle size={16} className="mx-auto text-green-600" />
                    ) : (
                      <XCircle size={16} className="mx-auto text-gray-400" />
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    {tipo.TEQP_REQUER_INSPECAO_INTERNA ? (
                      <CheckCircle size={16} className="mx-auto text-green-600" />
                    ) : (
                      <XCircle size={16} className="mx-auto text-gray-400" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Página {page} de {totalPages} ({data?.total} tipos)
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary disabled:opacity-50"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="btn-secondary disabled:opacity-50"
                >
                  Próxima
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {!isLoading && tipos.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Database size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum tipo encontrado</h3>
          <p className="text-sm text-gray-500">
            {searchTerm ? 'Tente ajustar os filtros' : 'Nenhum registro em tab_tipos_equipamento'}
          </p>
        </div>
      )}
    </div>
  )
}

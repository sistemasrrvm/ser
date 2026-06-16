/**
 * ClientesPage - Listagem de clientes (tab_clientes - NR13)
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { RefreshCw, Database, Eye } from 'lucide-react'
import { clientesApi } from '@/lib/api/clientes'
import { getApiErrorMessage } from '@/lib/api/client'
import { Nr13SyncButton, type Nr13SyncMode } from '@/app/components/Nr13SyncButton'
import { formatCnpj } from '@/lib/format/cnpj'
import { SortableTableHead } from '@/components/ui/SortableTableHead'
import { useTableSort } from '@/hooks/useTableSort'

export default function ClientesPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [idFilter, setIdFilter] = useState('')
  const [nomeFilter, setNomeFilter] = useState('')
  const [cnpjFilter, setCnpjFilter] = useState('')
  const { sortBy, sortDir, toggleSort } = useTableSort('CLI_NOME', 'asc')
  const pageSize = 50

  const clienteIdParsed =
    idFilter.trim() !== '' && /^\d+$/.test(idFilter.trim())
      ? parseInt(idFilter.trim(), 10)
      : undefined

  const hasActiveFilters = Boolean(idFilter.trim() || nomeFilter.trim() || cnpjFilter.trim())

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['clientes', page, idFilter, nomeFilter, cnpjFilter, sortBy, sortDir],
    queryFn: () =>
      clientesApi.list({
        page,
        page_size: pageSize,
        cliente_id: clienteIdParsed,
        nome: nomeFilter.trim() || undefined,
        cnpj: cnpjFilter.trim() || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
      }),
  })

  const { data: syncStatus } = useQuery({
    queryKey: ['clientes-status'],
    queryFn: () => clientesApi.getStatus(),
    refetchInterval: 60000,
  })

  const clientes = data?.items ?? []
  const totalPages = data?.total_pages ?? 0

  const resetPage = () => setPage(1)

  const handleSort = (column: string) => {
    toggleSort(column)
    setPage(1)
  }

  const syncMutation = useMutation({
    mutationFn: (mode: Nr13SyncMode) =>
      clientesApi.sync({ semFiltroData: mode === 'all' }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
      queryClient.invalidateQueries({ queryKey: ['clientes-status'] })
      const r = result.results
      alert(
        `Sincronização concluída (${result.data_ref}).\n` +
          `Total: ${r.total} | Novos: ${r.inserted} | Atualizados: ${r.updated}` +
          (r.skipped ? `\nIgnorados: ${r.skipped}` : '')
      )
    },
    onError: (error: unknown) => {
      alert(`Erro na sincronização:\n${getApiErrorMessage(error, 'Falha ao sincronizar clientes')}`)
    },
  })

  const daysBack = syncStatus?.nr13_data_ref_days_back ?? 2

  const handleSync = (mode: Nr13SyncMode) => {
    const message =
      mode === 'all'
        ? 'Carregar TODOS os clientes do sistema NR13 (sem filtro de data)? Pode demorar e trazer muitos registros.'
        : `Carregar clientes alterados/incluídos nos últimos ${daysBack} dia(s) (dataRef automática)?`
    if (confirm(message)) {
      syncMutation.mutate(mode)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
          <p className="text-sm text-gray-500 mt-1">
            Listagem de clientes do sistema NR13 ({data?.total ?? 0} total)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Nr13SyncButton
            daysBack={daysBack}
            isPending={syncMutation.isPending}
            onSync={handleSync}
          />
          <button onClick={() => refetch()} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={16} />
            Atualizar
          </button>
        </div>
      </div>

      {syncStatus && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-3">
          <Database size={20} className="text-blue-600" />
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-900">
              {syncStatus.total_registros} clientes em tab_clientes
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

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">ID</label>
            <input
              type="text"
              inputMode="numeric"
              value={idFilter}
              onChange={(e) => {
                setIdFilter(e.target.value)
                resetPage()
              }}
              placeholder="CLI_ID"
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nome</label>
            <input
              type="text"
              value={nomeFilter}
              onChange={(e) => {
                setNomeFilter(e.target.value)
                resetPage()
              }}
              placeholder="Nome do cliente"
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">CNPJ</label>
            <input
              type="text"
              value={cnpjFilter}
              onChange={(e) => {
                setCnpjFilter(e.target.value)
                resetPage()
              }}
              placeholder="CNPJ (com ou sem formatação)"
              className="input"
            />
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="text-center py-12 text-gray-500">Carregando clientes...</div>
      )}

      {!isLoading && clientes.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <SortableTableHead label="ID" column="CLI_ID" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="Nome" column="CLI_NOME" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="CNPJ" column="CLI_CNPJ" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="Site" column="CLI_SITE" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="Cidade" column="CLI_CIDADE" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {clientes.map((cliente) => (
                  <tr key={cliente.CLI_ID} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {cliente.CLI_ID}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                      {cliente.CLI_NOME || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {formatCnpj(cliente.CLI_CNPJ)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={cliente.CLI_SITE || undefined}>
                      {cliente.CLI_SITE ? (
                        <a
                          href={cliente.CLI_SITE.startsWith('http') ? cliente.CLI_SITE : `https://${cliente.CLI_SITE}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {cliente.CLI_SITE}
                        </a>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cliente.CLI_CIDADE || '-'}
                      {cliente.CLI_ESTADO ? ` / ${cliente.CLI_ESTADO}` : ''}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <Link
                        to={`/clientes/${cliente.CLI_ID}`}
                        className="text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
                        title="Ver detalhes e equipamentos"
                      >
                        <Eye size={16} />
                        Ver
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Página {page} de {totalPages} ({data?.total} clientes)
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Próxima
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {!isLoading && clientes.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Database size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum cliente encontrado</h3>
          <p className="text-sm text-gray-500">
            {hasActiveFilters ? 'Tente ajustar os filtros de busca' : 'Nenhum registro em tab_clientes'}
          </p>
        </div>
      )}
    </div>
  )
}

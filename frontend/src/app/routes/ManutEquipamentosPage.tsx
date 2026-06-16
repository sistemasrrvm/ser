/**
 * Página: Equipamentos (tab_equipamentos)
 */

import { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { RefreshCw, Database } from 'lucide-react'
import { equipamentosApi, parseEquipamentosFiltros } from '@/lib/api/equipamentos'
import { getApiErrorMessage } from '@/lib/api/client'
import { Nr13SyncButton, type Nr13SyncMode } from '@/app/components/Nr13SyncButton'
import { SortableTableHead } from '@/components/ui/SortableTableHead'
import { useTableSort } from '@/hooks/useTableSort'

export default function ManutEquipamentosPage() {
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const initialFiltros = parseEquipamentosFiltros(searchParams.get('filtros'))
  const [page, setPage] = useState(1)
  const [idFilter, setIdFilter] = useState(() =>
    initialFiltros?.equipamento_id != null ? String(initialFiltros.equipamento_id) : ''
  )
  const [tagFilter, setTagFilter] = useState(() => initialFiltros?.tag ?? '')
  const [nomeFilter, setNomeFilter] = useState(() => initialFiltros?.nome ?? '')
  const [numeroSerieFilter, setNumeroSerieFilter] = useState(() => initialFiltros?.numero_serie ?? '')
  const [areaFilter, setAreaFilter] = useState(() => initialFiltros?.area ?? '')
  const [clienteNomeFilter, setClienteNomeFilter] = useState(() => initialFiltros?.cliente_nome ?? '')
  const [tipoIdFilter, setTipoIdFilter] = useState(() =>
    initialFiltros?.tipo_equipamento_id != null ? String(initialFiltros.tipo_equipamento_id) : ''
  )
  const [clienteIdFromUrl] = useState(() =>
    String(initialFiltros?.cliente_id ?? searchParams.get('cliente_id') ?? '')
  )
  const { sortBy, sortDir, toggleSort } = useTableSort('EQP_TAG', 'asc')
  const pageSize = 50

  const equipamentoIdParsed =
    idFilter.trim() !== '' && /^\d+$/.test(idFilter.trim())
      ? parseInt(idFilter.trim(), 10)
      : undefined

  const clienteIdFromUrlParsed =
    clienteIdFromUrl.trim() !== '' && /^\d+$/.test(clienteIdFromUrl.trim())
      ? parseInt(clienteIdFromUrl.trim(), 10)
      : undefined

  const tipoIdParsed =
    tipoIdFilter.trim() !== '' && /^\d+$/.test(tipoIdFilter.trim())
      ? parseInt(tipoIdFilter.trim(), 10)
      : undefined

  const hasActiveFilters = Boolean(
    idFilter.trim() ||
      tagFilter.trim() ||
      nomeFilter.trim() ||
      numeroSerieFilter.trim() ||
      areaFilter.trim() ||
      clienteNomeFilter.trim() ||
      tipoIdFilter.trim() ||
      clienteIdFromUrlParsed
  )

  const resetPage = () => setPage(1)

  const { data, isLoading, refetch } = useQuery({
    queryKey: [
      'equipamentos',
      page,
      idFilter,
      tagFilter,
      nomeFilter,
      numeroSerieFilter,
      areaFilter,
      clienteNomeFilter,
      tipoIdFilter,
      clienteIdFromUrlParsed,
      sortBy,
      sortDir,
    ],
    queryFn: () =>
      equipamentosApi.list({
        page,
        page_size: pageSize,
        equipamento_id: equipamentoIdParsed,
        tag: tagFilter.trim() || undefined,
        nome: nomeFilter.trim() || undefined,
        numero_serie: numeroSerieFilter.trim() || undefined,
        area: areaFilter.trim() || undefined,
        cliente_id: clienteIdFromUrlParsed,
        cliente_nome: clienteNomeFilter.trim() || undefined,
        tipo_equipamento_id: tipoIdParsed,
        sort_by: sortBy,
        sort_dir: sortDir,
      }),
  })

  const { data: syncStatus } = useQuery({
    queryKey: ['equipamentos-status'],
    queryFn: () => equipamentosApi.getStatus(),
    refetchInterval: 60000,
  })

  const equipamentos = data?.items ?? []
  const totalPages = data?.total_pages ?? 0

  const handleSort = (column: string) => {
    toggleSort(column)
    setPage(1)
  }

  const syncMutation = useMutation({
    mutationFn: (mode: Nr13SyncMode) =>
      equipamentosApi.sync({ semFiltroData: mode === 'all' }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['equipamentos'] })
      queryClient.invalidateQueries({ queryKey: ['equipamentos-status'] })
      queryClient.invalidateQueries({ queryKey: ['equipamentos-cliente'] })
      const r = result.results
      alert(
        `Sincronização concluída (${result.data_ref}).\n` +
          `Total: ${r.total} | Novos: ${r.inserted} | Atualizados: ${r.updated}` +
          (r.skipped ? `\nIgnorados: ${r.skipped}` : '') +
          (r.message ? `\n${r.message}` : '')
      )
    },
    onError: (error: unknown) => {
      alert(`Erro na sincronização:\n${getApiErrorMessage(error, 'Falha ao sincronizar equipamentos')}`)
    },
  })

  const daysBack = syncStatus?.nr13_data_ref_days_back ?? 2

  const handleSync = (mode: Nr13SyncMode) => {
    const message =
      mode === 'all'
        ? 'Carregar TODOS os equipamentos do sistema NR13 (sem filtro de data)? Pode demorar e trazer muitos registros.'
        : `Carregar equipamentos alterados/incluídos nos últimos ${daysBack} dia(s) (dataRef automática)?`
    if (confirm(message)) {
      syncMutation.mutate(mode)
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Equipamentos</h1>
          <p className="text-sm text-gray-500 mt-1">
            Listagem de equipamentos do sistema NR13 ({data?.total ?? 0} total)
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
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-center gap-3">
          <Database size={20} className="text-blue-600" />
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-900">
              {syncStatus.total_registros} equipamentos em tab_equipamentos
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
              placeholder="EQP_ID"
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">TAG</label>
            <input
              type="text"
              value={tagFilter}
              onChange={(e) => {
                setTagFilter(e.target.value)
                resetPage()
              }}
              placeholder="TAG do equipamento"
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
              placeholder="Nome do equipamento"
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nº Série</label>
            <input
              type="text"
              value={numeroSerieFilter}
              onChange={(e) => {
                setNumeroSerieFilter(e.target.value)
                resetPage()
              }}
              placeholder="Número de série"
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Área</label>
            <input
              type="text"
              value={areaFilter}
              onChange={(e) => {
                setAreaFilter(e.target.value)
                resetPage()
              }}
              placeholder="Área"
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Cliente</label>
            <input
              type="text"
              value={clienteNomeFilter}
              onChange={(e) => {
                setClienteNomeFilter(e.target.value)
                resetPage()
              }}
              placeholder="Nome do cliente"
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo ID</label>
            <input
              type="text"
              inputMode="numeric"
              value={tipoIdFilter}
              onChange={(e) => {
                setTipoIdFilter(e.target.value)
                resetPage()
              }}
              placeholder="EQP_TEQP_ID"
              className="input"
            />
          </div>
        </div>
        {(clienteIdFromUrlParsed || clienteNomeFilter.trim()) && (
          <p className="mt-3 text-xs text-blue-700">
            {clienteIdFromUrlParsed && clienteNomeFilter.trim()
              ? `Filtrando cliente: ${clienteNomeFilter.trim()} (ID ${clienteIdFromUrlParsed})`
              : clienteIdFromUrlParsed
                ? `Filtrando equipamentos do cliente ID ${clienteIdFromUrlParsed}`
                : `Filtrando por cliente: ${clienteNomeFilter.trim()}`}
          </p>
        )}
      </div>

      {isLoading && <div className="text-center py-12 text-gray-500">Carregando...</div>}

      {!isLoading && equipamentos.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <SortableTableHead label="ID" column="EQP_ID" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="TAG" column="EQP_TAG" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="Nome" column="EQP_NOME" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="Nº Série" column="EQP_NUMERO_SERIE" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="Área" column="EQP_AREA" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="Cliente" column="CLI_NOME" activeColumn={sortBy} direction={sortDir} onSort={handleSort} />
                  <SortableTableHead label="Tipo ID" column="EQP_TEQP_ID" activeColumn={sortBy} direction={sortDir} onSort={handleSort} align="center" />
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {equipamentos.map((equip) => (
                  <tr key={equip.EQP_ID} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">{equip.EQP_ID}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">{equip.EQP_TAG}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{equip.EQP_NOME || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{equip.EQP_NUMERO_SERIE || '-'}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{equip.EQP_AREA || '-'}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {equip.CLI_NOME ? (
                        <Link
                          to={`/clientes/${equip.EQP_CLI_ID}`}
                          className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                        >
                          {equip.CLI_NOME}
                        </Link>
                      ) : (
                        '-'
                      )}
                      <span className="block text-xs text-gray-400 font-mono">ID {equip.EQP_CLI_ID}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-mono text-gray-500">{equip.EQP_TEQP_ID ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Página {page} de {totalPages} ({data?.total} equipamentos)
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

      {!isLoading && equipamentos.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Database size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum equipamento encontrado</h3>
          <p className="text-sm text-gray-500">
            {hasActiveFilters ? 'Tente ajustar os filtros' : 'Nenhum registro em tab_equipamentos'}
          </p>
        </div>
      )}
    </div>
  )
}

/**
 * ClienteDetailPage - Detalhes do cliente + equipamentos (tab_clientes / tab_equipamentos)
 */

import { useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Search, Wrench, ExternalLink } from 'lucide-react'
import { clientesApi } from '@/lib/api/clientes'
import { equipamentosApi, buildEquipamentosUrl } from '@/lib/api/equipamentos'
import { getApiErrorMessage } from '@/lib/api/client'
import { Nr13SyncButton, type Nr13SyncMode } from '@/app/components/Nr13SyncButton'
import { formatCnpj } from '@/lib/format/cnpj'
import { SortableTableHead } from '@/components/ui/SortableTableHead'
import { useTableSort } from '@/hooks/useTableSort'

function DetailField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-500 mb-1">{label}</label>
      <p className="text-base text-gray-900">{children}</p>
    </div>
  )
}

export default function ClienteDetailPage() {
  const queryClient = useQueryClient()
  const { clienteId } = useParams<{ clienteId: string }>()
  const parsedId = clienteId ? parseInt(clienteId, 10) : NaN
  const isValidId = Number.isFinite(parsedId) && parsedId > 0

  const [equipPage, setEquipPage] = useState(1)
  const [equipSearch, setEquipSearch] = useState('')
  const { sortBy, sortDir, toggleSort } = useTableSort('EQP_TAG', 'asc')
  const pageSize = 50

  const {
    data: cliente,
    isLoading: loadingCliente,
    error: clienteError,
  } = useQuery({
    queryKey: ['cliente', parsedId],
    queryFn: () => clientesApi.get(parsedId),
    enabled: isValidId,
  })

  const { data: equipamentosData, isLoading: loadingEquipamentos } = useQuery({
    queryKey: ['equipamentos-cliente', parsedId, equipPage, equipSearch, sortBy, sortDir],
    queryFn: () =>
      equipamentosApi.list({
        page: equipPage,
        page_size: pageSize,
        cliente_id: parsedId,
        search: equipSearch || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
      }),
    enabled: isValidId,
  })

  const { data: syncStatus } = useQuery({
    queryKey: ['equipamentos-status'],
    queryFn: () => equipamentosApi.getStatus(),
  })

  const syncMutation = useMutation({
    mutationFn: (mode: Nr13SyncMode) =>
      clientesApi.syncEquipamentos(parsedId, { semFiltroData: mode === 'all' }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['equipamentos-cliente', parsedId] })
      queryClient.invalidateQueries({ queryKey: ['equipamentos'] })
      const r = result.results
      alert(
        `Equipamentos sincronizados (clienteId: ${parsedId}, ${result.data_ref}).\n` +
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

  const handleSyncEquipamentos = (mode: Nr13SyncMode) => {
    const message =
      mode === 'all'
        ? `Carregar TODOS os equipamentos do cliente ${parsedId} na API NR13 (sem dataRef)?`
        : `Carregar equipamentos recentes do cliente ${parsedId} (últimos ${daysBack} dia(s))?`
    if (confirm(message)) {
      syncMutation.mutate(mode)
    }
  }

  const equipamentos = equipamentosData?.items ?? []
  const equipTotalPages = equipamentosData?.total_pages ?? 0

  const handleEquipSort = (column: string) => {
    toggleSort(column)
    setEquipPage(1)
  }

  if (!isValidId) {
    return (
      <div className="p-6">
        <p className="text-gray-600">ID de cliente inválido.</p>
        <Link to="/clientes" className="text-blue-600 hover:underline mt-4 inline-block">
          Voltar para clientes
        </Link>
      </div>
    )
  }

  if (loadingCliente) {
    return <div className="p-6 text-center text-gray-500">Carregando cliente...</div>
  }

  if (clienteError || !cliente) {
    return (
      <div className="p-6">
        <p className="text-gray-600">Cliente não encontrado.</p>
        <Link to="/clientes" className="text-blue-600 hover:underline mt-4 inline-block">
          Voltar para clientes
        </Link>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-8">
      <div>
        <Link
          to="/clientes"
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft size={16} />
          Voltar para clientes
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">{cliente.CLI_NOME || 'Cliente'}</h1>
        <div className="flex flex-wrap items-center gap-3 mt-2">
          <p className="text-sm text-gray-500 font-mono">CLI_ID: {cliente.CLI_ID}</p>
          <Link
            to={buildEquipamentosUrl({
              cliente_id: cliente.CLI_ID,
              cliente_nome: cliente.CLI_NOME ?? undefined,
            })}
            className="btn-primary inline-flex items-center gap-2 text-sm py-1.5 px-3"
          >
            <ExternalLink size={16} />
            Ver equipamentos deste cliente
          </Link>
        </div>
      </div>

      <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Dados do cliente</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <DetailField label="CNPJ">{formatCnpj(cliente.CLI_CNPJ)}</DetailField>
          <DetailField label="Site">{cliente.CLI_SITE || '-'}</DetailField>
          <DetailField label="Contato">{cliente.CLI_CONTATO || '-'}</DetailField>
          <DetailField label="Email">{cliente.CLI_EMAIL || '-'}</DetailField>
          <DetailField label="Telefone">{cliente.CLI_TELEFONE || '-'}</DetailField>
          <DetailField label="CEP">
            <span className="font-mono">{cliente.CLI_CEP || '-'}</span>
          </DetailField>
          <DetailField label="Endereço">
            {[cliente.CLI_ENDERECO, cliente.CLI_NUMERO, cliente.CLI_BAIRRO].filter(Boolean).join(', ') || '-'}
          </DetailField>
          <DetailField label="Cidade / UF">
            {cliente.CLI_CIDADE || '-'}
            {cliente.CLI_ESTADO ? ` / ${cliente.CLI_ESTADO}` : ''}
          </DetailField>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <Wrench size={20} className="text-[#56991f]" />
            <h2 className="text-lg font-semibold text-gray-900">
              Equipamentos ({equipamentosData?.total ?? 0})
            </h2>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Nr13SyncButton
              daysBack={daysBack}
              isPending={syncMutation.isPending}
              onSync={handleSyncEquipamentos}
            />
            <Link
              to={buildEquipamentosUrl({
                cliente_id: cliente.CLI_ID,
                cliente_nome: cliente.CLI_NOME ?? undefined,
              })}
              className="btn-secondary inline-flex items-center gap-2 text-sm"
            >
              <ExternalLink size={16} />
              Abrir listagem completa
            </Link>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Buscar equipamento</label>
          <div className="relative max-w-md">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={equipSearch}
              onChange={(e) => {
                setEquipSearch(e.target.value)
                setEquipPage(1)
              }}
              placeholder="TAG, nome ou número de série..."
              className="input pl-10"
            />
          </div>
        </div>

        {loadingEquipamentos && (
          <div className="text-center py-8 text-gray-500">Carregando equipamentos...</div>
        )}

        {!loadingEquipamentos && equipamentos.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <SortableTableHead label="ID" column="EQP_ID" activeColumn={sortBy} direction={sortDir} onSort={handleEquipSort} />
                    <SortableTableHead label="TAG" column="EQP_TAG" activeColumn={sortBy} direction={sortDir} onSort={handleEquipSort} />
                    <SortableTableHead label="Nome" column="EQP_NOME" activeColumn={sortBy} direction={sortDir} onSort={handleEquipSort} />
                    <SortableTableHead label="Nº Série" column="EQP_NUMERO_SERIE" activeColumn={sortBy} direction={sortDir} onSort={handleEquipSort} />
                    <SortableTableHead label="Área" column="EQP_AREA" activeColumn={sortBy} direction={sortDir} onSort={handleEquipSort} />
                    <SortableTableHead label="Tipo ID" column="EQP_TEQP_ID" activeColumn={sortBy} direction={sortDir} onSort={handleEquipSort} align="center" />
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
                      <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-mono text-gray-500">
                        {equip.EQP_TEQP_ID ?? '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {equipTotalPages > 1 && (
              <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Página {equipPage} de {equipTotalPages}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setEquipPage((p) => Math.max(1, p - 1))}
                    disabled={equipPage === 1}
                    className="btn-secondary disabled:opacity-50"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setEquipPage((p) => Math.min(equipTotalPages, p + 1))}
                    disabled={equipPage === equipTotalPages}
                    className="btn-secondary disabled:opacity-50"
                  >
                    Próxima
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {!loadingEquipamentos && equipamentos.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <Wrench size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum equipamento</h3>
            <p className="text-sm text-gray-500">
              {equipSearch
                ? 'Nenhum equipamento encontrado com os filtros informados'
                : 'Este cliente não possui equipamentos cadastrados'}
            </p>
          </div>
        )}
      </section>
    </div>
  )
}

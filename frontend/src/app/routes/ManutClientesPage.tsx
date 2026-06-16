/**
 * Página: Clientes NR13
 * Lista clientes do sistema NR13 (cache SQL Server)
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { manutApi, type ManutCliente } from '@/lib/api/manut'
import { formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { Search, RefreshCw, Database, Eye, X } from 'lucide-react'

export default function ManutClientesPage() {
  const [page, setPage] = useState(1)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCliente, setSelectedCliente] = useState<ManutCliente | null>(null)
  const pageSize = 50

  // Query para listar clientes
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['manut-clientes', page, searchTerm],
    queryFn: () =>
      manutApi.listClientes({
        page,
        page_size: pageSize,
        search: searchTerm || undefined,
      }),
  })

  // Query para status de sincronização
  const { data: syncStatus } = useQuery({
    queryKey: ['manut-clientes-status'],
    queryFn: () => manutApi.getClientesStatus(),
    refetchInterval: 60000, // Atualizar a cada 1 minuto
  })

  const clientes = data?.items || []
  const totalPages = data?.total_pages || 0

  const handleSearch = (value: string) => {
    setSearchTerm(value)
    setPage(1) // Reset para primeira página ao buscar
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Clientes NR13</h1>
          <p className="text-sm text-gray-500 mt-1">
            Dados sincronizados do sistema NR13 (somente leitura)
          </p>
        </div>

        <button
          onClick={() => refetch()}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw size={16} />
          Atualizar
        </button>
      </div>

      {/* Status de Sincronização */}
      {syncStatus && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-center gap-3">
          <Database size={20} className="text-blue-600" />
          <div className="flex-1">
            <p className="text-sm font-medium text-blue-900">
              {syncStatus.total_registros} clientes em cache
            </p>
            {syncStatus.ultima_sinc && (
              <p className="text-xs text-blue-700">
                Última sincronização:{' '}
                {formatDistanceToNow(new Date(syncStatus.ultima_sinc), {
                  addSuffix: true,
                  locale: ptBR,
                })}
              </p>
            )}
            {!syncStatus.ultima_sinc && (
              <p className="text-xs text-blue-700">Nunca sincronizado</p>
            )}
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Buscar
          </label>
          <div className="relative">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Nome ou CNPJ..."
              className="input pl-10"
            />
          </div>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="text-center py-12 text-gray-500">
          Carregando clientes...
        </div>
      )}

      {/* Tabela */}
      {!isLoading && clientes.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nome
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    CNPJ
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contato
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Telefone
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {clientes.map((cliente: ManutCliente) => (
                  <tr key={cliente.CLI_ID} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {cliente.CLI_ID}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {cliente.CLI_NOME}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cliente.CLI_CNPJ || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cliente.CLI_CONTATO || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cliente.CLI_TELEFONE || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <button
                        onClick={() => setSelectedCliente(cliente)}
                        className="text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
                        title="Ver detalhes"
                      >
                        <Eye size={16} />
                        Ver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Paginação */}
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

      {/* Empty State */}
      {!isLoading && clientes.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Database size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Nenhum cliente encontrado
          </h3>
          <p className="text-sm text-gray-500">
            {searchTerm
              ? 'Tente ajustar os filtros de busca'
              : 'Aguardando sincronização com SQL Server'}
          </p>
        </div>
      )}

      {/* Modal Ver Cliente */}
      {selectedCliente && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between sticky top-0 bg-white">
              <h2 className="text-xl font-bold text-gray-900">Detalhes do Cliente</h2>
              <button
                onClick={() => setSelectedCliente(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Conteúdo */}
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Informações Básicas */}
                <div className="col-span-2 border-b pb-4">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
                    Informações Básicas
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        ID
                      </label>
                      <p className="text-base text-gray-900 font-mono">{selectedCliente.CLI_ID}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Nome
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_NOME || '-'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        CNPJ
                      </label>
                      <p className="text-base text-gray-900 font-mono">{selectedCliente.CLI_CNPJ || '-'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Site
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_SITE || '-'}</p>
                    </div>
                  </div>
                </div>

                {/* Contato */}
                <div className="col-span-2 border-b pb-4">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
                    Contato
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Contato
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_CONTATO || '-'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Email
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_EMAIL || '-'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Telefone
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_TELEFONE || '-'}</p>
                    </div>
                  </div>
                </div>

                {/* Endereço */}
                <div className="col-span-2 border-b pb-4">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
                    Endereço
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="md:col-span-3">
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Logradouro
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_ENDERECO || '-'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Número
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_NUMERO || '-'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Bairro
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_BAIRRO || '-'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        CEP
                      </label>
                      <p className="text-base text-gray-900 font-mono">{selectedCliente.CLI_CEP || '-'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Cidade
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_CIDADE || '-'}</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Estado
                      </label>
                      <p className="text-base text-gray-900">{selectedCliente.CLI_ESTADO || '-'}</p>
                    </div>
                  </div>
                </div>

                {/* Datas */}
                <div className="col-span-2">
                  <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
                    Informações de Sistema
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Data de Inserção
                      </label>
                      <p className="text-base text-gray-900">
                        {selectedCliente.CLI_DT_INS
                          ? new Date(selectedCliente.CLI_DT_INS).toLocaleString('pt-BR')
                          : '-'}
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-500 mb-1">
                        Data de Atualização
                      </label>
                      <p className="text-base text-gray-900">
                        {selectedCliente.CLI_DT_UPD
                          ? new Date(selectedCliente.CLI_DT_UPD).toLocaleString('pt-BR')
                          : '-'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
              <button
                onClick={() => setSelectedCliente(null)}
                className="btn-secondary"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

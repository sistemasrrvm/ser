/**
 * Configurações Page - CRUD de Configurações do Sistema
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Edit2, Search, X, Settings, Link2, Mail } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { configuracoesApi, type Configuracao, type ConfiguracaoCreate } from '@/lib/api/configuracoes'
import { Nr13IntegracaoPanel } from '@/app/components/Nr13IntegracaoPanel'
import { EmailIntegracaoPanel } from '@/app/components/EmailIntegracaoPanel'
import { EmailTestPanel } from '@/app/components/EmailTestPanel'

export default function ConfiguracoesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [categoriaFilter, setCategoriaFilter] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingConfig, setEditingConfig] = useState<Configuracao | null>(null)
  const [formData, setFormData] = useState<ConfiguracaoCreate>({
    chave: '',
    valor: '',
    tipo: 'texto',
    descricao: '',
    categoria: 'geral',
  })

  const queryClient = useQueryClient()

  // Query para listar configurações
  const { data, isLoading, error } = useQuery({
    queryKey: ['configuracoes', categoriaFilter],
    queryFn: () => configuracoesApi.list(categoriaFilter || undefined),
  })

  // Mutation para criar configuração
  const createMutation = useMutation({
    mutationFn: (data: ConfiguracaoCreate) => configuracoesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configuracoes'] })
      setIsModalOpen(false)
      resetForm()
      alert('Configuração criada com sucesso!')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao criar configuração')
    },
  })

  // Mutation para atualizar configuração
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      configuracoesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configuracoes'] })
      setIsModalOpen(false)
      resetForm()
      alert('Configuração atualizada com sucesso!')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao atualizar configuração')
    },
  })

  // Mutation para excluir configuração
  const deleteMutation = useMutation({
    mutationFn: (id: number) => configuracoesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configuracoes'] })
      alert('Configuração excluída com sucesso!')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao excluir configuração')
    },
  })

  const resetForm = () => {
    setFormData({ chave: '', valor: '', tipo: 'texto', descricao: '', categoria: 'geral' })
    setEditingConfig(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validação
    if (!formData.chave) {
      alert('Chave é obrigatória')
      return
    }

    if (editingConfig) {
      const { chave, ...updateData } = formData
      updateMutation.mutate({ id: editingConfig.id, data: updateData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (config: Configuracao) => {
    setEditingConfig(config)
    setFormData({
      chave: config.chave,
      valor: config.valor || '',
      tipo: config.tipo,
      descricao: config.descricao || '',
      categoria: config.categoria,
    })
    setIsModalOpen(true)
  }

  const handleDelete = (id: number, chave: string) => {
    if (confirm(`Excluir configuração "${chave}"?`)) {
      deleteMutation.mutate(id)
    }
  }

  const handleOpenNew = () => {
    resetForm()
    setIsModalOpen(true)
  }

  // Filtrar configurações por termo de busca
  const filteredConfigs = data?.configuracoes?.filter((config) => {
    if (config.chave === 'nr13_integracao' || config.chave === 'email_integracao') return false
    const searchLower = searchTerm.toLowerCase()
    return (
      config.chave.toLowerCase().includes(searchLower) ||
      config.categoria.toLowerCase().includes(searchLower) ||
      (config.descricao || '').toLowerCase().includes(searchLower)
    )
  })

  // Obter categorias únicas
  const categorias = Array.from(new Set(data?.configuracoes?.map((c) => c.categoria) || []))

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Settings className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Configurações do Sistema</h1>
          <p className="text-gray-600">Gerenciar integrações e parâmetros globais da aplicação</p>
        </div>
      </div>

      <Tabs defaultValue="nr13" className="w-full">
        <TabsList className="mb-4 flex flex-wrap h-auto gap-1">
          <TabsTrigger value="nr13" className="gap-2">
            <Link2 className="w-4 h-4" />
            Integração NR13
          </TabsTrigger>
          <TabsTrigger value="email" className="gap-2">
            <Mail className="w-4 h-4" />
            E-mail
          </TabsTrigger>
          <TabsTrigger value="geral" className="gap-2">
            <Settings className="w-4 h-4" />
            Configurações gerais
          </TabsTrigger>
        </TabsList>

        <TabsContent value="nr13" className="mt-0">
          <Nr13IntegracaoPanel />
        </TabsContent>

        <TabsContent value="email" className="mt-0 space-y-0">
          <EmailIntegracaoPanel />
          <EmailTestPanel />
        </TabsContent>

        <TabsContent value="geral" className="mt-0">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-600">
              Chaves de configuração avançadas (exceto integrações gerenciadas nas outras abas)
            </p>
            <button
              onClick={handleOpenNew}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shrink-0"
            >
              <Plus className="w-4 h-4" />
              Nova Configuração
            </button>
          </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Busca */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Buscar por chave, categoria ou descrição..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filtro por Categoria */}
          <div>
            <select
              value={categoriaFilter}
              onChange={(e) => setCategoriaFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Todas as Categorias</option>
              {categorias.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Loading & Error */}
      {isLoading && (
        <div className="text-center py-8 text-gray-600">Carregando configurações...</div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          Erro ao carregar configurações
        </div>
      )}

      {/* Lista de Configurações */}
      {!isLoading && !error && (
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Chave
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Valor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Categoria
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Descrição
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredConfigs?.map((config) => (
                <tr key={config.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{config.chave}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 max-w-xs truncate">
                      {config.tipo === 'json' ? (
                        <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                          {config.valor?.substring(0, 50)}...
                        </code>
                      ) : (
                        config.valor || '-'
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        config.tipo === 'json'
                          ? 'bg-purple-100 text-purple-800'
                          : config.tipo === 'numero'
                          ? 'bg-blue-100 text-blue-800'
                          : config.tipo === 'boolean'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {config.tipo}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                      {config.categoria}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-500 max-w-xs truncate">
                      {config.descricao || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleEdit(config)}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                      title="Editar"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(config.id, config.chave)}
                      className="text-red-600 hover:text-red-900"
                      title="Excluir"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredConfigs?.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    Nenhuma configuração encontrada
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
        </TabsContent>
      </Tabs>

      {/* Modal de Criar/Editar */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-800">
                {editingConfig ? 'Editar Configuração' : 'Nova Configuração'}
              </h2>
              <button
                onClick={() => {
                  setIsModalOpen(false)
                  resetForm()
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Chave */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Chave *
                </label>
                <input
                  type="text"
                  value={formData.chave}
                  onChange={(e) => setFormData({ ...formData, chave: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="ex: smtp_host"
                  disabled={!!editingConfig}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Apenas letras minúsculas, números, underscore e hífen
                </p>
              </div>

              {/* Valor */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Valor</label>
                <textarea
                  value={formData.valor || ''}
                  onChange={(e) => setFormData({ ...formData, valor: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={formData.tipo === 'json' ? 6 : 3}
                  placeholder={
                    formData.tipo === 'json'
                      ? '{"chave": "valor"}'
                      : 'Valor da configuração'
                  }
                />
              </div>

              {/* Tipo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo *</label>
                <select
                  value={formData.tipo}
                  onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  <option value="texto">Texto</option>
                  <option value="numero">Número</option>
                  <option value="json">JSON</option>
                  <option value="boolean">Boolean</option>
                </select>
              </div>

              {/* Categoria */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Categoria *
                </label>
                <input
                  type="text"
                  value={formData.categoria}
                  onChange={(e) => setFormData({ ...formData, categoria: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="ex: email, sistema, integracao"
                  required
                />
              </div>

              {/* Descrição */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição
                </label>
                <input
                  type="text"
                  value={formData.descricao || ''}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Descrição da configuração"
                />
              </div>

              {/* Ações */}
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition font-medium"
                >
                  {editingConfig ? 'Atualizar' : 'Criar'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsModalOpen(false)
                    resetForm()
                  }}
                  className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition font-medium"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

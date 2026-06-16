/**
 * Listas Lookup Page - CRUD de Listas de Opções
 */

import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { lookupListsApi, type LookupList, type LookupListCreate } from '@/lib/api/lookupLists'
import { Plus, Trash2, Edit2, Search, RefreshCw, X, Download, Upload, AlertTriangle, FileSpreadsheet } from 'lucide-react'
import * as XLSX from 'xlsx'

interface OptionForm {
  id: string
  label: string
  filter?: string
}

export default function LookupListsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingList, setEditingList] = useState<LookupList | null>(null)
  const [formData, setFormData] = useState<LookupListCreate>({
    id: '',
    nome: '',
    descricao: '',
    opcoes: [],
  })
  const [newOption, setNewOption] = useState<OptionForm>({
    id: '',
    label: '',
    filter: '',
  })
  const [optionFilter, setOptionFilter] = useState('')

  // Estados para importação
  const [showImportModal, setShowImportModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [confirmationText, setConfirmationText] = useState('')
  const [isImporting, setIsImporting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const excelInputRef = useRef<HTMLInputElement>(null)

  const isConfirmationValid = confirmationText.toUpperCase() === 'EXCLUIR TUDO'

  const queryClient = useQueryClient()

  // Query para listar listas
  const { data, isLoading, error } = useQuery({
    queryKey: ['lookup-lists'],
    queryFn: () => lookupListsApi.list(),
  })

  // Mutation para criar lista
  const createMutation = useMutation({
    mutationFn: (data: LookupListCreate) => lookupListsApi.create(data),
    onSuccess: (lista) => {
      queryClient.invalidateQueries({ queryKey: ['lookup-lists'] })
      // Invalidar cache das opções desta lista
      queryClient.invalidateQueries({ queryKey: ['lookup-options', lista.id] })
      setIsModalOpen(false)
      resetForm()
      alert('Lista criada com sucesso!')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao criar lista')
    },
  })

  // Mutation para atualizar lista
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      lookupListsApi.update(id, data),
    onSuccess: (lista, variables) => {
      queryClient.invalidateQueries({ queryKey: ['lookup-lists'] })
      // Invalidar cache das opções desta lista
      queryClient.invalidateQueries({ queryKey: ['lookup-options', variables.id] })
      setIsModalOpen(false)
      resetForm()
      alert('Lista atualizada com sucesso!')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao atualizar lista')
    },
  })

  // Mutation para excluir lista
  const deleteMutation = useMutation({
    mutationFn: (id: string) => lookupListsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lookup-lists'] })
      alert('Lista excluída com sucesso!')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao excluir lista')
    },
  })

  // Mutation para refresh (API externa)
  const refreshMutation = useMutation({
    mutationFn: (id: string) => lookupListsApi.refresh(id),
    onSuccess: (lista, id) => {
      queryClient.invalidateQueries({ queryKey: ['lookup-lists'] })
      // Invalidar cache das opções desta lista
      queryClient.invalidateQueries({ queryKey: ['lookup-options', id] })
      alert('Lista atualizada via API externa!')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao atualizar lista')
    },
  })

  const resetForm = () => {
    setFormData({ id: '', nome: '', descricao: '', opcoes: [] })
    setEditingList(null)
    setNewOption({ id: '', label: '', filter: '' })
    setOptionFilter('')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validação
    if (!formData.id || !formData.nome) {
      alert('ID e Nome são obrigatórios')
      return
    }

    // REMOVIDO: validação que exigia pelo menos uma opção
    // Agora permite salvar lista vazia para continuar no futuro

    if (editingList) {
      // Ao editar, não envia o ID (não pode ser alterado)
      const { id, ...updateData } = formData
      updateMutation.mutate({ id: editingList.id, data: updateData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (lista: LookupList) => {
    setEditingList(lista)
    setFormData({
      id: lista.id,
      nome: lista.nome,
      descricao: lista.descricao || '',
      opcoes: lista.opcoes,
      config_api: lista.config_api,
    })
    setIsModalOpen(true)
  }

  const handleDelete = (id: string, nome: string) => {
    if (confirm(`Deseja realmente excluir a lista "${nome}"?`)) {
      deleteMutation.mutate(id)
    }
  }

  const handleRefresh = (id: string, nome: string) => {
    if (confirm(`Deseja atualizar a lista "${nome}" via API externa?`)) {
      refreshMutation.mutate(id)
    }
  }

  const handleAddOption = () => {
    if (!newOption.id || !newOption.label) {
      alert('ID e Label da opção são obrigatórios')
      return
    }

    // Verificar duplicidade
    if (formData.opcoes.some((opt) => opt.id === newOption.id)) {
      alert('Já existe uma opção com este ID')
      return
    }

    const option: any = {
      id: newOption.id,
      label: newOption.label,
    }

    if (newOption.filter) {
      option.filter = newOption.filter
    }

    setFormData({
      ...formData,
      opcoes: [...formData.opcoes, option],
    })

    setNewOption({ id: '', label: '', filter: '' })
  }

  const handleRemoveOption = (optionId: string) => {
    setFormData({
      ...formData,
      opcoes: formData.opcoes.filter((opt) => opt.id !== optionId),
    })
  }

  // Handler para exportar lista (download JSON)
  const handleExportList = (lista: LookupList) => {
    try {
      // Criar objeto de exportação
      const exportData = {
        id: lista.id,
        nome: lista.nome,
        descricao: lista.descricao,
        opcoes: lista.opcoes,
        config_api: lista.config_api,
        exportado_em: new Date().toISOString(),
      }

      // Criar blob e fazer download
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json',
      })

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `lookup-list-${lista.id}-${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      alert('Lista exportada com sucesso!')
    } catch (error: any) {
      console.error('Erro ao exportar lista:', error)
      alert('Erro ao exportar lista: ' + (error?.message || 'Erro desconhecido'))
    }
  }

  // Handler para selecionar arquivo de importação
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validar extensão
    if (!file.name.endsWith('.json')) {
      alert('Arquivo deve ser do tipo .json')
      return
    }

    setSelectedFile(file)
    setShowImportModal(true)
  }

  // Handler para confirmar importação (DANGER ZONE)
  const handleConfirmImport = async () => {
    if (!selectedFile || !isConfirmationValid) return

    // Primeira confirmação
    if (
      !confirm(
        `🚨 CONFIRMAÇÃO FINAL - DANGER ZONE 🚨\n\n` +
          `Esta ação vai EXCLUIR PERMANENTEMENTE:\n` +
          `- Todas as opções existentes nesta lista\n` +
          `- Campos configurados podem ficar INCONSISTENTES\n\n` +
          `E SUBSTITUIR pelo conteúdo do arquivo JSON.\n\n` +
          `Esta ação NÃO PODE SER DESFEITA!\n\n` +
          `Deseja realmente continuar?`
      )
    ) {
      return
    }

    // Segunda confirmação (última chance)
    if (
      !confirm(
        `⚠️ ÚLTIMA CONFIRMAÇÃO ⚠️\n\n` +
          `Você tem CERTEZA ABSOLUTA que deseja excluir tudo e importar?\n\n` +
          `Confirma a exclusão total e importação da nova configuração?`
      )
    ) {
      return
    }

    try {
      setIsImporting(true)

      // Ler arquivo JSON
      const text = await selectedFile.text()
      const importData = JSON.parse(text)

      // Validar estrutura básica
      if (!importData.id || !importData.nome) {
        throw new Error('Arquivo JSON inválido: faltam campos obrigatórios (id, nome)')
      }

      // Preparar dados para atualização
      const updateData: any = {
        nome: importData.nome,
        descricao: importData.descricao || '',
        opcoes: importData.opcoes || [],
        config_api: importData.config_api,
      }

      // Atualizar lista (usando ID do arquivo JSON)
      await lookupListsApi.update(importData.id, updateData)

      // Atualizar cache
      queryClient.invalidateQueries({ queryKey: ['lookup-lists'] })

      alert(`Lista "${importData.nome}" importada e substituída com sucesso!`)

      // Fechar modal e resetar
      setShowImportModal(false)
      setSelectedFile(null)
      setConfirmationText('')

      // Recarregar página
      window.location.reload()
    } catch (error: any) {
      console.error('Erro ao importar lista:', error)
      alert('Erro ao importar lista: ' + (error?.message || 'Erro desconhecido'))
    } finally {
      setIsImporting(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleCancelImport = () => {
    setShowImportModal(false)
    setSelectedFile(null)
    setConfirmationText('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Handler para exportar opções como Excel
  const handleExportExcel = () => {
    try {
      if (formData.opcoes.length === 0) {
        alert('Não há opções para exportar')
        return
      }

      // Preparar dados para Excel
      const excelData = formData.opcoes.map((opt) => ({
        ID: opt.id,
        Label: opt.label,
        Filter: opt.filter || '',
      }))

      // Criar worksheet
      const ws = XLSX.utils.json_to_sheet(excelData)

      // Criar workbook
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, 'Opções')

      // Salvar arquivo
      const fileName = `lookup-${formData.id || 'lista'}-${Date.now()}.xlsx`
      XLSX.writeFile(wb, fileName)

      alert('Excel exportado com sucesso!')
    } catch (error: any) {
      console.error('Erro ao exportar Excel:', error)
      alert('Erro ao exportar Excel: ' + (error?.message || 'Erro desconhecido'))
    }
  }

  // Handler para importar opções de Excel
  const handleImportExcel = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validar extensão
    if (!file.name.match(/\.(xlsx|xls)$/)) {
      alert('Arquivo deve ser do tipo Excel (.xlsx ou .xls)')
      if (excelInputRef.current) {
        excelInputRef.current.value = ''
      }
      return
    }

    const reader = new FileReader()

    reader.onload = (event) => {
      try {
        const data = event.target?.result
        if (!data) throw new Error('Erro ao ler arquivo')

        // Ler Excel
        const workbook = XLSX.read(data, { type: 'binary' })

        // Pegar primeira planilha
        const firstSheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[firstSheetName]

        // Converter para JSON
        const jsonData = XLSX.utils.sheet_to_json(worksheet)

        if (jsonData.length === 0) {
          throw new Error('Planilha está vazia')
        }

        // Validar e mapear dados
        const importedOptions: any[] = []
        const errors: string[] = []

        jsonData.forEach((row: any, index) => {
          const rowNum = index + 2 // Excel começa em 1, header é linha 1

          // Validar campos obrigatórios
          if (!row.ID || !row.Label) {
            errors.push(`Linha ${rowNum}: ID e Label são obrigatórios`)
            return
          }

          // Verificar duplicidade
          if (importedOptions.some((opt) => opt.id === row.ID)) {
            errors.push(`Linha ${rowNum}: ID "${row.ID}" duplicado`)
            return
          }

          const option: any = {
            id: String(row.ID).trim(),
            label: String(row.Label).trim(),
          }

          if (row.Filter && String(row.Filter).trim()) {
            option.filter = String(row.Filter).trim()
          }

          importedOptions.push(option)
        })

        // Se houver erros, mostrar e não importar
        if (errors.length > 0) {
          alert('Erros encontrados no Excel:\n\n' + errors.join('\n'))
          if (excelInputRef.current) {
            excelInputRef.current.value = ''
          }
          return
        }

        // Confirmar importação
        if (
          !confirm(
            `Importar ${importedOptions.length} opções do Excel?\n\n` +
              `ATENÇÃO: Isto vai SUBSTITUIR todas as opções atuais (${formData.opcoes.length} opções).\n\n` +
              `Deseja continuar?`
          )
        ) {
          if (excelInputRef.current) {
            excelInputRef.current.value = ''
          }
          return
        }

        // Atualizar formData com opções importadas
        setFormData({
          ...formData,
          opcoes: importedOptions,
        })

        // Limpar filtro para mostrar todas as opções importadas
        setOptionFilter('')

        alert(`${importedOptions.length} opções importadas com sucesso!`)

        // Limpar input
        if (excelInputRef.current) {
          excelInputRef.current.value = ''
        }
      } catch (error: any) {
        console.error('Erro ao importar Excel:', error)
        alert('Erro ao importar Excel: ' + (error?.message || 'Erro desconhecido'))
        if (excelInputRef.current) {
          excelInputRef.current.value = ''
        }
      }
    }

    reader.onerror = () => {
      alert('Erro ao ler arquivo')
      if (excelInputRef.current) {
        excelInputRef.current.value = ''
      }
    }

    reader.readAsBinaryString(file)
  }

  const filteredListas = data?.listas.filter((l) =>
    l.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Listas Lookup</h1>
          <p className="text-gray-500 mt-1">
            Gerencie as listas de opções usadas nos campos Lookup
          </p>
        </div>
        <div className="flex gap-2">
          {/* Input file oculto */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            className="hidden"
            onChange={handleFileSelect}
          />

          {/* Botão Importar Lista (DANGER ZONE) */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isImporting}
            className="btn-secondary border-red-500 text-red-700 hover:bg-red-50 flex items-center"
          >
            <Upload size={20} className="mr-2" />
            {isImporting ? 'Importando...' : 'Importar Lista'}
          </button>

          {/* Botão Nova Lista */}
          <button
            onClick={() => {
              resetForm()
              setIsModalOpen(true)
            }}
            className="btn-primary flex items-center"
          >
            <Plus size={20} className="mr-2" />
            Nova Lista
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="card">
        <div className="relative">
          <Search
            size={20}
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            placeholder="Buscar listas por ID ou nome..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      {/* List */}
      <div className="card">
        {isLoading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-2 text-gray-600">Carregando listas...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-8 text-red-600">
            Erro ao carregar listas. Tente novamente.
          </div>
        )}

        {filteredListas && filteredListas.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Nenhuma lista encontrada.
          </div>
        )}

        {filteredListas && filteredListas.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    ID
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Nome
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Descrição
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">
                    Opções
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">
                    API
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredListas.map((lista) => (
                  <tr
                    key={lista.id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4 font-mono text-sm text-gray-600">
                      {lista.id}
                    </td>
                    <td className="py-3 px-4 font-medium text-gray-900">
                      {lista.nome}
                    </td>
                    <td className="py-3 px-4 text-gray-600">
                      {lista.descricao || '-'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {lista.opcoes.length} opções
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {lista.config_api ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          API
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      {lista.config_api && (
                        <button
                          onClick={() => handleRefresh(lista.id, lista.nome)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Atualizar via API"
                          disabled={refreshMutation.isPending}
                        >
                          <RefreshCw size={18} className={refreshMutation.isPending ? 'animate-spin' : ''} />
                        </button>
                      )}
                      <button
                        onClick={() => handleExportList(lista)}
                        className="text-green-600 hover:text-green-800"
                        title="Exportar"
                      >
                        <Download size={18} />
                      </button>
                      <button
                        onClick={() => handleEdit(lista)}
                        className="text-yellow-600 hover:text-yellow-800"
                        title="Editar"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleDelete(lista.id, lista.nome)}
                        className="text-red-600 hover:text-red-800"
                        title="Excluir"
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Criar/Editar */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">
                {editingList ? `Editar Lista: ${editingList.nome}` : 'Nova Lista Lookup'}
              </h2>
              <button
                onClick={() => {
                  setIsModalOpen(false)
                  resetForm()
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* ID e Nome */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ID (identificador único) *
                  </label>
                  <input
                    type="text"
                    value={formData.id}
                    onChange={(e) =>
                      setFormData({ ...formData, id: e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, '') })
                    }
                    placeholder="ex: estados_brasil"
                    className="input"
                    required
                    disabled={!!editingList}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Apenas letras minúsculas, números, - e _
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome *
                  </label>
                  <input
                    type="text"
                    value={formData.nome}
                    onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                    placeholder="ex: Estados do Brasil"
                    className="input"
                    required
                  />
                </div>
              </div>

              {/* Descrição */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descrição
                </label>
                <textarea
                  value={formData.descricao}
                  onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                  placeholder="Descrição da lista"
                  className="input"
                  rows={2}
                />
              </div>

              {/* Opções */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-700">
                    Opções {formData.opcoes.length === 0 && <span className="text-gray-500 text-xs font-normal">(pode salvar vazia e continuar depois)</span>}
                  </label>

                  {/* Botões Importar/Exportar Excel */}
                  <div className="flex gap-2">
                    {/* Input file oculto para Excel */}
                    <input
                      ref={excelInputRef}
                      type="file"
                      accept=".xlsx,.xls"
                      className="hidden"
                      onChange={handleImportExcel}
                    />

                    <button
                      type="button"
                      onClick={() => excelInputRef.current?.click()}
                      className="btn-secondary text-xs flex items-center"
                      title="Importar opções de planilha Excel"
                    >
                      <Upload size={14} className="mr-1" />
                      Importar Excel
                    </button>

                    <button
                      type="button"
                      onClick={handleExportExcel}
                      disabled={formData.opcoes.length === 0}
                      className="btn-secondary text-xs flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Exportar opções para planilha Excel"
                    >
                      <FileSpreadsheet size={14} className="mr-1" />
                      Exportar Excel
                    </button>
                  </div>
                </div>

                {/* Lista de opções */}
                {formData.opcoes.length > 0 && (
                  <div className="mb-4">
                    {/* Campo de filtro */}
                    <div className="mb-3">
                      <div className="relative">
                        <Search
                          size={16}
                          className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                        />
                        <input
                          type="text"
                          placeholder="Filtrar por ID, Label ou Filter..."
                          value={optionFilter}
                          onChange={(e) => setOptionFilter(e.target.value)}
                          className="input pl-9 text-sm"
                        />
                        {optionFilter && (
                          <button
                            type="button"
                            onClick={() => setOptionFilter('')}
                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                          >
                            <X size={16} />
                          </button>
                        )}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {(() => {
                          const filtered = formData.opcoes.filter((opt) => {
                            const filterLower = optionFilter.toLowerCase()
                            return (
                              opt.id.toLowerCase().includes(filterLower) ||
                              opt.label.toLowerCase().includes(filterLower) ||
                              (opt.filter && opt.filter.toLowerCase().includes(filterLower))
                            )
                          })
                          return optionFilter
                            ? `Mostrando ${filtered.length} de ${formData.opcoes.length} opções`
                            : `${formData.opcoes.length} opções no total`
                        })()}
                      </p>
                    </div>

                    {/* Lista filtrada */}
                    <div className="space-y-2 max-h-60 overflow-y-auto border rounded-lg p-3 bg-gray-50">
                      {(() => {
                        const filteredOptions = formData.opcoes.filter((opt) => {
                          if (!optionFilter) return true
                          const filterLower = optionFilter.toLowerCase()
                          return (
                            opt.id.toLowerCase().includes(filterLower) ||
                            opt.label.toLowerCase().includes(filterLower) ||
                            (opt.filter && opt.filter.toLowerCase().includes(filterLower))
                          )
                        })

                        if (filteredOptions.length === 0) {
                          return (
                            <div className="text-center py-4 text-gray-500 text-sm">
                              Nenhuma opção encontrada com o filtro "{optionFilter}"
                            </div>
                          )
                        }

                        return filteredOptions.map((opt) => (
                          <div
                            key={opt.id}
                            className="flex items-center justify-between bg-white p-2 rounded border"
                          >
                            <div className="flex-1">
                              <span className="font-mono text-sm text-gray-600">{opt.id}</span>
                              <span className="mx-2 text-gray-400">→</span>
                              <span className="font-medium text-gray-900">{opt.label}</span>
                              {opt.filter && (
                                <span className="ml-2 text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                                  filtro: {opt.filter}
                                </span>
                              )}
                            </div>
                            <button
                              type="button"
                              onClick={() => handleRemoveOption(opt.id)}
                              className="text-red-500 hover:text-red-700 ml-2"
                            >
                              <X size={16} />
                            </button>
                          </div>
                        ))
                      })()}
                    </div>
                  </div>
                )}

                {formData.opcoes.length === 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                    <p className="text-sm text-yellow-800">
                      ℹ️ Nenhuma opção adicionada. Você pode salvar a lista vazia e adicionar opções depois.
                    </p>
                  </div>
                )}

                {/* Adicionar nova opção */}
                <div className="border rounded-lg p-4 bg-blue-50">
                  <p className="text-sm font-medium text-gray-700 mb-3">Adicionar Opção</p>
                  <div className="grid grid-cols-3 gap-3">
                    <input
                      type="text"
                      value={newOption.id}
                      onChange={(e) => setNewOption({ ...newOption, id: e.target.value })}
                      placeholder="ID da opção (ex: sp)"
                      className="input"
                    />
                    <input
                      type="text"
                      value={newOption.label}
                      onChange={(e) => setNewOption({ ...newOption, label: e.target.value })}
                      placeholder="Label (ex: São Paulo)"
                      className="input"
                    />
                    <input
                      type="text"
                      value={newOption.filter || ''}
                      onChange={(e) => setNewOption({ ...newOption, filter: e.target.value })}
                      placeholder="Filtro (opcional)"
                      className="input"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleAddOption}
                    className="btn-secondary mt-3 w-full"
                  >
                    <Plus size={16} className="mr-2" />
                    Adicionar Opção
                  </button>
                </div>
              </div>

              {/* Botões */}
              <div className="flex justify-end space-x-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => {
                    setIsModalOpen(false)
                    resetForm()
                  }}
                  className="btn-secondary"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? 'Salvando...'
                    : editingList
                    ? 'Atualizar'
                    : 'Criar Lista'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal DANGER ZONE - Importação */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-red-900 flex items-center gap-2">
                <AlertTriangle className="h-6 w-6 text-red-600" />
                DANGER ZONE - Importar Lista
              </h2>
            </div>

            <div className="p-6 space-y-6">
              {/* Informações do arquivo */}
              <div className="bg-gray-50 border border-gray-300 rounded p-3">
                <p className="text-sm font-semibold text-gray-700">Arquivo selecionado:</p>
                <p className="text-sm text-gray-900 font-mono">{selectedFile?.name}</p>
              </div>

              {/* DANGER ZONE */}
              <div className="bg-red-100 border-2 border-red-500 rounded-lg p-4">
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <div className="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded">
                      DANGER ZONE
                    </div>
                    <p className="text-sm font-bold text-red-900">
                      Excluir TUDO e Substituir
                    </p>
                  </div>

                  <div className="bg-white border border-red-300 rounded p-3 space-y-2">
                    <p className="text-sm text-red-900 font-semibold">
                      ⚠️ ATENÇÃO: Esta ação é IRREVERSÍVEL!
                    </p>
                    <ul className="text-xs text-red-800 space-y-1 ml-4 list-disc">
                      <li>Todas as opções existentes serão PERMANENTEMENTE EXCLUÍDAS</li>
                      <li>Campos configurados podem ficar INCONSISTENTES</li>
                      <li>O conteúdo será SUBSTITUÍDO pelo arquivo JSON</li>
                      <li>NÃO É POSSÍVEL DESFAZER esta operação</li>
                    </ul>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-red-900">
                      Para confirmar, digite: <span className="font-mono bg-red-200 px-2 py-0.5 rounded">EXCLUIR TUDO</span>
                    </label>
                    <input
                      type="text"
                      value={confirmationText}
                      onChange={(e) => setConfirmationText(e.target.value)}
                      placeholder="Digite EXCLUIR TUDO para confirmar"
                      className="input font-mono border-red-300 focus:border-red-500 focus:ring-red-500"
                      disabled={isImporting}
                    />
                    {confirmationText && !isConfirmationValid && (
                      <p className="text-xs text-red-600">
                        ❌ Texto incorreto. Digite exatamente: EXCLUIR TUDO
                      </p>
                    )}
                    {isConfirmationValid && (
                      <p className="text-xs text-green-600 font-semibold">
                        ✅ Confirmação válida
                      </p>
                    )}
                  </div>

                  <div className="bg-yellow-50 border border-yellow-300 rounded p-3">
                    <p className="text-xs text-yellow-900 font-semibold">
                      💡 Após digitar "EXCLUIR TUDO", você ainda terá que confirmar DUAS VEZES em pop-ups de segurança.
                    </p>
                  </div>
                </div>
              </div>

              {/* Botões */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  onClick={handleCancelImport}
                  disabled={isImporting}
                  className="btn-secondary"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleConfirmImport}
                  disabled={!isConfirmationValid || isImporting}
                  className={`px-4 py-2 rounded font-medium ${
                    isConfirmationValid
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {isImporting ? 'Importando...' : 'Confirmar e Importar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

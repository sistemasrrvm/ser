/**
 * FormTemplateEdit Page - Edição de Template com Abas
 * Sprint 003 - Navegação Hierárquica
 */

import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { formulariosApi } from '@/lib/api/formularios'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ArrowLeft, Download, Upload, AlertTriangle, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import FormTemplateInfo from '../components/FormTemplate/FormTemplateInfo'
import FormPageList from '../components/FormTemplate/FormPageList'
import { useState, useRef } from 'react'

export default function FormTemplateEditPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const templateId = parseInt(id || '0')
  const [isExporting, setIsExporting] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [confirmationText, setConfirmationText] = useState('')
  const [deleteConfirmationText, setDeleteConfirmationText] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const isConfirmationValid = confirmationText.toUpperCase() === 'EXCLUIR TUDO'
  const isDeleteConfirmationValid = deleteConfirmationText.toUpperCase() === 'EXCLUIR'

  // Query para buscar formulário
  const { data: template, isLoading } = useQuery({
    queryKey: ['formulario', templateId],
    queryFn: () => formulariosApi.get(templateId),
    enabled: !!templateId,
  })

  // Mutation para excluir formulário
  const deleteMutation = useMutation({
    mutationFn: () => formulariosApi.delete(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['formularios'] })
      navigate('/formularios')
    },
  })

  // Handler para exportar template
  const handleExportTemplate = async () => {
    if (!template) return

    try {
      setIsExporting(true)

      // Chamar API para exportar
      const exportData = await formulariosApi.exportTemplate(templateId)

      // Criar blob e fazer download
      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json'
      })

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `template-${template.nome.replace(/[^a-zA-Z0-9]/g, '-')}-${Date.now()}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      alert('Template exportado com sucesso!')
    } catch (error: any) {
      console.error('Erro ao exportar template:', error)
      alert('Erro ao exportar template: ' + (error?.response?.data?.detail || error?.message || 'Erro desconhecido'))
    } finally {
      setIsExporting(false)
    }
  }

  // Handler para selecionar arquivo
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

    // MÚLTIPLAS CONFIRMAÇÕES (padrão do sistema)

    // Primeira confirmação
    if (
      !confirm(
        `🚨 CONFIRMAÇÃO FINAL - DANGER ZONE 🚨\n\n` +
          `Esta ação vai EXCLUIR PERMANENTEMENTE:\n` +
          `- Todas as páginas existentes\n` +
          `- Todos os campos dentro dessas páginas\n` +
          `- Relatórios preenchidos podem ficar INCONSISTENTES\n\n` +
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

      const result = await formulariosApi.importTemplate(templateId, selectedFile)

      // Atualizar cache
      queryClient.invalidateQueries({ queryKey: ['formulario', templateId] })
      queryClient.invalidateQueries({ queryKey: ['formularios'] })

      alert(`Template "${result.nome}" importado e substituído com sucesso!`)

      // Fechar modal e resetar
      setShowImportModal(false)
      setSelectedFile(null)
      setConfirmationText('')

      // Recarregar página atual para mostrar novos dados
      window.location.reload()
    } catch (error: any) {
      console.error('Erro ao importar template:', error)
      alert('Erro ao importar template: ' + (error?.response?.data?.detail || error?.message || 'Erro desconhecido'))
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

  // Handler para excluir formulário (DANGER ZONE)
  const handleDeleteTemplate = async () => {
    if (!isDeleteConfirmationValid) return

    if (
      !confirm(
        `🚨 CONFIRMAÇÃO FINAL - DANGER ZONE 🚨\n\n` +
          `Você está prestes a EXCLUIR PERMANENTEMENTE este formulário:\n\n` +
          `"${template?.nome}"\n\n` +
          `Esta ação vai EXCLUIR:\n` +
          `- O formulário completo\n` +
          `- Todas as páginas\n` +
          `- Todos os campos\n\n` +
          `Relatórios preenchidos podem ficar INCONSISTENTES!\n\n` +
          `Esta ação NÃO PODE SER DESFEITA!\n\n` +
          `Deseja realmente continuar?`
      )
    ) {
      return
    }

    try {
      await deleteMutation.mutateAsync()
      alert('Formulário excluído com sucesso!')
    } catch (error: any) {
      console.error('Erro ao excluir formulário:', error)
      alert('Erro ao excluir formulário: ' + (error?.response?.data?.detail || error?.message || 'Erro desconhecido'))
    }
  }

  const handleCancelDelete = () => {
    setShowDeleteModal(false)
    setDeleteConfirmationText('')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Carregando...</div>
      </div>
    )
  }

  if (!template) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Formulário não encontrado</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header com breadcrumb */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/formularios')}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{template.nome}</h1>
            <p className="text-gray-500 mt-1">{template.descricao}</p>
          </div>
        </div>

        {/* Botões Importar, Exportar e Excluir */}
        <div className="flex gap-2">
          {/* Input file oculto */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            className="hidden"
            onChange={handleFileSelect}
          />

          {/* Botão Exportar Template */}
          <Button
            variant="outline"
            onClick={handleExportTemplate}
            disabled={isExporting}
          >
            <Download className="h-4 w-4 mr-2" />
            {isExporting ? 'Exportando...' : 'Exportar Template'}
          </Button>

          {/* Botão Importar Template (DANGER ZONE) */}
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={isImporting}
            className="border-red-500 text-red-700 hover:bg-red-50"
          >
            <Upload className="h-4 w-4 mr-2" />
            {isImporting ? 'Importando...' : 'Importar Template'}
          </Button>

          {/* Botão Excluir Formulário (DANGER ZONE) */}
          <Button
            variant="outline"
            onClick={() => setShowDeleteModal(true)}
            disabled={deleteMutation.isPending}
            className="border-red-600 text-red-700 hover:bg-red-50"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Excluir Formulário
          </Button>
        </div>
      </div>

      {/* Tabs de navegação */}
      <Tabs defaultValue="info" className="w-full">
        <TabsList>
          <TabsTrigger value="info">Informações</TabsTrigger>
          <TabsTrigger value="pages">Páginas</TabsTrigger>
        </TabsList>

        <TabsContent value="info" className="mt-6">
          <FormTemplateInfo template={template} />
        </TabsContent>

        <TabsContent value="pages" className="mt-6">
          <FormPageList templateId={templateId} />
        </TabsContent>
      </Tabs>

      {/* Modal DANGER ZONE - Excluir Formulário */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-red-900 flex items-center gap-2">
                <AlertTriangle className="h-6 w-6 text-red-600" />
                DANGER ZONE - Excluir Formulário
              </h2>
            </div>

            <div className="p-6 space-y-6">
              {/* Informações do formulário */}
              <div className="bg-gray-50 border border-gray-300 rounded p-3">
                <p className="text-sm font-semibold text-gray-700">Formulário a ser excluído:</p>
                <p className="text-lg text-gray-900 font-bold">{template?.nome}</p>
                {template?.descricao && (
                  <p className="text-sm text-gray-600 mt-1">{template.descricao}</p>
                )}
              </div>

              {/* DANGER ZONE */}
              <div className="bg-red-100 border-2 border-red-500 rounded-lg p-4">
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <div className="bg-red-600 text-white text-xs font-bold px-2 py-1 rounded">
                      DANGER ZONE
                    </div>
                    <p className="text-sm font-bold text-red-900">
                      Exclusão Permanente
                    </p>
                  </div>

                  <div className="bg-white border border-red-300 rounded p-3 space-y-2">
                    <p className="text-sm text-red-900 font-semibold">
                      ⚠️ ATENÇÃO: Esta ação é IRREVERSÍVEL!
                    </p>
                    <ul className="text-xs text-red-800 space-y-1 ml-4 list-disc">
                      <li>O formulário será PERMANENTEMENTE EXCLUÍDO</li>
                      <li>Todas as páginas serão PERDIDAS</li>
                      <li>Todos os campos serão PERDIDOS</li>
                      <li>Relatórios preenchidos podem ficar INCONSISTENTES</li>
                      <li>NÃO É POSSÍVEL DESFAZER esta operação</li>
                    </ul>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-sm font-semibold text-red-900">
                      Para confirmar, digite: <span className="font-mono bg-red-200 px-2 py-0.5 rounded">EXCLUIR</span>
                    </Label>
                    <Input
                      type="text"
                      value={deleteConfirmationText}
                      onChange={(e) => setDeleteConfirmationText(e.target.value)}
                      placeholder="Digite EXCLUIR para confirmar"
                      className="font-mono border-red-300 focus:border-red-500 focus:ring-red-500"
                      disabled={deleteMutation.isPending}
                    />
                    {deleteConfirmationText && !isDeleteConfirmationValid && (
                      <p className="text-xs text-red-600">
                        ❌ Texto incorreto. Digite exatamente: EXCLUIR
                      </p>
                    )}
                    {isDeleteConfirmationValid && (
                      <p className="text-xs text-green-600 font-semibold">
                        ✅ Confirmação válida
                      </p>
                    )}
                  </div>

                  <div className="bg-yellow-50 border border-yellow-300 rounded p-3">
                    <p className="text-xs text-yellow-900 font-semibold">
                      💡 Após digitar "EXCLUIR", você ainda terá que confirmar em um pop-up de segurança.
                    </p>
                  </div>
                </div>
              </div>

              {/* Botões */}
              <div className="flex justify-end space-x-3 pt-4">
                <Button
                  variant="outline"
                  onClick={handleCancelDelete}
                  disabled={deleteMutation.isPending}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleDeleteTemplate}
                  disabled={!isDeleteConfirmationValid || deleteMutation.isPending}
                  className={`${
                    isDeleteConfirmationValid
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {deleteMutation.isPending ? 'Excluindo...' : 'Confirmar e Excluir'}
                </Button>
              </div>
            </div>
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
                DANGER ZONE - Importar Template
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
                      <li>Todas as páginas existentes serão PERMANENTEMENTE EXCLUÍDAS</li>
                      <li>Todos os campos dentro dessas páginas serão PERDIDOS</li>
                      <li>Relatórios preenchidos podem ficar INCONSISTENTES</li>
                      <li>O ID do template será MANTIDO, mas o conteúdo será SUBSTITUÍDO</li>
                      <li>NÃO É POSSÍVEL DESFAZER esta operação</li>
                    </ul>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-sm font-semibold text-red-900">
                      Para confirmar, digite: <span className="font-mono bg-red-200 px-2 py-0.5 rounded">EXCLUIR TUDO</span>
                    </Label>
                    <Input
                      type="text"
                      value={confirmationText}
                      onChange={(e) => setConfirmationText(e.target.value)}
                      placeholder="Digite EXCLUIR TUDO para confirmar"
                      className="font-mono border-red-300 focus:border-red-500 focus:ring-red-500"
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
                <Button
                  variant="outline"
                  onClick={handleCancelImport}
                  disabled={isImporting}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleConfirmImport}
                  disabled={!isConfirmationValid || isImporting}
                  className={`${
                    isConfirmationValid
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {isImporting ? 'Importando...' : 'Confirmar e Importar'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

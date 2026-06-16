/**
 * ImportExcelModal - Modal para importação de páginas e campos via Excel
 * Sprint 005 - Importar Excel de Páginas e Campos
 */

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { formulariosApi } from '@/lib/api/formularios'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Download, Upload, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

interface ImportExcelModalProps {
  templateId: number
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  hasExistingPages: boolean
  existingPagesCount: number
}

export default function ImportExcelModal({
  templateId,
  isOpen,
  onClose,
  onSuccess,
  hasExistingPages,
  existingPagesCount,
}: ImportExcelModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [replaceMode, setReplaceMode] = useState(false)
  const [confirmationText, setConfirmationText] = useState('')
  const [importErrors, setImportErrors] = useState<{ line: number; message: string }[]>([])

  // Verificar se usuário digitou corretamente
  const isConfirmationValid = confirmationText.toUpperCase() === 'EXCLUIR TUDO'

  // Mutation: download template
  const downloadTemplateMutation = useMutation({
    mutationFn: () => formulariosApi.downloadImportTemplate(),
    onSuccess: (blob) => {
      // Criar URL temporária e fazer download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'Template_Importacao_Paginas_Campos.xlsx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao baixar template')
    },
  })

  // Mutation: importar Excel
  const importMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) throw new Error('Nenhum arquivo selecionado')
      return formulariosApi.importExcel(templateId, selectedFile, replaceMode)
    },
    onSuccess: (data) => {
      alert(`✅ ${data.message}`)
      onSuccess()
      handleClose()
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail

      // Se for objeto com lista de erros
      if (detail && typeof detail === 'object' && detail.errors) {
        setImportErrors(detail.errors)
      } else {
        // Erro genérico
        alert(detail || error.message || 'Erro ao importar arquivo')
      }
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validar extensão
    if (!file.name.endsWith('.xlsx')) {
      alert('Por favor, selecione um arquivo .xlsx válido')
      e.target.value = ''
      return
    }

    // Validar tamanho (5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('Arquivo muito grande. Tamanho máximo: 5MB')
      e.target.value = ''
      return
    }

    setSelectedFile(file)
    setImportErrors([]) // Limpar erros anteriores
  }

  const handleImport = () => {
    if (!selectedFile) {
      alert('Por favor, selecione um arquivo para importar')
      return
    }

    // Se tem páginas e não marcou replace, confirmar
    if (hasExistingPages && !replaceMode) {
      if (
        !confirm(
          `Atenção: Existem ${existingPagesCount} páginas cadastradas.\n\n` +
            `A importação irá ADICIONAR novas páginas/campos aos existentes.\n\n` +
            `Deseja continuar?`
        )
      ) {
        return
      }
    }

    // Se marcou replace, MÚLTIPLAS CONFIRMAÇÕES
    if (replaceMode) {
      // Primeira confirmação
      if (
        !confirm(
          `🚨 CONFIRMAÇÃO FINAL - DANGER ZONE 🚨\n\n` +
            `Você está prestes a EXCLUIR PERMANENTEMENTE:\n` +
            `• ${existingPagesCount} páginas\n` +
            `• Todos os campos dessas páginas\n` +
            `• Configurações e mapeamentos Excel\n\n` +
            `Esta ação é IRREVERSÍVEL!\n\n` +
            `Tem CERTEZA ABSOLUTA?`
        )
      ) {
        return
      }

      // Segunda confirmação (última chance)
      if (
        !confirm(
          `⚠️ ÚLTIMA CONFIRMAÇÃO ⚠️\n\n` +
            `Esta é sua ÚLTIMA CHANCE para cancelar!\n\n` +
            `Após clicar OK, TODOS os dados serão PERMANENTEMENTE EXCLUÍDOS.\n\n` +
            `Confirma a exclusão total e importação da nova configuração?`
        )
      ) {
        return
      }
    }

    importMutation.mutate()
  }

  const handleClose = () => {
    setSelectedFile(null)
    setReplaceMode(false)
    setConfirmationText('')
    setImportErrors([])
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Importar Páginas e Campos</DialogTitle>
          <DialogDescription>
            Importe múltiplas páginas e campos de uma vez usando uma planilha Excel
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Instruções */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <ol className="list-decimal list-inside space-y-1 text-sm text-blue-900">
              <li>Baixe o modelo Excel clicando no botão abaixo</li>
              <li>Preencha a planilha "Dados" com suas páginas e campos</li>
              <li>Consulte a planilha "Instruções" para detalhes e exemplos</li>
              <li>Salve o arquivo e faça o upload aqui</li>
            </ol>
          </div>

          {/* Botão Download Template */}
          <div>
            <Button
              variant="outline"
              onClick={() => downloadTemplateMutation.mutate()}
              disabled={downloadTemplateMutation.isPending}
              className="w-full"
            >
              <Download className="h-4 w-4 mr-2" />
              {downloadTemplateMutation.isPending ? 'Baixando...' : 'Baixar Modelo Excel'}
            </Button>
            <p className="text-xs text-gray-500 mt-2">
              O modelo contém exemplos e instruções completas
            </p>
          </div>

          {/* Upload de Arquivo */}
          <div className="space-y-2">
            <Label htmlFor="file">Arquivo Excel (.xlsx)</Label>
            <Input
              id="file"
              type="file"
              accept=".xlsx"
              onChange={handleFileChange}
              disabled={importMutation.isPending}
            />
            {selectedFile && (
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle className="h-4 w-4" />
                <span>{selectedFile.name}</span>
              </div>
            )}
          </div>

          {/* Aviso se já tem páginas */}
          {hasExistingPages && selectedFile && (
            <div className="space-y-4">
              {/* Info: Modo normal (adicionar) */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-blue-900">Informação</p>
                    <p className="text-sm text-blue-700 mt-1">
                      Existem <strong>{existingPagesCount} páginas</strong> cadastradas.
                      A importação irá <strong>ADICIONAR</strong> as novas páginas/campos aos existentes.
                    </p>
                  </div>
                </div>
              </div>

              {/* DANGER ZONE: Excluir tudo e substituir */}
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
                      <li>Todas as {existingPagesCount} páginas serão PERMANENTEMENTE EXCLUÍDAS</li>
                      <li>Todos os campos dentro dessas páginas serão PERDIDOS</li>
                      <li>Relatórios preenchidos podem ficar INCONSISTENTES</li>
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
                      disabled={importMutation.isPending}
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

                  <div className="flex items-start space-x-2">
                    <input
                      type="checkbox"
                      id="replace"
                      checked={replaceMode}
                      onChange={(e) => setReplaceMode(e.target.checked)}
                      disabled={!isConfirmationValid || importMutation.isPending}
                      className="mt-1"
                    />
                    <label
                      htmlFor="replace"
                      className={`text-sm font-medium cursor-pointer ${
                        isConfirmationValid ? 'text-red-900' : 'text-gray-400'
                      }`}
                    >
                      Confirmo que quero EXCLUIR TUDO e importar nova configuração
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Lista de Erros */}
          {importErrors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <XCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-semibold text-red-900">
                    Erros encontrados no arquivo ({importErrors.length})
                  </p>
                  <div className="mt-2 max-h-40 overflow-y-auto space-y-1">
                    {importErrors.map((error, index) => (
                      <div key={index} className="text-xs font-mono text-red-800">
                        <strong>Linha {error.line}:</strong> {error.message}
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-red-600 mt-3">
                    Corrija os erros no arquivo e tente novamente. Nenhum dado foi importado.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Limites */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <p className="text-xs text-blue-900 font-medium">Limites</p>
            <ul className="text-xs text-blue-700 mt-1 space-y-1">
              <li>• Máximo: 50 páginas e 500 campos por importação</li>
              <li>• Arquivo máximo: 5MB</li>
              <li>• Todos os dados são validados antes da importação</li>
            </ul>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={importMutation.isPending}>
            Cancelar
          </Button>
          <Button
            onClick={handleImport}
            disabled={!selectedFile || importMutation.isPending}
            className={replaceMode ? 'bg-red-600 hover:bg-red-700 text-white' : ''}
          >
            <Upload className="h-4 w-4 mr-2" />
            {importMutation.isPending
              ? 'Importando...'
              : replaceMode
                ? '🚨 EXCLUIR TUDO E IMPORTAR'
                : 'Importar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

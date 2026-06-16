/**
 * FormTemplateInfo - Informações do Formulário
 * Permite editar nome e descrição
 */

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { formulariosApi } from '@/lib/api/formularios'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Download } from 'lucide-react'
import {
  downloadExcelFromDataUrl,
  mesclagemExcelFilename,
  triggerBlobDownload,
} from '@/lib/download'
import type { Formulario } from '@/lib/api/types'

interface FormTemplateInfoProps {
  template: Formulario
}

export default function FormTemplateInfo({ template }: FormTemplateInfoProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    nome: template.nome,
    descricao: template.descricao || '',
    excel_template: template.excel_template || '',
  })
  const [excelFileName, setExcelFileName] = useState<string | null>(null)
  const [isDownloadingExcel, setIsDownloadingExcel] = useState(false)

  const queryClient = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: () => formulariosApi.update(template.id, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['formulario', template.id] })
      queryClient.invalidateQueries({ queryKey: ['formularios'] })
      setIsEditing(false)
    },
  })

  const hasExcelTemplate = Boolean(isEditing ? formData.excel_template : template.excel_template)

  const handleDownloadExcel = async () => {
    const filename =
      excelFileName ||
      mesclagemExcelFilename(
        isEditing ? formData.nome : template.nome,
        template.id,
        isEditing ? formData.excel_template : template.excel_template
      )

    try {
      setIsDownloadingExcel(true)

      // Upload local ainda não salvo: baixar do base64 em memória
      if (isEditing && excelFileName && formData.excel_template) {
        downloadExcelFromDataUrl(formData.excel_template, filename)
        return
      }

      const blob = await formulariosApi.downloadExcelTemplate(template.id)
      triggerBlobDownload(blob, filename)
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string }
      alert(err.response?.data?.detail || err.message || 'Erro ao baixar template Excel')
    } finally {
      setIsDownloadingExcel(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate()
  }

  const handleCancel = () => {
    setFormData({
      nome: template.nome,
      descricao: template.descricao || '',
      excel_template: template.excel_template || '',
    })
    setExcelFileName(null)
    setIsEditing(false)
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      alert('Por favor, selecione um arquivo Excel válido (.xlsx ou .xls)')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      alert('Arquivo muito grande. Tamanho máximo: 10MB')
      return
    }

    const reader = new FileReader()
    reader.onload = () => {
      const base64 = reader.result as string
      setFormData({ ...formData, excel_template: base64 })
      setExcelFileName(file.name)
    }
    reader.onerror = () => {
      alert('Erro ao ler arquivo')
    }
    reader.readAsDataURL(file)
  }

  const handleRemoveExcel = () => {
    setFormData({ ...formData, excel_template: '' })
    setExcelFileName(null)
  }

  const ExcelDownloadButton = () => (
    <Button
      type="button"
      variant="outline"
      size="sm"
      onClick={handleDownloadExcel}
      disabled={isDownloadingExcel}
      className="shrink-0"
    >
      <Download className="h-4 w-4 mr-1" />
      {isDownloadingExcel ? 'Baixando...' : 'Baixar Excel'}
    </Button>
  )

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Informações do Formulário</h2>
        {!isEditing && (
          <Button variant="outline" onClick={() => setIsEditing(true)}>
            Editar
          </Button>
        )}
      </div>

      {isEditing ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="nome">Nome do Formulário *</Label>
            <Input
              id="nome"
              value={formData.nome}
              onChange={(e) =>
                setFormData({ ...formData, nome: e.target.value })
              }
              required
              minLength={3}
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="descricao">Descrição</Label>
            <textarea
              id="descricao"
              className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={formData.descricao}
              onChange={(e) =>
                setFormData({ ...formData, descricao: e.target.value })
              }
              maxLength={500}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="excel">Template Excel (para mesclagem de dados)</Label>
            <div className="space-y-2">
              {formData.excel_template ? (
                <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-md">
                  <span className="text-sm text-green-700 flex-1">
                    {excelFileName || 'Arquivo anexado'}
                  </span>
                  <ExcelDownloadButton />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleRemoveExcel}
                  >
                    Remover
                  </Button>
                </div>
              ) : (
                <Input
                  id="excel"
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileChange}
                />
              )}
              <p className="text-xs text-gray-500">
                Formatos aceitos: .xlsx, .xls | Tamanho máximo: 10MB
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Salvando...' : 'Salvar'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={updateMutation.isPending}
            >
              Cancelar
            </Button>
          </div>
        </form>
      ) : (
        <div className="space-y-4">
          <div>
            <Label className="text-gray-500">Nome</Label>
            <p className="mt-1 text-gray-900">{template.nome}</p>
          </div>

          <div>
            <Label className="text-gray-500">Descrição</Label>
            <p className="mt-1 text-gray-900">
              {template.descricao || (
                <span className="text-gray-400 italic">Sem descrição</span>
              )}
            </p>
          </div>

          <div>
            <Label className="text-gray-500">Template Excel (mesclagem)</Label>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              {hasExcelTemplate ? (
                <>
                  <span className="inline-flex items-center gap-2 px-3 py-1 bg-green-50 text-green-700 rounded-md text-sm">
                    ✓ Arquivo Excel anexado
                  </span>
                  <ExcelDownloadButton />
                </>
              ) : (
                <span className="text-gray-400 italic">Nenhum arquivo anexado</span>
              )}
            </div>
            {hasExcelTemplate && (
              <p className="text-xs text-gray-500 mt-2">
                Baixe o Excel bruto para revisar o layout antes de um novo upload.
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <Label className="text-gray-500">Criado em</Label>
              <p className="mt-1 text-gray-900">
                {new Date(template.criado_em).toLocaleString('pt-BR')}
              </p>
            </div>
            <div>
              <Label className="text-gray-500">Atualizado em</Label>
              <p className="mt-1 text-gray-900">
                {new Date(template.atualizado_em).toLocaleString('pt-BR')}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

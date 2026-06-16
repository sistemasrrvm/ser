/**
 * ReportKickoffPage - Iniciar novo relatório
 * Sprint 004 - Entrada de Dados (KICKOFF) - Versão Simplificada
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reportsApi } from '@/lib/api/reports'
import { api } from '@/lib/api/client'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'

export default function ReportKickoffPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [templateId, setTemplateId] = useState<number | null>(null)

  // Query: Listar templates
  const { data: templates, isLoading: loadingTemplates } = useQuery({
    queryKey: ['form-templates'],
    queryFn: async () => {
      const response = await api.get('/formularios')
      return response.data
    },
  })

  // Mutation: Criar relatório
  const createMutation = useMutation({
    mutationFn: reportsApi.create,
    onSuccess: (report) => {
      // Invalidar queries de relatórios para atualizar listagem e dashboard
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      navigate(`/relatorios/${report.id}/preencher`)
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao criar relatório')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!templateId) {
      alert('Selecione um template de formulário')
      return
    }

    createMutation.mutate({
      form_template_id: templateId,
    })
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900">Novo Relatório</h1>
        <p className="text-sm text-gray-500 mt-2">
          Selecione o template de formulário para iniciar
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 bg-white p-8 rounded-lg border shadow-sm">
        {/* Template */}
        <div className="space-y-3">
          <Label className="text-base font-semibold">Template de Formulário *</Label>
          <Select
            value={templateId?.toString() || ''}
            onChange={(e) => setTemplateId(Number(e.target.value))}
            required
            disabled={loadingTemplates}
            className="text-base py-3"
          >
            <option value="">Selecione o template</option>
            {templates?.formularios?.map((t: any) => (
              <option key={t.id} value={t.id}>
                {t.nome}
              </option>
            ))}
          </Select>
          {templates?.formularios && templates.formularios.length === 0 && (
            <p className="text-sm text-orange-600">
              Nenhum template disponível. Crie um template primeiro.
            </p>
          )}
        </div>

        {/* Botões */}
        <div className="flex gap-3 pt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/relatorios')}
            className="flex-1"
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={createMutation.isPending || !templateId}
            className="flex-1 text-base py-3"
          >
            {createMutation.isPending ? 'Criando...' : 'Iniciar Preenchimento'}
          </Button>
        </div>
      </form>
    </div>
  )
}

/**
 * FormSeparatorModal - Modal para Criar/Editar Separador Visual
 * Separadores servem para organizar visualmente grupos de campos dentro de uma página
 */

import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { formFieldsApi, type FormField, type FormFieldCreate } from '@/lib/api/formFields'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface FormSeparatorModalProps {
  pageId: number
  separator: FormField | null
  open: boolean
  onOpenChange: (open: boolean) => void
  existingFields: FormField[]
}

export default function FormSeparatorModal({ pageId, separator, open, onOpenChange, existingFields }: FormSeparatorModalProps) {
  const [formData, setFormData] = useState<FormFieldCreate>({
    rotulo: `separator_${Date.now()}`,
    ordem: 1,
    tipo: 'separator',
    configuracao: {
      titulo: '',
      descricao: '',
    },
  })

  const queryClient = useQueryClient()

  // Calcular próxima ordem disponível
  const getNextOrder = () => {
    if (existingFields.length === 0) return 1
    const maxOrder = Math.max(...existingFields.map(f => f.ordem))
    return maxOrder + 1
  }

  useEffect(() => {
    if (separator) {
      // Editando: manter label existente
      setFormData({
        rotulo: separator.rotulo,
        ordem: separator.ordem,
        tipo: 'separator',
        configuracao: separator.configuracao || { titulo: '', descricao: '' },
      })
    } else {
      // Criando: gerar label único com timestamp
      setFormData({
        rotulo: `separator_${Date.now()}`,
        ordem: getNextOrder(),
        tipo: 'separator',
        configuracao: { titulo: '', descricao: '' },
      })
    }
  }, [separator, open, existingFields])

  const createMutation = useMutation({
    mutationFn: (data: FormFieldCreate) => formFieldsApi.create(pageId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-fields', pageId] })
      onOpenChange(false)
    },
    onError: (error: any) => alert(error.response?.data?.detail || 'Erro ao criar separador'),
  })

  const updateMutation = useMutation({
    mutationFn: (data: FormFieldCreate) => formFieldsApi.update(pageId, separator!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-fields', pageId] })
      onOpenChange(false)
    },
    onError: (error: any) => alert(error.response?.data?.detail || 'Erro ao atualizar separador'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validar campos obrigatórios
    if (!formData.configuracao?.titulo || formData.configuracao.titulo.trim() === '') {
      alert('Título é obrigatório')
      return
    }

    if (separator) {
      updateMutation.mutate(formData)
    } else {
      createMutation.mutate(formData)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{separator ? 'Editar Separador' : 'Novo Separador'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Título *</Label>
            <Input
              value={formData.configuracao?.titulo || ''}
              onChange={(e) => setFormData({ ...formData, configuracao: { ...formData.configuracao, titulo: e.target.value } })}
              placeholder="Ex: Dados Pessoais, Informações de Contato"
              required
              maxLength={100}
            />
            <p className="text-xs text-gray-500">
              Será exibido em negrito no formulário
            </p>
          </div>

          <div className="space-y-2">
            <Label>Descrição</Label>
            <Input
              value={formData.configuracao?.descricao || ''}
              onChange={(e) => setFormData({ ...formData, configuracao: { ...formData.configuracao, descricao: e.target.value } })}
              placeholder="Ex: Preencha seus dados pessoais abaixo"
              maxLength={255}
            />
            <p className="text-xs text-gray-500">
              Texto explicativo exibido abaixo do título (opcional)
            </p>
          </div>

          <div className="space-y-2">
            <Label>Posição *</Label>
            <Input
              type="number"
              value={formData.ordem}
              onChange={(e) => setFormData({ ...formData, ordem: parseInt(e.target.value) })}
              required
              min={1}
            />
            <p className="text-xs text-gray-500">
              Ordem de exibição entre os campos (1 = primeiro, 2 = segundo...)
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-xs text-blue-900">
              💡 <strong>Dica:</strong> Separadores são exibidos visualmente no formulário de preenchimento,
              ajudando o usuário a identificar diferentes seções dentro da mesma página.
            </p>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Salvando...' : separator ? 'Atualizar' : 'Criar'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

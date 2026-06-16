/**
 * FormPageModal - Modal para Criar/Editar Página
 */

import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { formPagesApi, type FormPage, type FormPageCreate } from '@/lib/api/formPages'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface FormPageModalProps {
  templateId: number
  page: FormPage | null
  open: boolean
  onOpenChange: (open: boolean) => void
  existingPages: FormPage[]
}

export default function FormPageModal({
  templateId,
  page,
  open,
  onOpenChange,
  existingPages,
}: FormPageModalProps) {
  const [formData, setFormData] = useState<FormPageCreate>({
    nome: '',
    ordem: 1,
    regra_exibicao_id: null,
  })

  const queryClient = useQueryClient()

  // Calcular próxima ordem disponível
  const getNextOrder = () => {
    if (existingPages.length === 0) return 1
    const maxOrder = Math.max(...existingPages.map(p => p.ordem))
    return maxOrder + 1
  }

  // Resetar form quando abrir/fechar ou mudar página
  useEffect(() => {
    if (page) {
      setFormData({
        nome: page.nome,
        ordem: page.ordem,
        regra_exibicao_id: page.regra_exibicao_id,
      })
    } else {
      setFormData({
        nome: '',
        ordem: getNextOrder(),
        regra_exibicao_id: null,
      })
    }
  }, [page, open, existingPages])

  // Mutation para criar
  const createMutation = useMutation({
    mutationFn: (data: FormPageCreate) => formPagesApi.create(templateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-pages', templateId] })
      onOpenChange(false)
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Erro ao criar página'
      alert(message)
    },
  })

  // Mutation para atualizar
  const updateMutation = useMutation({
    mutationFn: (data: FormPageCreate) =>
      formPagesApi.update(templateId, page!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-pages', templateId] })
      onOpenChange(false)
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Erro ao atualizar página'
      alert(message)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (page) {
      updateMutation.mutate(formData)
    } else {
      createMutation.mutate(formData)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {page ? 'Editar Página' : 'Nova Página'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="label">Nome da Página *</Label>
            <Input
              id="label"
              value={formData.nome}
              onChange={(e) =>
                setFormData({ ...formData, nome: e.target.value })
              }
              required
              minLength={1}
              maxLength={100}
              placeholder="Ex: Dados Básicos"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ordem">Ordem *</Label>
            <Input
              id="ordem"
              type="number"
              value={formData.ordem}
              onChange={(e) =>
                setFormData({ ...formData, ordem: parseInt(e.target.value) })
              }
              required
              min={1}
            />
            <p className="text-xs text-gray-500">
              A ordem determina a sequência de exibição das páginas
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Salvando...' : page ? 'Atualizar' : 'Criar'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

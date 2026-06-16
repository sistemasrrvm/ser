/**
 * FormPageInfo - Informações da Página
 */

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { formPagesApi, type FormPage } from '@/lib/api/formPages'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface FormPageInfoProps {
  page: FormPage
  templateId: number
}

export default function FormPageInfo({ page, templateId }: FormPageInfoProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    nome: page.nome,
    ordem: page.ordem,
  })

  const queryClient = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: () => formPagesApi.update(templateId, page.id, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-page', templateId, page.id] })
      queryClient.invalidateQueries({ queryKey: ['form-pages', templateId] })
      setIsEditing(false)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateMutation.mutate()
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold">Informações da Página</h2>
        {!isEditing && (
          <Button variant="outline" onClick={() => setIsEditing(true)}>Editar</Button>
        )}
      </div>

      {isEditing ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="label">Nome da Página *</Label>
            <Input id="label" value={formData.nome} onChange={(e) => setFormData({ ...formData, nome: e.target.value })} required minLength={1} maxLength={100} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="ordem">Ordem *</Label>
            <Input id="ordem" type="number" value={formData.ordem} onChange={(e) => setFormData({ ...formData, ordem: parseInt(e.target.value) })} required min={1} />
          </div>

          <div className="flex gap-2">
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Salvando...' : 'Salvar'}
            </Button>
            <Button type="button" variant="outline" onClick={() => setIsEditing(false)}>Cancelar</Button>
          </div>
        </form>
      ) : (
        <div className="space-y-4">
          <div><Label className="text-gray-500">Nome</Label><p className="mt-1 text-gray-900">{page.nome}</p></div>
          <div><Label className="text-gray-500">Ordem</Label><p className="mt-1 text-gray-900">{page.ordem}</p></div>
        </div>
      )}
    </div>
  )
}

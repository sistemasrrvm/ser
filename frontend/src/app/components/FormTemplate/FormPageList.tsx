/**
 * FormPageList - Lista de Páginas com Drag-and-Drop
 * Sprint 003 - CRUD de Páginas
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formPagesApi, type FormPage } from '@/lib/api/formPages'
import { DndContext, closestCenter, DragEndEvent } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy, arrayMove } from '@dnd-kit/sortable'
import { Plus, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useNavigate } from 'react-router-dom'
import SortablePageItem from './SortablePageItem'
import FormPageModal from './FormPageModal'
import ImportExcelModal from './ImportExcelModal'

interface FormPageListProps {
  templateId: number
}

export default function FormPageList({ templateId }: FormPageListProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [editingPage, setEditingPage] = useState<FormPage | null>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Query para listar páginas
  const { data, isLoading } = useQuery({
    queryKey: ['form-pages', templateId],
    queryFn: () => formPagesApi.list(templateId),
  })

  // Mutation para excluir página
  const deleteMutation = useMutation({
    mutationFn: (pageId: number) => formPagesApi.delete(templateId, pageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-pages', templateId] })
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Erro ao excluir página'
      alert(message)
    },
  })

  // Mutation para reordenar
  const reorderMutation = useMutation({
    mutationFn: (pages: { id: number; ordem: number }[]) =>
      formPagesApi.reorder(templateId, pages),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-pages', templateId] })
    },
  })

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (!over || active.id === over.id || !data) return

    const pages = [...data.paginas]
    const oldIndex = pages.findIndex((p) => p.id === active.id)
    const newIndex = pages.findIndex((p) => p.id === over.id)

    const newPages = arrayMove(pages, oldIndex, newIndex)

    // Atualizar ordens
    const updates = newPages.map((page, index) => ({
      id: page.id,
      ordem: index + 1,
    }))

    reorderMutation.mutate(updates)
  }

  const handleEdit = (page: FormPage) => {
    setEditingPage(page)
    setIsModalOpen(true)
  }

  const handleDelete = (page: FormPage) => {
    if (
      confirm(
        `Deseja realmente excluir a página "${page.nome}"?\n\nATENÇÃO: Todos os campos desta página também serão excluídos.`
      )
    ) {
      deleteMutation.mutate(page.id)
    }
  }

  const handleNew = () => {
    setEditingPage(null)
    setIsModalOpen(true)
  }

  const handleNavigateToPage = (pageId: number) => {
    navigate(`/formularios/${templateId}/pages/${pageId}`)
  }

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Carregando páginas...</div>
  }

  const pages = data?.paginas || []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Páginas do Formulário</h2>
          <p className="text-sm text-gray-500 mt-1">
            Arraste para reordenar | {pages.length} página(s)
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsImportModalOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Importar Excel
          </Button>
          <Button onClick={handleNew}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Página
          </Button>
        </div>
      </div>

      {pages.length === 0 ? (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <p className="text-gray-500 mb-4">Nenhuma página criada ainda</p>
          <Button onClick={handleNew} variant="outline">
            <Plus className="h-4 w-4 mr-2" />
            Criar Primeira Página
          </Button>
        </div>
      ) : (
        <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={pages.map((p) => p.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {pages.map((page) => (
                <SortablePageItem
                  key={page.id}
                  page={page}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  onNavigate={handleNavigateToPage}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      {/* Modal de Criar/Editar */}
      <FormPageModal
        templateId={templateId}
        page={editingPage}
        open={isModalOpen}
        onOpenChange={(open) => {
          setIsModalOpen(open)
          if (!open) setEditingPage(null)
        }}
        existingPages={pages}
      />

      {/* Modal de Importação */}
      <ImportExcelModal
        templateId={templateId}
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['form-pages', templateId] })
          setIsImportModalOpen(false)
        }}
        hasExistingPages={pages.length > 0}
        existingPagesCount={pages.length}
      />
    </div>
  )
}

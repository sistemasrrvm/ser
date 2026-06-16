/**
 * SortablePageItem - Item de Página Arrastável
 */

import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Trash2, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { FormPage } from '@/lib/api/formPages'

interface SortablePageItemProps {
  page: FormPage
  onEdit: (page: FormPage) => void
  onDelete: (page: FormPage) => void
  onNavigate: (pageId: number) => void
}

export default function SortablePageItem({
  page,
  onEdit,
  onDelete,
  onNavigate,
}: SortablePageItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: page.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex items-center gap-3">
        {/* Drag Handle */}
        <button
          className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600"
          {...attributes}
          {...listeners}
        >
          <GripVertical className="h-5 w-5" />
        </button>

        {/* Ordem */}
        <div className="flex-shrink-0 w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center text-sm font-semibold text-slate-700">
          {page.ordem}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">{page.nome}</h3>
          {page.regra_exibicao_id && (
            <p className="text-xs text-gray-500 mt-1">
              Regra de visibilidade: #{page.regra_exibicao_id}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onNavigate(page.id)}
            title="Gerenciar Campos"
          >
            <Settings className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onDelete(page)}
            title="Excluir página"
          >
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      </div>
    </div>
  )
}

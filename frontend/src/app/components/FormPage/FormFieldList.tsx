/**
 * FormFieldList - Lista de Campos com Drag-and-Drop
 */

import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { formFieldsApi, type FormField } from '@/lib/api/formFields'
import { DndContext, closestCenter, DragEndEvent } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy, arrayMove, useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Plus, Trash2, Edit2, GripVertical, Minus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import FormFieldModal from './FormFieldModal'
import FormSeparatorModal from './FormSeparatorModal'

interface FormFieldListProps {
  pageId: number
  templateId?: number
}

function SortableFieldItem({ field, onEdit, onDelete, onEditSeparator }: any) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: field.id })

  // Renderização especial para separadores
  if (field.tipo === 'separator') {
    return (
      <div ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.5 : 1 }} className="bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-dashed border-purple-300 rounded-lg p-4 hover:shadow-md transition-shadow">
        <div className="flex items-center gap-3">
          <button className="cursor-grab active:cursor-grabbing text-purple-400 hover:text-purple-600" {...attributes} {...listeners}>
            <GripVertical className="h-5 w-5" />
          </button>
          <div className="flex-shrink-0 w-8 h-8 bg-purple-200 rounded-full flex items-center justify-center text-purple-700">
            <Minus className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-purple-900 truncate">{field.configuracao?.titulo || 'Sem título'}</h3>
              <span className="text-xs bg-purple-200 text-purple-800 px-2 py-0.5 rounded">Separador</span>
            </div>
            <p className="text-xs text-purple-600 mt-1">{field.configuracao?.descricao || 'Sem descrição'}</p>
            <p className="text-xs text-purple-500 mt-1">Posição: {field.ordem}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" onClick={() => onEditSeparator(field)}><Edit2 className="h-4 w-4" /></Button>
            <Button variant="ghost" size="icon" onClick={() => onDelete(field)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
          </div>
        </div>
      </div>
    )
  }

  // Renderização normal para campos
  return (
    <div ref={setNodeRef} style={{ transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.5 : 1 }} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-center gap-3">
        <button className="cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600" {...attributes} {...listeners}>
          <GripVertical className="h-5 w-5" />
        </button>
        <div className="flex-shrink-0 w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center text-sm font-semibold">{field.ordem}</div>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">{field.rotulo}</h3>
          <div className="flex items-center gap-3 mt-1">
            <p className="text-xs text-gray-500">Tipo: {field.tipo}</p>
            {field.configuracao?.excel_mapping && field.configuracao.excel_mapping.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                {field.configuracao.excel_mapping.map((m: any, idx: number) => (
                  <div key={idx} className="flex items-center gap-1">
                    <span className="text-xs text-blue-600 font-medium">{m.planilha}</span>
                    <div className="bg-blue-100 border border-blue-300 text-blue-800 px-2 py-0.5 rounded text-xs font-semibold">
                      {m.celula}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={() => onEdit(field)}><Edit2 className="h-4 w-4" /></Button>
          <Button variant="ghost" size="icon" onClick={() => onDelete(field)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
        </div>
      </div>
    </div>
  )
}

export default function FormFieldList({ pageId, templateId }: FormFieldListProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isSeparatorModalOpen, setIsSeparatorModalOpen] = useState(false)
  const [editingField, setEditingField] = useState<FormField | null>(null)
  const [editingSeparator, setEditingSeparator] = useState<FormField | null>(null)

  // Estados de filtro
  const [filterNome, setFilterNome] = useState('')
  const [filterTipo, setFilterTipo] = useState('')
  const [filterPlanilha, setFilterPlanilha] = useState('')
  const [filterCelula, setFilterCelula] = useState('')

  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['form-fields', pageId],
    queryFn: () => formFieldsApi.list(pageId),
  })

  const deleteMutation = useMutation({
    mutationFn: (fieldId: number) => formFieldsApi.delete(pageId, fieldId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['form-fields', pageId] }),
    onError: (error: any) => alert(error.response?.data?.detail || 'Erro ao excluir campo'),
  })

  const reorderMutation = useMutation({
    mutationFn: (fields: { id: number; ordem: number }[]) => formFieldsApi.reorder(pageId, fields),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['form-fields', pageId] }),
  })

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id || !data) return

    const fields = [...data.campos]
    const oldIndex = fields.findIndex((f) => f.id === active.id)
    const newIndex = fields.findIndex((f) => f.id === over.id)
    const newFields = arrayMove(fields, oldIndex, newIndex)
    const updates = newFields.map((field, index) => ({ id: field.id, ordem: index + 1 }))
    reorderMutation.mutate(updates)
  }

  // Processar dados ANTES de qualquer return
  const fields = data?.campos || []

  // Extrair valores únicos para autocomplete
  const uniqueValues = useMemo(() => {
    const tipos = new Set<string>()
    const planilhas = new Set<string>()
    const celulas = new Set<string>()

    fields.forEach((field) => {
      tipos.add(field.tipo)
      if (field.configuracao?.excel_mapping) {
        field.configuracao.excel_mapping.forEach((mapping: any) => {
          if (mapping.planilha) planilhas.add(mapping.planilha)
          if (mapping.celula) celulas.add(mapping.celula)
        })
      }
    })

    return {
      tipos: Array.from(tipos).sort(),
      planilhas: Array.from(planilhas).sort(),
      celulas: Array.from(celulas).sort()
    }
  }, [fields])

  // Aplicar filtros
  const filteredFields = useMemo(() => {
    return fields.filter((field) => {
      // Filtro por nome (rotulo ou título do separador)
      const nome = field.tipo === 'separator' ? field.configuracao?.titulo : field.rotulo
      if (filterNome && !nome?.toLowerCase().includes(filterNome.toLowerCase())) {
        return false
      }

      // Filtro por tipo
      if (filterTipo && field.tipo !== filterTipo) {
        return false
      }

      // Filtro por planilha
      if (filterPlanilha) {
        const mappings = field.configuracao?.excel_mapping || []

        // Caso especial: filtrar campos SEM mapeamento
        if (filterPlanilha === '(Sem Informação)') {
          if (mappings.length > 0) return false
        } else {
          // Filtro normal: buscar pela planilha
          const hasMatch = mappings.some((mapping: any) =>
            mapping.planilha?.toLowerCase().includes(filterPlanilha.toLowerCase())
          )
          if (!hasMatch) return false
        }
      }

      // Filtro por célula
      if (filterCelula) {
        const mappings = field.configuracao?.excel_mapping || []

        // Caso especial: filtrar campos SEM mapeamento
        if (filterCelula === '(Sem Informação)') {
          if (mappings.length > 0) return false
        } else {
          // Filtro normal: buscar pela célula
          const hasMatch = mappings.some((mapping: any) =>
            mapping.celula?.toLowerCase().includes(filterCelula.toLowerCase())
          )
          if (!hasMatch) return false
        }
      }

      return true
    })
  }, [fields, filterNome, filterTipo, filterPlanilha, filterCelula])

  const hasActiveFilters = filterNome || filterTipo || filterPlanilha || filterCelula

  const clearFilters = () => {
    setFilterNome('')
    setFilterTipo('')
    setFilterPlanilha('')
    setFilterCelula('')
  }

  // Early return DEPOIS de todos os hooks
  if (isLoading) return <div className="text-center py-8 text-gray-500">Carregando campos...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Campos da Página</h2>
          <p className="text-sm text-gray-500 mt-1">
            {filteredFields.length} de {fields.length} item(s)
            {hasActiveFilters && ' (filtrado)'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => { setEditingSeparator(null); setIsSeparatorModalOpen(true) }} variant="outline">
            <Minus className="h-4 w-4 mr-2" />Novo Separador
          </Button>
          <Button onClick={() => { setEditingField(null); setIsModalOpen(true) }}>
            <Plus className="h-4 w-4 mr-2" />Novo Campo
          </Button>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <Label className="text-sm font-semibold">Filtros</Label>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="h-4 w-4 mr-1" />
              Limpar filtros
            </Button>
          )}
        </div>
        <div className="grid grid-cols-4 gap-3">
          <div className="space-y-1">
            <Label className="text-xs text-gray-600">Nome do Campo</Label>
            <Input
              value={filterNome}
              onChange={(e) => setFilterNome(e.target.value)}
              placeholder="Filtrar por nome..."
              className="text-sm"
            />
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-gray-600">Tipo</Label>
            <Input
              value={filterTipo}
              onChange={(e) => setFilterTipo(e.target.value)}
              placeholder="Filtrar por tipo..."
              className="text-sm"
              list="tipos-list"
            />
            <datalist id="tipos-list">
              {uniqueValues.tipos.map((tipo) => (
                <option key={tipo} value={tipo} />
              ))}
            </datalist>
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-gray-600">Planilha</Label>
            <Input
              value={filterPlanilha}
              onChange={(e) => setFilterPlanilha(e.target.value)}
              placeholder="Filtrar por planilha..."
              className="text-sm"
              list="planilhas-list"
            />
            <datalist id="planilhas-list">
              <option value="(Sem Informação)" />
              {uniqueValues.planilhas.map((planilha) => (
                <option key={planilha} value={planilha} />
              ))}
            </datalist>
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-gray-600">Célula</Label>
            <Input
              value={filterCelula}
              onChange={(e) => setFilterCelula(e.target.value)}
              placeholder="Filtrar por célula..."
              className="text-sm"
              list="celulas-list"
            />
            <datalist id="celulas-list">
              <option value="(Sem Informação)" />
              {uniqueValues.celulas.map((celula) => (
                <option key={celula} value={celula} />
              ))}
            </datalist>
          </div>
        </div>
      </div>

      {fields.length === 0 ? (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <p className="text-gray-500 mb-4">Nenhum campo criado ainda</p>
          <Button onClick={() => setIsModalOpen(true)} variant="outline">
            <Plus className="h-4 w-4 mr-2" />Criar Primeiro Campo
          </Button>
        </div>
      ) : filteredFields.length === 0 ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <p className="text-yellow-700 mb-3">Nenhum campo corresponde aos filtros aplicados</p>
          <Button onClick={clearFilters} variant="outline" size="sm">
            <X className="h-4 w-4 mr-1" />
            Limpar filtros
          </Button>
        </div>
      ) : (
        <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={filteredFields.map((f) => f.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {filteredFields.map((field) => (
                <SortableFieldItem
                  key={field.id}
                  field={field}
                  onEdit={(f: FormField) => { setEditingField(f); setIsModalOpen(true) }}
                  onEditSeparator={(f: FormField) => { setEditingSeparator(f); setIsSeparatorModalOpen(true) }}
                  onDelete={(f: FormField) => {
                    const itemType = f.tipo === 'separator' ? 'separador' : 'campo'
                    const itemName = f.tipo === 'separator' ? f.configuracao?.titulo : f.rotulo
                    if (confirm(`Excluir ${itemType} "${itemName}"?`)) deleteMutation.mutate(f.id)
                  }}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      <FormFieldModal pageId={pageId} field={editingField} open={isModalOpen} onOpenChange={(open) => { setIsModalOpen(open); if (!open) setEditingField(null) }} existingFields={fields} templateId={templateId} />

      <FormSeparatorModal pageId={pageId} separator={editingSeparator} open={isSeparatorModalOpen} onOpenChange={(open) => { setIsSeparatorModalOpen(open); if (!open) setEditingSeparator(null) }} existingFields={fields} />
    </div>
  )
}

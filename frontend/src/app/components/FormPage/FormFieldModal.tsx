/**
 * FormFieldModal - Modal Dinâmico para Criar/Editar Campo
 * O formulário muda conforme o tipo de campo selecionado
 */

import { useState, useEffect, useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { formFieldsApi, type FormField, type FormFieldCreate } from '@/lib/api/formFields'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api/client'

interface FormFieldModalProps {
  pageId: number
  field: FormField | null
  open: boolean
  onOpenChange: (open: boolean) => void
  existingFields: FormField[]
  templateId?: number
}

// Tipo para Data Mapping
interface ExcelMapping {
  planilha: string
  celula: string
}

// Configurações padrão para cada tipo de campo
const defaultConfigs: Record<string, any> = {
  textbox: { format_validation: 'none', min_characters: 0, max_characters: 255, require: false, read_only: false, unique: false, default_value: '', excel_mapping: [] },
  date: { type: 'date', date_format: 'dd_mm_yyyy', require: false, read_only: false, default_value: '', excel_mapping: [] },
  number: { min_value: null, max_value: null, decimal_places: 0, require: false, read_only: false, default_value: '', excel_mapping: [] },
  yes_no: { export_yes_no_value: 'sim_nao', default_value: '', require: false, read_only: false, excel_mapping: [] },
  choice: { options: [], allow_multiple: false, require: false, read_only: false, default_value: '', excel_mapping: [] },
  lookup: {
    source_type: 'view',
    target_table: null,
    target_view: null,
    target_list_id: null,
    target_template_id: null,
    display_field: 'label',
    value_field: 'id',
    export_lookup_value: 'label',
    use_autocomplete: true,
    dependent_filter: { enabled: false, filter_by_field: null, filter_by_page: null },
    require: false,
    read_only: false,
    default_value: '',
    excel_mapping: []
  },
}

export default function FormFieldModal({ pageId, field, open, onOpenChange, existingFields, templateId }: FormFieldModalProps) {
  const [formData, setFormData] = useState<FormFieldCreate>({
    rotulo: '',
    ordem: 1,
    tipo: 'textbox',
    configuracao: defaultConfigs.textbox,
  })

  const queryClient = useQueryClient()

  // Query para buscar views disponíveis
  const { data: availableViews = [] } = useQuery({
    queryKey: ['lookup-views'],
    queryFn: async () => {
      const response = await api.get('/lookup/views')
      return response.data || []
    },
    enabled: open && formData.tipo === 'lookup' && formData.configuracao?.source_type === 'view',
  })

  // Query para buscar listas lookup disponíveis
  const { data: lookupLists = [] } = useQuery({
    queryKey: ['lookup-lists'],
    queryFn: async () => {
      const response = await api.get('/lookup-lists')
      return response.data.listas || []
    },
    enabled: open && formData.tipo === 'lookup' && formData.configuracao?.source_type === 'list',
  })

  // Query para buscar formulários disponíveis (para Lookup)
  const { data: formularios = [], isLoading: isLoadingFormularios } = useQuery({
    queryKey: ['formularios-list'],
    queryFn: async () => {
      const response = await api.get('/formularios')
      const items = response.data.items || []
      return items
    },
    enabled: open && formData.tipo === 'lookup' && formData.configuracao?.source_type === 'form',
  })

  // Query para buscar todos os campos do formulário (para autocomplete de planilhas)
  const { data: allTemplateFields = [], isLoading: isLoadingFields } = useQuery({
    queryKey: ['formulario-all-fields', templateId],
    queryFn: async () => {
      if (!templateId) return []
      const response = await api.get(`/formularios/${templateId}/fields`)
      return response.data
    },
    enabled: open && !!templateId,
  })

  // Extrair planilhas únicas de todos os campos
  const availableSheets = useMemo(() => {
    const sheets = new Set<string>()
    let fieldsWithMapping = 0
    allTemplateFields.forEach((field: any) => {
      if (field.configuracao?.excel_mapping) {
        fieldsWithMapping++
        field.configuracao.excel_mapping.forEach((mapping: ExcelMapping) => {
          if (mapping.planilha) {
            sheets.add(mapping.planilha)
          }
        })
      }
    })
    return Array.from(sheets).sort()
  }, [allTemplateFields])

  // Query para buscar campos do formulário selecionado (para Lookup)
  const { data: targetFields = [] } = useQuery({
    queryKey: ['formulario-fields', formData.configuracao?.target_template_id],
    queryFn: async () => {
      const response = await api.get(`/formularios/${formData.configuracao.target_template_id}/fields`)
      return response.data
    },
    enabled: open && formData.tipo === 'lookup' && !!formData.configuracao?.target_template_id,
  })

  // Calcular próxima ordem disponível
  const getNextOrder = () => {
    if (existingFields.length === 0) return 1
    const maxOrder = Math.max(...existingFields.map(f => f.ordem))
    return maxOrder + 1
  }

  useEffect(() => {
    if (field) {
      setFormData({ rotulo: field.rotulo, ordem: field.ordem, tipo: field.tipo, configuracao: field.configuracao })
    } else {
      setFormData({ rotulo: '', ordem: getNextOrder(), tipo: 'textbox', configuracao: defaultConfigs.textbox })
    }
  }, [field, open, existingFields])

  const createMutation = useMutation({
    mutationFn: (data: FormFieldCreate) => formFieldsApi.create(pageId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-fields', pageId] })
      onOpenChange(false)
    },
    onError: (error: any) => alert(error.response?.data?.detail || 'Erro ao criar campo'),
  })

  const updateMutation = useMutation({
    mutationFn: (data: FormFieldCreate) => formFieldsApi.update(pageId, field!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form-fields', pageId] })
      onOpenChange(false)
    },
    onError: (error: any) => alert(error.response?.data?.detail || 'Erro ao atualizar campo'),
  })

  const handleTypeChange = (newType: string) => {
    // Preservar excel_mapping ao trocar tipo
    const currentExcelMapping = formData.configuracao?.excel_mapping || []
    const newConfig = {
      ...defaultConfigs[newType],
      excel_mapping: currentExcelMapping
    }

    // Garantir que lookup sempre tenha source_type definido
    if (newType === 'lookup' && !newConfig.source_type) {
      newConfig.source_type = 'view'
    }

    setFormData({
      ...formData,
      tipo: newType,
      configuracao: newConfig
    })
  }

  const handleConfigChange = (key: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      configuracao: { ...prev.configuracao, [key]: value }
    }))
  }

  // Funções para gerenciar Excel Mapping
  const excelMappings: ExcelMapping[] = formData.configuracao?.excel_mapping || []

  const addExcelMapping = () => {
    const newMappings = [...excelMappings, { planilha: '', celula: '' }]
    handleConfigChange('excel_mapping', newMappings)
  }

  const updateExcelMapping = (index: number, field: 'planilha' | 'celula', value: string) => {
    const newMappings = [...excelMappings]
    newMappings[index][field] = value.toUpperCase() // Sempre em maiúsculas
    handleConfigChange('excel_mapping', newMappings)
  }

  const removeExcelMapping = (index: number) => {
    const newMappings = excelMappings.filter((_, i) => i !== index)
    handleConfigChange('excel_mapping', newMappings)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validar mapeamentos Excel (remover vazios)
    const validMappings = excelMappings.filter(
      (m) => m.planilha.trim() !== '' && m.celula.trim() !== ''
    )

    // Atualizar formData com mappings válidos
    const finalFormData = {
      ...formData,
      configuracao: {
        ...formData.configuracao,
        excel_mapping: validMappings,
      },
    }

    if (field) {
      updateMutation.mutate(finalFormData)
    } else {
      createMutation.mutate(finalFormData)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{field ? 'Editar Campo' : 'Novo Campo'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Campos comuns */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Nome do Campo *</Label>
              <Input value={formData.rotulo} onChange={(e) => setFormData({ ...formData, rotulo: e.target.value })} required maxLength={100} />
            </div>
            <div className="space-y-2">
              <Label>Ordem *</Label>
              <Input type="number" value={formData.ordem} onChange={(e) => setFormData({ ...formData, ordem: parseInt(e.target.value) })} required min={1} />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Tipo de Campo *</Label>
            <select
              value={formData.tipo}
              onChange={(e) => handleTypeChange(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="textbox">Textbox</option>
              <option value="date">Date</option>
              <option value="number">Number</option>
              <option value="yes_no">Yes/No</option>
              <option value="choice">Choice</option>
              <option value="lookup">Lookup</option>
            </select>
          </div>

          {/* Configurações específicas por tipo */}
          <div className="border-t pt-4">
            <h3 className="font-semibold mb-3">Configurações do Campo</h3>

            {formData.tipo === 'textbox' && (
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label>Validação de Formato</Label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" value={formData.configuracao?.format_validation} onChange={(e) => handleConfigChange('format_validation', e.target.value)}>
                    <option value="none">Nenhuma</option>
                    <option value="uppercase">Caixa Alta</option>
                    <option value="email">E-mail</option>
                    <option value="phone">Telefone</option>
                    <option value="cpf">CPF</option>
                    <option value="cep">CEP</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Min. Caracteres</Label>
                    <Input type="number" value={formData.configuracao?.min_characters} onChange={(e) => handleConfigChange('min_characters', parseInt(e.target.value))} min={0} />
                  </div>
                  <div className="space-y-2">
                    <Label>Max. Caracteres</Label>
                    <Input type="number" value={formData.configuracao?.max_characters} onChange={(e) => handleConfigChange('max_characters', parseInt(e.target.value))} min={1} />
                  </div>
                </div>
              </div>
            )}

            {formData.tipo === 'date' && (
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label>Tipo de Data</Label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" value={formData.configuracao?.type} onChange={(e) => handleConfigChange('type', e.target.value)}>
                    <option value="date">Date</option>
                    <option value="datetime">Date & Time</option>
                    <option value="time">Time</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Formato da Data</Label>
                  <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" value={formData.configuracao?.date_format || 'dd_mm_yyyy'} onChange={(e) => handleConfigChange('date_format', e.target.value)}>
                    <option value="dd_mm_yyyy">DD/MM/YYYY</option>
                    <option value="yyyy_mm_dd">YYYY/MM/DD</option>
                    <option value="dd_mmm">DD-MMM</option>
                  </select>
                  <p className="text-xs text-gray-500">
                    Formato de exibição da data no relatório e exportações
                  </p>
                </div>
              </div>
            )}

            {formData.tipo === 'yes_no' && (
              <div className="space-y-2">
                <Label>Como Exportar</Label>
                <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2" value={formData.configuracao?.export_yes_no_value || 'sim_nao'} onChange={(e) => handleConfigChange('export_yes_no_value', e.target.value)}>
                  <option value="sim_nao">Sim / Não</option>
                  <option value="yes_no">Yes / No</option>
                  <option value="true_false">true / false</option>
                  <option value="um_zero">1 / 0</option>
                  <option value="s_n">S / N</option>
                  <option value="simbolos">■ / □</option>
                </select>
                <p className="text-xs text-gray-500">
                  Define como o valor será gravado na exportação (Excel/PDF)
                </p>
              </div>
            )}

            {formData.tipo === 'choice' && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Opções *</Label>
                  <div className="space-y-2">
                    {(formData.configuracao?.options || []).map((option: string, index: number) => (
                      <div key={index} className="flex gap-2">
                        <Input
                          value={option}
                          onChange={(e) => {
                            const newOptions = [...(formData.configuracao?.options || [])]
                            newOptions[index] = e.target.value
                            handleConfigChange('options', newOptions)
                          }}
                          placeholder={`Opção ${index + 1}`}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            const newOptions = (formData.configuracao?.options || []).filter((_: any, i: number) => i !== index)
                            handleConfigChange('options', newOptions)
                          }}
                          className="text-red-500 hover:text-red-700"
                        >
                          ×
                        </Button>
                      </div>
                    ))}
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const newOptions = [...(formData.configuracao?.options || []), '']
                      handleConfigChange('options', newOptions)
                    }}
                  >
                    + Adicionar Opção
                  </Button>
                  <p className="text-xs text-gray-500">
                    Lista de valores que o usuário poderá escolher
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.configuracao?.allow_multiple || false}
                      onChange={(e) => handleConfigChange('allow_multiple', e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm">Permitir seleção múltipla</span>
                  </label>
                  <p className="text-xs text-gray-500">
                    Se marcado, usuário pode selecionar mais de uma opção
                  </p>
                </div>
              </div>
            )}

            {formData.tipo === 'lookup' && (
              <div className="space-y-4">
                {/* Tipo de Origem */}
                <div className="space-y-2">
                  <Label>Tipo de Origem *</Label>
                  <select
                    value={formData.configuracao?.source_type || 'view'}
                    onChange={(e) => {
                      const value = e.target.value
                      setFormData(prev => ({
                        ...prev,
                        configuracao: {
                          ...prev.configuracao,
                          source_type: value,
                          target_view: null,
                          target_list_id: null,
                          target_template_id: null,
                          display_field: 'label',
                          value_field: 'id',
                          export_lookup_value: prev.configuracao?.export_lookup_value || 'label',
                          dependent_filter: { enabled: false, filter_by_field: null, filter_by_page: null }
                        }
                      }))
                    }}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    <option value="list">Lista</option>
                    <option value="view">View</option>
                    <option value="form">Formulário</option>
                  </select>
                  <p className="text-xs text-gray-500">
                    Lista/View: estrutura padrão (id, label, filter) | Formulário: campos customizados
                  </p>
                </div>

                {/* Valor para exportação no Excel/PDF */}
                <div className="space-y-2">
                  <Label>Como Exportar</Label>
                  <select
                    value={formData.configuracao?.export_lookup_value || 'label'}
                    onChange={(e) => handleConfigChange('export_lookup_value', e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    <option value="label">Label (padrão)</option>
                    <option value="id">ID</option>
                    <option value="id_label">ID | Label</option>
                  </select>
                  <p className="text-xs text-gray-500">
                    Define qual valor do lookup será escrito na exportação do relatório
                  </p>
                </div>

                {/* ORIGEM: Lista */}
                {formData.configuracao?.source_type === 'list' && (
                  <div className="space-y-2">
                    <Label>Lista *</Label>
                    <select
                      value={formData.configuracao?.target_list_id || ''}
                      onChange={(e) => handleConfigChange('target_list_id', e.target.value)}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      <option value="">Selecione a lista...</option>
                      {lookupLists.map((list: any) => (
                        <option key={list.id} value={list.id}>
                          {list.nome}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500">
                      Listas cadastradas no sistema (estrutura: id, label, filter)
                    </p>
                  </div>
                )}

                {/* ORIGEM: View */}
                {formData.configuracao?.source_type === 'view' && (
                  <div className="space-y-2">
                    <Label>View *</Label>
                    <select
                      value={formData.configuracao?.target_view || ''}
                      onChange={(e) => handleConfigChange('target_view', e.target.value)}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      <option value="">Selecione a view...</option>
                      {availableViews.map((view) => (
                        <option key={view.value} value={view.value}>
                          {view.label}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500">
                      Views homologadas do banco (estrutura: id, label, filter)
                    </p>
                  </div>
                )}

                {/* ORIGEM: Formulário */}
                {formData.configuracao?.source_type === 'form' && (
                  <>
                    <div className="space-y-2">
                      <Label>Formulário de Origem *</Label>
                      <select
                        value={formData.configuracao?.target_template_id || ''}
                        onChange={(e) => {
                          const value = e.target.value ? parseInt(e.target.value) : null
                          setFormData(prev => ({
                            ...prev,
                            configuracao: {
                              ...prev.configuracao,
                              target_template_id: value,
                              display_field: ''
                            }
                          }))
                        }}
                        disabled={isLoadingFormularios}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <option value="">
                          {isLoadingFormularios ? 'Carregando formulários...' : 'Selecione o formulário...'}
                        </option>
                        {formularios.map((form: any) => (
                          <option key={form.id} value={form.id}>
                            {form.nome}
                          </option>
                        ))}
                      </select>
                      <p className="text-xs text-gray-500">
                        Formulário de onde os dados serão buscados ({formularios.length} disponíveis)
                      </p>
                    </div>

                    {formData.configuracao?.target_template_id && (
                      <>
                        <div className="space-y-2">
                          <Label>Campo a Exibir *</Label>
                          <select
                            value={formData.configuracao?.display_field || ''}
                            onChange={(e) => handleConfigChange('display_field', e.target.value)}
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                          >
                            <option value="">Selecione o campo...</option>
                            {targetFields.map((field: any) => (
                              <option key={field.rotulo} value={field.rotulo}>
                                {field.rotulo}
                              </option>
                            ))}
                          </select>
                          <p className="text-xs text-gray-500">
                            Campo que será exibido na lista de opções
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label>Campo Valor</Label>
                          <Input
                            value={formData.configuracao?.value_field || 'id'}
                            onChange={(e) => handleConfigChange('value_field', e.target.value)}
                            placeholder="id"
                          />
                          <p className="text-xs text-gray-500">
                            Campo usado como valor (geralmente "id")
                          </p>
                        </div>
                      </>
                    )}
                  </>
                )}

                {/* Configurações comuns para Lista e View */}
                {(formData.configuracao?.source_type === 'list' || formData.configuracao?.source_type === 'view') && (
                  <>
                    {/* Autocomplete */}
                    <div className="space-y-2 pt-3 border-t">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.configuracao?.use_autocomplete !== false}
                          onChange={(e) => handleConfigChange('use_autocomplete', e.target.checked)}
                          className="rounded"
                        />
                        <span className="text-sm font-medium">Usar Autocomplete</span>
                      </label>
                      <p className="text-xs text-gray-500">
                        Recomendado para listas/views com muitos valores (busca dinâmica)
                      </p>
                    </div>

                    {/* Filtro Dependente */}
                    <div className="space-y-2 pt-3 border-t">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.configuracao?.dependent_filter?.enabled || false}
                          onChange={(e) => handleConfigChange('dependent_filter', {
                            enabled: e.target.checked,
                            filter_by_field: null,
                            filter_by_page: null
                          })}
                          className="rounded"
                        />
                        <span className="text-sm font-medium">Filtrar por outro campo da tela</span>
                      </label>
                      <p className="text-xs text-gray-500">
                        Campo Filter será usado para filtrar dinamicamente as opções
                      </p>
                    </div>

                    {formData.configuracao?.dependent_filter?.enabled && (
                      <div className="space-y-2 ml-6 border-l-2 border-blue-300 pl-4">
                        <Label>Campo de Filtro *</Label>
                        <select
                          value={formData.configuracao?.dependent_filter?.filter_by_field || ''}
                          onChange={(e) => handleConfigChange('dependent_filter', {
                            ...formData.configuracao?.dependent_filter,
                            filter_by_field: e.target.value
                          })}
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                        >
                          <option value="">Selecione o campo...</option>
                          {existingFields
                            .filter(f => f.ordem < (formData.ordem || 9999))
                            .map(field => (
                              <option key={field.id} value={field.rotulo}>
                                {field.rotulo}
                              </option>
                            ))}
                        </select>
                        <p className="text-xs text-gray-500">
                          Valor deste campo será usado para filtrar (campo Filter da lista/view)
                        </p>
                        <div className="bg-blue-50 border border-blue-200 rounded p-2 mt-2">
                          <p className="text-xs text-blue-900">
                            <strong>Exemplo:</strong> Se campo "Região" = "Sudeste", apenas estados com Filter = "Sudeste" aparecerão
                          </p>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Valor Padrão */}
            <div className="space-y-2 mt-4 pt-4 border-t">
              <Label>Valor Padrão</Label>
              <Input
                value={formData.configuracao?.default_value || ''}
                onChange={(e) => handleConfigChange('default_value', e.target.value)}
                placeholder="Digite o valor padrão ou use valores especiais abaixo"
                maxLength={255}
              />
              <div className="flex gap-2 flex-wrap">
                <button
                  type="button"
                  onClick={() => handleConfigChange('default_value', '{{usuario.login}}')}
                  className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 border border-blue-200"
                  title="Inserir login do usuário"
                >
                  + Login do Usuário
                </button>
                <button
                  type="button"
                  onClick={() => handleConfigChange('default_value', '{{usuario.nome}}')}
                  className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 border border-blue-200"
                  title="Inserir nome do usuário"
                >
                  + Nome do Usuário
                </button>
                <button
                  type="button"
                  onClick={() => handleConfigChange('default_value', '{{relatorio.numero}}')}
                  className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 border border-blue-200"
                  title="Inserir número do relatório"
                >
                  + Número do Relatório
                </button>
              </div>
              <div className="text-xs text-gray-500 space-y-1">
                <p>Valor que será pré-preenchido quando o usuário criar um novo relatório.</p>
                <p className="text-gray-400 italic">
                  Valores especiais: <code className="bg-gray-100 px-1 rounded">{'{{usuario.login}}'}</code>,
                  <code className="bg-gray-100 px-1 rounded ml-1">{'{{usuario.nome}}'}</code>,
                  <code className="bg-gray-100 px-1 rounded ml-1">{'{{relatorio.numero}}'}</code>
                </p>
              </div>
            </div>

            {/* Atributos comuns */}
            <div className="flex gap-4 mt-4 pt-4 border-t">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={formData.configuracao?.require || false} onChange={(e) => handleConfigChange('require', e.target.checked)} className="rounded" />
                <span className="text-sm">Obrigatório</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={formData.configuracao?.read_only || false} onChange={(e) => handleConfigChange('read_only', e.target.checked)} className="rounded" />
                <span className="text-sm">Somente Leitura</span>
              </label>
              {formData.tipo === 'textbox' && (
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={formData.configuracao?.unique || false} onChange={(e) => handleConfigChange('unique', e.target.checked)} className="rounded" />
                  <span className="text-sm">Único</span>
                </label>
              )}
            </div>
          </div>

          {/* Data Mapping Excel */}
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-semibold">Data Mapping - Excel</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Defina em quais células do Excel este campo será gravado
                </p>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={addExcelMapping}>
                + Adicionar Mapeamento
              </Button>
            </div>

            {excelMappings.length === 0 ? (
              <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-6 text-center">
                <p className="text-sm text-gray-500">
                  Nenhum mapeamento definido. Clique em "Adicionar Mapeamento" para começar.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {excelMappings.map((mapping, index) => (
                  <div
                    key={index}
                    className="flex gap-3 items-start p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-semibold">
                      {index + 1}
                    </div>
                    <div className="flex-1 grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label className="text-xs">Planilha</Label>
                        <Input
                          value={mapping.planilha}
                          onChange={(e) => updateExcelMapping(index, 'planilha', e.target.value)}
                          placeholder="Ex: Dados, Resumo, Sheet1"
                          className="text-sm"
                          list={`sheet-options-${index}`}
                        />
                        <datalist id={`sheet-options-${index}`}>
                          {availableSheets.map((sheet) => (
                            <option key={sheet} value={sheet} />
                          ))}
                        </datalist>
                        {isLoadingFields ? (
                          <p className="text-xs text-gray-500">Carregando planilhas...</p>
                        ) : availableSheets.length > 0 ? (
                          <p className="text-xs text-green-600 font-medium">
                            ✓ {availableSheets.length} planilha(s) disponível(is)
                          </p>
                        ) : (
                          <p className="text-xs text-gray-500">
                            Nenhuma planilha encontrada
                          </p>
                        )}
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Célula</Label>
                        <Input
                          value={mapping.celula}
                          onChange={(e) => updateExcelMapping(index, 'celula', e.target.value)}
                          placeholder="Ex: A1, B5, ZW34"
                          className="text-sm font-mono"
                          maxLength={10}
                        />
                      </div>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeExcelMapping(index)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    >
                      ×
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {excelMappings.length > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                💡 O mesmo campo pode ser mapeado para múltiplas células/planilhas
              </p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>Cancelar</Button>
            <Button type="submit" disabled={isPending}>{isPending ? 'Salvando...' : field ? 'Atualizar' : 'Criar'}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

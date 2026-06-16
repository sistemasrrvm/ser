/**
 * ReportWizardPage - Preenchimento do formulário dinâmico
 * Sprint 004 - WIZARD (renderização dinâmica de páginas/campos)
 */

import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reportsApi } from '@/lib/api/reports'
import { formPagesApi } from '@/lib/api/formPages'
import { formFieldsApi } from '@/lib/api/formFields'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Autocomplete } from '@/components/ui/autocomplete'
import { api } from '@/lib/api/client'
import { useAuth } from '@/lib/auth/AuthContext'
import { getReportStatusLabel } from '@/lib/reports/statusLabels'
import {
  canEditReport,
  canExportReportExcel,
  canFinalizeReport,
  canApproveReport,
  canRequestCorrection,
  canViewReport,
} from '@/lib/reports/reportPermissions'
import { LOOKUP_COMBO_MAX_ITEMS } from '@/lib/lookup/constants'

const isSimpleLookupCombo = (field: { configuracao?: { use_autocomplete?: boolean } }) =>
  field.configuracao?.use_autocomplete === false

/** Params da API de view lookup; combo simples (#300) pede até 1000 itens. */
const viewLookupRequestParams = (
  field: { configuracao?: { use_autocomplete?: boolean } },
  extra?: { filter?: unknown; id?: unknown; search?: string }
) => {
  const params: Record<string, unknown> = { ...extra }
  if (isSimpleLookupCombo(field)) {
    params.page_size = LOOKUP_COMBO_MAX_ITEMS
  }
  return params
}

/** Formata valor de data conforme config date_format do campo */
function formatDateValue(value: string | null | undefined, dateFormat: string | undefined): string {
  if (!value || typeof value !== 'string') return value || '-'
  const s = value.trim().split('T')[0] // YYYY-MM-DD part
  if (!s) return '-'
  const parts = s.split('-')
  if (parts.length !== 3) return value
  const [y, m, d] = parts
  const monthNames = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  const monthIdx = parseInt(m, 10) - 1
  const mmm = monthIdx >= 0 && monthIdx < 12 ? monthNames[monthIdx] : m
  switch (dateFormat) {
    case 'yyyy_mm_dd': return `${y}/${m}/${d}`
    case 'dd_mmm': return `${d}-${mmm}`
    case 'dd_mm_yyyy':
    default: return `${d}/${m}/${y}`
  }
}

const wizardFieldDomId = (fieldId: number) => `wizard-field-${fieldId}`

function isRequiredFieldEmpty(field: { id: number; tipo: string; configuracao?: Record<string, unknown> }, formData: Record<string, unknown>): boolean {
  const value = formData[`campo_${field.id}`]
  if (field.tipo === 'yes_no') {
    return value !== 'true' && value !== 'false'
  }
  if (field.tipo === 'choice' && field.configuracao?.allow_multiple) {
    const selected = Array.isArray(value) ? value : value ? [value] : []
    return selected.length === 0
  }
  if (field.tipo === 'number') {
    return value === undefined || value === null || value === ''
  }
  return value === undefined || value === null || value === ''
}

function focusWizardField(fieldId: number) {
  const focusTarget =
    document.getElementById(wizardFieldDomId(fieldId)) ??
    document
      .getElementById(`wizard-field-wrap-${fieldId}`)
      ?.querySelector<HTMLElement>(
        'input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])'
      )

  if (!focusTarget) return

  focusTarget.focus({ preventScroll: false })
  focusTarget.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

export default function ReportWizardPage() {
  const { id } = useParams<{ id: string }>()
  const reportId = Number(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()

  const [currentPageIndex, setCurrentPageIndex] = useState(0)
  const [formData, setFormData] = useState<Record<string, any>>({})
  const [lookupOptions, setLookupOptions] = useState<Record<number, Array<{ label: string; value: any }>>>({})
  const [lookupTotalCounts, setLookupTotalCounts] = useState<Record<number, number>>({})
  const [lookupSelectedLabels, setLookupSelectedLabels] = useState<Record<number, string>>({})
  const [showHistorico, setShowHistorico] = useState(false)
  const [correctionModalOpen, setCorrectionModalOpen] = useState(false)
  const [correctionDesc, setCorrectionDesc] = useState('')
  const restoredLookupLabelsRef = useRef<Set<number>>(new Set())
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null)

  const lookupLabelKey = (fieldId: number) => `campo_${fieldId}_label`

  // Query: Buscar relatório
  const { data: report, isLoading: loadingReport, error: reportError } = useQuery({
    queryKey: ['report', reportId],
    queryFn: () => reportsApi.get(reportId),
    retry: false,
  })

  const reportPermCtx = report
    ? { status: report.status, tecnico_id: report.tecnico_id }
    : null
  const canEdit = !!(user && reportPermCtx && canEditReport(user, reportPermCtx))
  const canExportExcel = !!(user && reportPermCtx && canExportReportExcel(user, reportPermCtx))
  const canFinalize = !!(user && reportPermCtx && canFinalizeReport(user, reportPermCtx))
  const canApprove = !!(user && reportPermCtx && canApproveReport(user, reportPermCtx))
  const canRequestCorr = !!(user && reportPermCtx && canRequestCorrection(user, reportPermCtx))
  const canViewHistorico = !!(user && reportPermCtx && canViewReport(user, reportPermCtx))
  const formReadOnly = !canEdit

  const { data: correcoesData, isLoading: loadingCorrecoes } = useQuery({
    queryKey: ['report-correcoes', reportId],
    queryFn: () => reportsApi.listCorrecoes(reportId),
    enabled: !!report && canViewHistorico,
  })

  // Query: Buscar páginas do template
  const { data: pagesData, isLoading: loadingPages } = useQuery({
    queryKey: ['form-pages', report?.form_template_id],
    queryFn: () => formPagesApi.list(report!.form_template_id),
    enabled: !!report,
  })

  // Query: Buscar campos da página atual
  const currentPage = pagesData?.paginas?.[currentPageIndex]
  const { data: fieldsData, isLoading: loadingFields } = useQuery({
    queryKey: ['form-fields', currentPage?.id],
    queryFn: () => formFieldsApi.list(currentPage!.id),
    enabled: !!currentPage,
  })

  // Carregar respostas existentes e labels de lookup persistidos
  useEffect(() => {
    if (report?.respostas) {
      setFormData(report.respostas)
      const labels: Record<number, string> = {}
      for (const [key, val] of Object.entries(report.respostas)) {
        const match = key.match(/^campo_(\d+)_label$/)
        if (match && val) {
          labels[Number(match[1])] = String(val)
        }
      }
      if (Object.keys(labels).length > 0) {
        setLookupSelectedLabels((prev) => ({ ...prev, ...labels }))
      }
    }
  }, [report])

  // Restaurar labels de lookup salvos sem _label (rascunhos antigos)
  useEffect(() => {
    const fields = fieldsData?.campos || []
    if (fields.length === 0) return

    const restoreMissingLabels = async () => {
      for (const field of fields) {
        if (field.tipo !== 'lookup') continue
        const fieldValue = formData[`campo_${field.id}`]
        if (!fieldValue) continue
        if (restoredLookupLabelsRef.current.has(field.id)) continue

        const savedLabel = formData[lookupLabelKey(field.id)]
        if (savedLabel) {
          restoredLookupLabelsRef.current.add(field.id)
          setLookupSelectedLabels((prev) => ({ ...prev, [field.id]: String(savedLabel) }))
          continue
        }

        restoredLookupLabelsRef.current.add(field.id)
        const config = field.configuracao

        try {
          let label: string | null = null

          if (config?.source_type === 'view' && config?.target_view) {
            const response = await api.get(`/lookup/views/${config.target_view}/data`, {
              params: { id: fieldValue, page_size: 1 },
            })
            label = response.data.items?.[0]?.label ?? null
          } else if (config?.source_type === 'list' && config?.target_list_id) {
            const response = await api.get(`/lookup-lists/${config.target_list_id}/options`)
            const opcoes = response.data?.opcoes || []
            const found = opcoes.find((item: any) => String(item.id) === String(fieldValue))
            label = found?.label ?? null
          } else if (config?.source_type === 'form' && config?.target_template_id) {
            const response = await api.get(
              `/formularios/${config.target_template_id}/lookup-options`,
              {
                params: {
                  display_field: config.display_field,
                  value_field: config.value_field || 'id',
                },
              }
            )
            const found = (response.data || []).find(
              (item: any) => String(item.value) === String(fieldValue)
            )
            label = found?.label ?? null
          }

          if (label) {
            setLookupSelectedLabels((prev) => ({ ...prev, [field.id]: label }))
          }
        } catch (error) {
          console.error(`Erro ao restaurar label do lookup ${field.id}:`, error)
        }
      }
    }

    restoreMissingLabels()
  }, [fieldsData, formData])

  // Função para carregar opções de um lookup específico (LAZY)
  const loadLookupOptionsForField = async (field: any) => {
    // Se já carregou, não carregar novamente
    if (lookupOptions[field.id] && lookupOptions[field.id].length > 0) {
      return
    }

    const config = field.configuracao

    // Se tem filtro dependente, buscar valor do filtro
    const hasFilter = config?.dependent_filter?.enabled && config?.dependent_filter?.filter_by_field
    let filterValue = null

    if (hasFilter) {
      const fields = fieldsData?.campos || []
      const filterField = fields.find((f: any) => f.rotulo === config.dependent_filter.filter_by_field)
      if (filterField) {
        filterValue = formData[`campo_${filterField.id}`]
      }

      // Se filtro está habilitado mas não tem valor, não carregar ainda
      if (!filterValue) {
        return
      }
    }

    try {
      let response

      // Tipo 1: Lista (target_list_id) — backend: GET /lookup-lists/{list_id}/options → { opcoes, total }
      if (config?.source_type === 'list' && config?.target_list_id) {
        response = await api.get(`/lookup-lists/${config.target_list_id}/options`, {
          params: filterValue ? { filter: filterValue } : {}
        })
        const opcoes = response.data?.opcoes || []
        setLookupOptions((prev) => ({
          ...prev,
          [field.id]: opcoes.map((item: any) => ({
            label: item.label,
            value: item.id,
            filter: item.filter
          }))
        }))
      }

      // Tipo 2: View (target_view)
      else if (config?.source_type === 'view' && config?.target_view) {
        response = await api.get(`/lookup/views/${config.target_view}/data`, {
          params: viewLookupRequestParams(field, filterValue ? { filter: filterValue } : {}),
        })
        const items = response.data.items || []
        const total = response.data.total || 0

        setLookupOptions((prev) => ({
          ...prev,
          [field.id]: items.map((item: any) => ({
            label: item.label,
            value: item.id,
            filter: item.filter
          }))
        }))

        setLookupTotalCounts((prev) => ({
          ...prev,
          [field.id]: total
        }))
      }

      // Tipo 3: Formulário (target_template_id)
      else if (config?.source_type === 'form' && config?.target_template_id && config?.display_field) {
        response = await api.get(
          `/formularios/${config.target_template_id}/lookup-options`,
          {
            params: {
              display_field: config.display_field,
              value_field: config.value_field || 'id',
            },
          }
        )
        setLookupOptions((prev) => ({
          ...prev,
          [field.id]: response.data,
        }))
      }
    } catch (error) {
      console.error(`Erro ao carregar opções do lookup ${field.id}:`, error)
    }
  }

  // Combo simples (#300): pré-carrega opções ao exibir a página (sem esperar onFocus)
  useEffect(() => {
    const fields = fieldsData?.campos || []
    for (const field of fields) {
      if (field.tipo !== 'lookup' || !isSimpleLookupCombo(field)) continue
      void loadLookupOptionsForField(field)
    }
  }, [fieldsData, formData])

  // Função para buscar no backend com filtro de texto
  const handleLookupSearch = async (fieldId: number, searchTerm: string, config: any, filterValue?: any) => {
    try {
      let response

      if (config?.source_type === 'view' && config?.target_view) {
        response = await api.get(`/lookup/views/${config.target_view}/data`, {
          params: {
            search: searchTerm,
            filter: filterValue || undefined
          }
        })
        const items = response.data.items || []

        const mappedItems = items.map((item: any) => ({
          label: item.label,
          value: item.id,
          filter: item.filter
        }))

        setLookupOptions((prev) => ({
          ...prev,
          [fieldId]: mappedItems
        }))
      }
    } catch (error) {
      console.error('Erro ao buscar lookup:', error)
    }
  }

  // Mutation: Atualizar respostas
  const updateMutation = useMutation({
    mutationFn: (data: Record<string, any>) =>
      reportsApi.update(reportId, { respostas: data }),
    onSuccess: () => {
      // Invalidar queries de relatórios para atualizar listagem e dashboard
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      // Invalidar também a query do relatório atual para garantir dados atualizados
      queryClient.invalidateQueries({ queryKey: ['report', reportId] })
    },
  })

  // Mutation: Finalizar (mudar status)
  const finalizeMutation = useMutation({
    mutationFn: () => reportsApi.updateStatus(reportId, { status: 'em_revisao' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['report', reportId] })
      alert('Relatório finalizado com sucesso!')
      navigate('/relatorios')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao finalizar relatório')
    },
  })

  const approveMutation = useMutation({
    mutationFn: () => reportsApi.updateStatus(reportId, { status: 'aprovado' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['report', reportId] })
      alert('Relatório aprovado!')
      navigate('/relatorios')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao aprovar relatório')
    },
  })

  const requestCorrectionMutation = useMutation({
    mutationFn: (descricao: string) =>
      reportsApi.requestCorrection(reportId, { descricao }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      queryClient.invalidateQueries({ queryKey: ['report', reportId] })
      queryClient.invalidateQueries({ queryKey: ['report-correcoes', reportId] })
      setCorrectionModalOpen(false)
      setCorrectionDesc('')
      alert('Correção solicitada. O relatório foi devolvido ao técnico.')
      navigate('/relatorios')
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao solicitar correção')
    },
  })

  const handleRequestCorrection = () => {
    const trimmed = correctionDesc.trim()
    if (trimmed.length < 10) {
      alert('Descreva a correção com pelo menos 10 caracteres.')
      return
    }
    requestCorrectionMutation.mutate(trimmed)
  }

  const handleApprove = () => {
    if (confirm('Deseja aprovar este relatório?')) {
      approveMutation.mutate()
    }
  }

  const openCorrectionModal = () => {
    setCorrectionDesc('')
    setCorrectionModalOpen(true)
  }

  const goToPrevPage = () => {
    if (currentPageIndex > 0) setCurrentPageIndex(currentPageIndex - 1)
  }

  const goToNextPageView = () => {
    if (currentPageIndex < (pagesData?.paginas?.length || 0) - 1) {
      setCurrentPageIndex(currentPageIndex + 1)
    }
  }

  const handleFieldChange = (fieldId: number, value: any) => {
    if (!canEdit) return

    const fields = fieldsData?.campos || []
    const currentField = fields.find((f: any) => f.id === fieldId)
    if (currentField?.tipo === 'textbox' && typeof value === 'string' && currentField.configuracao?.format_validation === 'uppercase') {
      value = value.toUpperCase()
    }
    const newData = { ...formData, [`campo_${fieldId}`]: value }
    setFormData(newData)

    // Se for campo lookup, salvar o label também (state + respostas para reload)
    if (currentField?.tipo === 'lookup' && value) {
      const options = lookupOptions[fieldId] || []
      const selectedOption = options.find((opt) => String(opt.value) === String(value))
      if (selectedOption) {
        newData[lookupLabelKey(fieldId)] = selectedOption.label
        setLookupSelectedLabels((prev) => ({ ...prev, [fieldId]: selectedOption.label }))
      }
    } else if (currentField?.tipo === 'lookup' && !value) {
      delete newData[lookupLabelKey(fieldId)]
      setLookupSelectedLabels((prev) => {
        const newLabels = { ...prev }
        delete newLabels[fieldId]
        return newLabels
      })
    }

    // Verificar se algum campo depende deste campo (filtro dependente)
    const dependentFields = fields.filter((f: any) => {
      const config = f.configuracao
      if (!config?.dependent_filter?.enabled) return false

      // Encontrar o campo que fornece o filtro
      const filterField = fields.find((ff: any) => ff.rotulo === config.dependent_filter.filter_by_field)
      return filterField?.id === fieldId
    })

    // Limpar e recarregar campos dependentes
    if (dependentFields.length > 0) {
      for (const depField of dependentFields) {
        // Limpar valor do campo dependente
        newData[`campo_${depField.id}`] = ''

        // Limpar label
        setLookupSelectedLabels(prev => {
          const newLabels = { ...prev }
          delete newLabels[depField.id]
          return newLabels
        })

        // Recarregar opções com o novo filtro
        const config = depField.configuracao
        if (value && config?.source_type === 'view' && config?.target_view) {
          api.get(`/lookup/views/${config.target_view}/data`, {
            params: viewLookupRequestParams(depField, { filter: value }),
          }).then(response => {
            const items = response.data.items || []
            const total = response.data.total || 0

            setLookupOptions(prev => ({
              ...prev,
              [depField.id]: items.map((item: any) => ({
                label: item.label,
                value: item.id,
                filter: item.filter
              }))
            }))

            setLookupTotalCounts(prev => ({
              ...prev,
              [depField.id]: total
            }))
          }).catch(error => {
            console.error('Erro ao recarregar lookup dependente:', error)
            setLookupOptions(prev => ({ ...prev, [depField.id]: [] }))
          })
        } else {
          // Se não tem valor, limpar opções
          setLookupOptions(prev => ({ ...prev, [depField.id]: [] }))
        }
      }
      setFormData(newData)
    }

    if (canEdit) {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current)
      }
      saveTimerRef.current = setTimeout(() => {
        updateMutation.mutate(newData)
      }, 1000)
    }
  }

  const handlePrevPage = () => {
    if (currentPageIndex > 0) {
      setCurrentPageIndex(currentPageIndex - 1)
    }
  }

  const handleNextPage = () => {
    if (!validateCurrentPageRequiredFields()) return

    if (currentPageIndex < (pagesData?.paginas?.length || 0) - 1) {
      setCurrentPageIndex(currentPageIndex + 1)
    }
  }

  const validateCurrentPageRequiredFields = (): boolean => {
    const fields = fieldsData?.campos || []
    const requiredFields = fields.filter(f => f.tipo !== 'separator' && f.configuracao?.require)

    for (const field of requiredFields) {
      if (isRequiredFieldEmpty(field, formData)) {
        alert(`Campo "${field.rotulo}" é obrigatório`)
        focusWizardField(field.id)
        return false
      }
    }
    return true
  }

  const handleSaveDraft = () => {
    updateMutation.mutate(formData, {
      onSuccess: () => {
        alert('Rascunho salvo!')
      },
      onError: (error: any) => {
        alert(error.response?.data?.detail || 'Erro ao salvar rascunho')
      },
    })
  }

  const handleFinalize = () => {
    if (!validateCurrentPageRequiredFields()) return

    const message =
      report?.status === 'em_correcao'
        ? 'Deseja reenviar este relatório para revisão?'
        : 'Deseja finalizar este relatório? Ele será enviado para revisão.'
    if (confirm(message)) {
      updateMutation.mutate(formData)
      setTimeout(() => finalizeMutation.mutate(), 500)
    }
  }

  // Mutation: Exportar para Excel
  const exportExcelMutation = useMutation({
    mutationFn: () => reportsApi.exportToExcel(reportId),
    onSuccess: (blob) => {
      // Criar URL temporária e fazer download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `Relatorio_${report?.numero}_${new Date().toISOString().slice(0, 10)}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
    onError: async (error: any) => {
      // Se a resposta for um blob de erro, converter para texto
      if (error.response?.data instanceof Blob) {
        try {
          const text = await error.response.data.text()
          const errorData = JSON.parse(text)
          alert(`Erro ao exportar: ${errorData.detail || 'Erro desconhecido'}`)
        } catch {
          alert('Erro ao exportar relatório para Excel')
        }
      } else {
        alert(error.response?.data?.detail || error.message || 'Erro ao exportar relatório para Excel')
      }
    },
  })

  // Mutation: Exportar para PDF
  const exportPdfMutation = useMutation({
    mutationFn: () => reportsApi.exportToPdf(reportId),
    onSuccess: (blob) => {
      // Criar URL temporária e fazer download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `Relatorio_${report?.numero}_${new Date().toISOString().slice(0, 10)}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
    onError: async (error: any) => {
      // Se a resposta for um blob de erro, converter para texto
      if (error.response?.data instanceof Blob) {
        try {
          const text = await error.response.data.text()
          const errorData = JSON.parse(text)
          alert(`Erro ao exportar: ${errorData.detail || 'Erro desconhecido'}`)
        } catch {
          alert('Erro ao exportar relatório para PDF')
        }
      } else {
        alert(error.response?.data?.detail || error.message || 'Erro ao exportar relatório para PDF')
      }
    },
  })

  const handleExportExcel = () => {
    if (confirm('Deseja exportar este relatório para Excel?')) {
      exportExcelMutation.mutate()
    }
  }

  const handleExportPdf = () => {
    if (confirm('Deseja exportar este relatório para PDF?')) {
      exportPdfMutation.mutate()
    }
  }

  const renderField = (field: any) => {
    const fieldKey = `campo_${field.id}`
    const fieldInputId = wizardFieldDomId(field.id)
    const value = formData[fieldKey] || ''
    const readOnly = !!(field.configuracao?.read_only || formReadOnly)

    switch (field.tipo) {
      case 'textbox':
        if (readOnly) {
          return (
            <div className="flex h-10 w-full rounded-md border border-slate-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
              {value || '-'}
            </div>
          )
        }
        return (
          <Input
            id={fieldInputId}
            value={value}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            required={field.configuracao?.require}
            maxLength={field.configuracao?.max_characters}
            placeholder={field.rotulo}
          />
        )

      case 'date':
        // Se for somente leitura, renderizar como texto estilizado
        if (readOnly) {
          const displayValue = formatDateValue(value, field.configuracao?.date_format)
          return (
            <div className="flex h-10 w-full rounded-md border border-slate-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
              {displayValue}
            </div>
          )
        }
        return (
          <Input
            id={fieldInputId}
            type={field.configuracao?.type || 'date'}
            value={value}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            required={field.configuracao?.require}
          />
        )

      case 'number':
        // Se for somente leitura, renderizar como texto estilizado
        if (readOnly) {
          return (
            <div className="flex h-10 w-full rounded-md border border-slate-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
              {value || '-'}
            </div>
          )
        }
        return (
          <Input
            id={fieldInputId}
            type="number"
            value={value}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            required={field.configuracao?.require}
            step={field.configuracao?.decimal_places > 0 ? '0.01' : '1'}
          />
        )

      case 'yes_no':
        // Sempre usar string "true"/"false" para evitar perda no refetch/JSON
        const yesNoValue = value === true || value === 'true' ? 'true' : value === false || value === 'false' ? 'false' : ''
        if (readOnly) {
          const displayValue = yesNoValue === 'true' ? 'Sim' : yesNoValue === 'false' ? 'Não' : '-'
          return (
            <div className="flex h-10 w-full rounded-md border border-slate-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
              {displayValue}
            </div>
          )
        }
        // Dois radios sempre visíveis (Sim | Não), valor em string "true"/"false"
        return (
          <div className="flex gap-6 items-center">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                id={fieldInputId}
                type="radio"
                name={fieldKey}
                value="true"
                checked={yesNoValue === 'true'}
                onChange={() => handleFieldChange(field.id, 'true')}
                required={field.configuracao?.require}
                className="w-4 h-4 border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <span>Sim</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="radio"
                name={fieldKey}
                value="false"
                checked={yesNoValue === 'false'}
                onChange={() => handleFieldChange(field.id, 'false')}
                required={field.configuracao?.require}
                className="w-4 h-4 border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <span>Não</span>
            </label>
          </div>
        )

      case 'choice':
        const choiceOptions = field.configuracao?.options || []
        const allowMultiple = field.configuracao?.allow_multiple || false

        // Se for somente leitura, renderizar como texto estilizado
        if (readOnly) {
          const displayValue = allowMultiple
            ? (Array.isArray(value) ? value.join(', ') : value || '-')
            : (value || '-')
          return (
            <div className="flex h-10 w-full rounded-md border border-slate-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
              {displayValue}
            </div>
          )
        }

        if (allowMultiple) {
          // Renderizar checkboxes para seleção múltipla
          const selectedValues = Array.isArray(value) ? value : (value ? [value] : [])
          return (
            <div className="space-y-2">
              {choiceOptions.map((option: string, index: number) => (
                <label key={index} className="flex items-center gap-2">
                  <input
                    id={index === 0 ? fieldInputId : undefined}
                    type="checkbox"
                    checked={selectedValues.includes(option)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        handleFieldChange(field.id, [...selectedValues, option])
                      } else {
                        handleFieldChange(field.id, selectedValues.filter((v: string) => v !== option))
                      }
                    }}
                    disabled={readOnly}
                    className="rounded"
                  />
                  <span>{option}</span>
                </label>
              ))}
            </div>
          )
        } else {
          // Renderizar select para seleção única
          return (
            <Select
              id={fieldInputId}
              value={value || ''}
              onChange={(e) => handleFieldChange(field.id, e.target.value)}
              disabled={readOnly}
            >
              <option value="">Selecione...</option>
              {choiceOptions.map((option: string, index: number) => (
                <option key={index} value={option}>
                  {option}
                </option>
              ))}
            </Select>
          )
        }

      case 'lookup':
        const options = lookupOptions[field.id] || []
        const useAutocomplete = field.configuracao?.use_autocomplete !== false
        const totalCount = lookupTotalCounts[field.id] || 0

        // Obter filterValue se houver filtro dependente
        const hasFilter = field.configuracao?.dependent_filter?.enabled && field.configuracao?.dependent_filter?.filter_by_field
        let filterValue = null
        if (hasFilter) {
          const fields = fieldsData?.campos || []
          const filterField = fields.find((f: any) => f.rotulo === field.configuracao.dependent_filter.filter_by_field)
          if (filterField) {
            filterValue = formData[`campo_${filterField.id}`]
          }
        }

        // Obter label do valor selecionado (do state dedicado ou das options)
        const selectedLabel = value
          ? (lookupSelectedLabels[field.id] ||
              options.find((opt) => String(opt.value) === String(value))?.label)
          : null

        // Se for somente leitura, renderizar como texto estilizado
        if (readOnly) {
          const displayValue = value && selectedLabel ? `${value} | ${selectedLabel}` : value || '-'
          return (
            <div className="flex h-10 w-full rounded-md border border-slate-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
              {displayValue}
            </div>
          )
        }

        return (
          <div>
            {useAutocomplete ? (
              <Autocomplete
                inputId={fieldInputId}
                options={options}
                value={value || ''}
                selectedLabel={selectedLabel || undefined}
                onChange={(newValue) => handleFieldChange(field.id, newValue)}
                placeholder="Digite para buscar..."
                disabled={readOnly}
                totalCount={totalCount}
                minCharsForSearch={3}
                onSearch={(searchTerm) => handleLookupSearch(field.id, searchTerm, field.configuracao, filterValue)}
                onFocus={() => loadLookupOptionsForField(field)}
              />
            ) : (
              <Select
                id={fieldInputId}
                value={value || ''}
                onChange={(e) => handleFieldChange(field.id, e.target.value)}
                onFocus={() => loadLookupOptionsForField(field)}
                disabled={readOnly}
              >
                <option value="">Selecione...</option>
                {options.map((opt, index) => (
                  <option key={`${opt.value}-${index}`} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
            )}

            {/* Exibir ID e Label do valor selecionado */}
            {value && selectedLabel && (
              <div className="mt-1 text-xs text-gray-600">
                {value} | {selectedLabel}
              </div>
            )}
          </div>
        )

      case 'separator':
        return (
          <div className="my-6 border-t-2 border-gray-300 pt-4">
            <h3 className="text-lg font-bold text-gray-900 mb-1">
              {field.configuracao?.titulo || 'Separador'}
            </h3>
            {field.configuracao?.descricao && (
              <p className="text-sm text-gray-600">
                {field.configuracao.descricao}
              </p>
            )}
          </div>
        )

      case 'grid':
        return (
          <div className="border rounded p-4 bg-gray-50">
            <p className="text-sm text-gray-600">
              [Tipo GRID será implementado em sprint futura]
            </p>
          </div>
        )

      default:
        return <p className="text-sm text-gray-500">Tipo de campo não suportado: {field.tipo}</p>
    }
  }

  if (loadingReport || loadingPages) {
    return <div className="p-6 text-center">Carregando...</div>
  }

  if (reportError) {
    const errorMessage = (reportError as any)?.response?.data?.detail || (reportError as Error)?.message || 'Erro desconhecido'
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-900 mb-2">Erro ao carregar relatório</h2>
          <p className="text-red-700 mb-4">{errorMessage}</p>
          <p className="text-sm text-red-600">Report ID: {reportId}</p>
          <Button className="mt-4" onClick={() => navigate('/relatorios')}>
            Voltar para lista
          </Button>
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-yellow-900 mb-2">Relatório não encontrado</h2>
          <p className="text-yellow-700">O relatório com ID {reportId} não foi encontrado.</p>
          <Button className="mt-4" onClick={() => navigate('/relatorios')}>
            Voltar para lista
          </Button>
        </div>
      </div>
    )
  }

  const pages = pagesData?.paginas || []
  const fields = fieldsData?.campos || []
  const isLastPage = currentPageIndex === pages.length - 1

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">{report.numero}</h1>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              report.status === 'rascunho'
                ? 'bg-gray-100 text-gray-700'
                : report.status === 'em_revisao'
                ? 'bg-blue-100 text-blue-700'
                : report.status === 'em_correcao'
                ? 'bg-orange-100 text-orange-700'
                : report.status === 'aprovado'
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {getReportStatusLabel(report.status)}
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          {report.cliente?.nome} - {report.equipamento?.nome}
        </p>
      </div>

      {/* Tabs de Páginas + Histórico */}
      <div className="mb-6 border-b">
        <div className="flex gap-2 flex-wrap">
          {pages.map((page, index) => (
            <button
              key={page.id}
              onClick={() => {
                setShowHistorico(false)
                setCurrentPageIndex(index)
              }}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                !showHistorico && index === currentPageIndex
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {page.nome}
            </button>
          ))}
          {canViewHistorico && (
            <button
              onClick={() => setShowHistorico(true)}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                showHistorico
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Histórico de Correções
            </button>
          )}
        </div>
      </div>

      {showHistorico ? (
        <div className="bg-white p-6 rounded-lg border space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Histórico de Correções</h2>
          {loadingCorrecoes ? (
            <p className="text-center text-gray-500">Carregando histórico...</p>
          ) : (correcoesData?.correcoes?.length || 0) === 0 ? (
            <p className="text-center text-gray-500 py-8">
              Nenhuma solicitação de correção registrada.
            </p>
          ) : (
            <div className="space-y-4">
              {correcoesData!.correcoes.map((correcao) => (
                <div
                  key={correcao.id}
                  className="border rounded-lg p-4 bg-orange-50/40 border-orange-100"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <p className="text-sm font-medium text-gray-900">
                      {correcao.solicitado_por_nome}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(correcao.created_at).toLocaleString('pt-BR')}
                    </p>
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{correcao.descricao}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white p-6 rounded-lg border space-y-6">
          {loadingFields ? (
            <p className="text-center text-gray-500">Carregando campos...</p>
          ) : (
            fields.map((field) => (
              <div
                key={field.id}
                id={`wizard-field-wrap-${field.id}`}
                className={field.tipo === 'separator' ? '' : 'space-y-2'}
              >
                {field.tipo !== 'separator' && (
                  <Label>
                    {field.rotulo}
                    {field.configuracao?.require && <span className="text-red-500 ml-1">*</span>}
                  </Label>
                )}
                {renderField(field)}
              </div>
            ))
          )}

          {fields.length === 0 && (
            <p className="text-center text-gray-500 py-8">Nenhum campo nesta página</p>
          )}
        </div>
      )}

      {/* Botões de Navegação */}
      <div className="mt-6 flex justify-between items-center">
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate('/relatorios')}>
            Voltar
          </Button>
          {canEdit && (report.status === 'rascunho' || report.status === 'em_correcao') && (
            <Button variant="outline" onClick={handleSaveDraft} disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Salvando...' : 'Salvar Rascunho'}
            </Button>
          )}
          {canExportExcel && (
            <Button
              variant="default"
              onClick={handleExportExcel}
              disabled={exportExcelMutation.isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              {exportExcelMutation.isPending ? 'Exportando...' : '📊 Exportar Excel'}
            </Button>
          )}
          {/* BOTÃO PDF OCULTO - Conforme solicitação do usuário
          <Button
            variant="default"
            onClick={handleExportPdf}
            disabled={exportPdfMutation.isPending}
            className="bg-red-600 hover:bg-red-700"
          >
            {exportPdfMutation.isPending ? 'Exportando...' : '📄 Exportar PDF'}
          </Button>
          */}
        </div>

        <div className="flex gap-2 flex-wrap justify-end">
          {canApprove && (
            <Button
              variant="default"
              className="bg-green-600 hover:bg-green-700"
              onClick={handleApprove}
              disabled={approveMutation.isPending}
            >
              {approveMutation.isPending ? 'Aprovando...' : 'Aprovar'}
            </Button>
          )}
          {canRequestCorr && (
            <Button
              variant="outline"
              className="border-orange-500 text-orange-700 hover:bg-orange-50"
              onClick={openCorrectionModal}
              disabled={requestCorrectionMutation.isPending}
            >
              Solicitar Correção
            </Button>
          )}
          {canFinalize && !showHistorico && (
            <>
              {currentPageIndex > 0 && (
                <Button variant="outline" onClick={handlePrevPage}>
                  Anterior
                </Button>
              )}
              {!isLastPage ? (
                <Button onClick={handleNextPage}>Próxima</Button>
              ) : (
                <Button onClick={handleFinalize} disabled={finalizeMutation.isPending}>
                  {finalizeMutation.isPending ? 'Finalizando...' : 'Finalizar'}
                </Button>
              )}
            </>
          )}
          {!canEdit && !showHistorico && pages.length > 1 && (
            <>
              {currentPageIndex > 0 && (
                <Button variant="outline" onClick={goToPrevPage}>
                  Anterior
                </Button>
              )}
              {currentPageIndex < pages.length - 1 && (
                <Button variant="outline" onClick={goToNextPageView}>
                  Próxima
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Status de Auto-save */}
      {canEdit && !showHistorico && updateMutation.isPending && (
        <p className="text-sm text-gray-500 text-center mt-2">Salvando automaticamente...</p>
      )}

      <Dialog open={correctionModalOpen} onOpenChange={setCorrectionModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Solicitar Correção</DialogTitle>
            <DialogDescription>
              Descreva o que o técnico deve corrigir. O relatório voltará para o status Em Correção.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="correcao-descricao">Descrição da correção</Label>
            <textarea
              id="correcao-descricao"
              className="flex min-h-[120px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={correctionDesc}
              onChange={(e) => setCorrectionDesc(e.target.value)}
              maxLength={2000}
              placeholder="Descreva os ajustes necessários (mínimo 10 caracteres)"
            />
            <p className="text-xs text-gray-500">
              {correctionDesc.trim().length}/10 caracteres mínimos
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCorrectionModalOpen(false)}>
              Cancelar
            </Button>
            <Button
              className="bg-orange-600 hover:bg-orange-700"
              onClick={handleRequestCorrection}
              disabled={
                requestCorrectionMutation.isPending || correctionDesc.trim().length < 10
              }
            >
              {requestCorrectionMutation.isPending ? 'Enviando...' : 'Solicitar Correção'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

/**
 * API - Formulários
 */

import { api } from './client'
import type {
  Formulario,
  FormularioCreate,
  FormularioUpdate,
  FormularioListResponse,
} from './types'

export const formulariosApi = {
  /**
   * Listar formulários
   */
  async list(): Promise<FormularioListResponse> {
    const { data } = await api.get<FormularioListResponse>('/formularios')
    return data
  },

  /**
   * Obter formulário por ID
   */
  async get(id: number): Promise<Formulario> {
    const { data } = await api.get<Formulario>(`/formularios/${id}`)
    return data
  },

  /**
   * Criar formulário
   */
  async create(formulario: FormularioCreate): Promise<Formulario> {
    const { data } = await api.post<Formulario>('/formularios', formulario)
    return data
  },

  /**
   * Atualizar formulário
   */
  async update(id: number, formulario: FormularioUpdate): Promise<Formulario> {
    const { data } = await api.put<Formulario>(`/formularios/${id}`, formulario)
    return data
  },

  /**
   * Excluir formulário
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/formularios/${id}`)
  },

  /**
   * Download template Excel para importação de páginas/campos
   */
  async downloadImportTemplate(): Promise<Blob> {
    const { data } = await api.get('/formularios/import-template', {
      responseType: 'blob',
    })
    return data
  },

  /**
   * Download do template Excel de mesclagem gravado no formulário (#302)
   */
  async downloadExcelTemplate(id: number): Promise<Blob> {
    const { data } = await api.get(`/formularios/${id}/excel-template`, {
      responseType: 'blob',
    })
    return data
  },

  /**
   * Importar páginas e campos de Excel
   */
  async importExcel(
    templateId: number,
    file: File,
    replace: boolean = false
  ): Promise<{ success: boolean; pages_created: number; fields_created: number; message: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const { data } = await api.post(
      `/formularios/${templateId}/import-excel?replace=${replace}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return data
  },

  /**
   * Exportar template completo (formulário + páginas + campos) em JSON
   * Sprint 007
   */
  async exportTemplate(id: number): Promise<any> {
    const { data } = await api.get(`/formularios/${id}/export`)
    return data
  },

  /**
   * Importar template de arquivo JSON SUBSTITUINDO template existente
   * DANGER ZONE: Substitui completamente páginas e campos
   * Sprint 007
   */
  async importTemplate(templateId: number, file: File): Promise<{ success: boolean; id: number; nome: string; message: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const { data } = await api.post(`/formularios/${templateId}/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return data
  },
}

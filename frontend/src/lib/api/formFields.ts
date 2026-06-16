import { api } from './client';

export interface FormField {
  id: number;
  pagina_id: number;
  rotulo: string;
  ordem: number;
  tipo: 'textbox' | 'date' | 'number' | 'yes_no' | 'choice' | 'lookup' | 'separator';
  configuracao: Record<string, any>;
  regra_exibicao_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface FormFieldCreate {
  rotulo: string;
  ordem: number;
  tipo: string;
  configuracao?: Record<string, any>;
  regra_exibicao_id?: number | null;
}

export interface FormFieldUpdate {
  rotulo?: string;
  ordem?: number;
  tipo?: string;
  configuracao?: Record<string, any>;
  regra_exibicao_id?: number | null;
}

export interface FormFieldListResponse {
  total: number;
  campos: FormField[];
}

export const formFieldsApi = {
  /**
   * Listar todos os campos de uma página
   */
  list: async (pageId: number): Promise<FormFieldListResponse> => {
    const response = await api.get<FormFieldListResponse>(
      `/form-pages/${pageId}/fields`
    );
    return response.data;
  },

  /**
   * Obter um campo específico
   */
  get: async (pageId: number, fieldId: number): Promise<FormField> => {
    const response = await api.get<FormField>(
      `/form-pages/${pageId}/fields/${fieldId}`
    );
    return response.data;
  },

  /**
   * Criar novo campo
   */
  create: async (pageId: number, data: FormFieldCreate): Promise<FormField> => {
    const response = await api.post<FormField>(
      `/form-pages/${pageId}/fields`,
      data
    );
    return response.data;
  },

  /**
   * Atualizar campo
   */
  update: async (
    pageId: number,
    fieldId: number,
    data: FormFieldUpdate
  ): Promise<FormField> => {
    const response = await api.put<FormField>(
      `/form-pages/${pageId}/fields/${fieldId}`,
      data
    );
    return response.data;
  },

  /**
   * Excluir campo
   */
  delete: async (pageId: number, fieldId: number): Promise<void> => {
    await api.delete(`/form-pages/${pageId}/fields/${fieldId}`);
  },

  /**
   * Reordenar campos (atualiza ordem de múltiplos campos em lote)
   */
  reorder: async (
    pageId: number,
    fields: { id: number; ordem: number }[]
  ): Promise<void> => {
    await api.post(`/form-pages/${pageId}/fields/reorder`, {
      fields: fields,
    });
  },
};

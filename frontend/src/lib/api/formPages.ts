import { api } from './client';

export interface FormPage {
  id: number;
  formulario_id: number;
  nome: string;
  ordem: number;
  regra_exibicao_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface FormPageCreate {
  nome: string;
  ordem: number;
  regra_exibicao_id?: number | null;
}

export interface FormPageUpdate {
  nome?: string;
  ordem?: number;
  regra_exibicao_id?: number | null;
}

export interface FormPageListResponse {
  total: number;
  paginas: FormPage[];
}

export const formPagesApi = {
  /**
   * Listar todas as páginas de um formulário
   */
  list: async (templateId: number): Promise<FormPageListResponse> => {
    const response = await api.get<FormPageListResponse>(
      `/form-templates/${templateId}/pages`
    );
    return response.data;
  },

  /**
   * Obter uma página específica
   */
  get: async (templateId: number, pageId: number): Promise<FormPage> => {
    const response = await api.get<FormPage>(
      `/form-templates/${templateId}/pages/${pageId}`
    );
    return response.data;
  },

  /**
   * Criar nova página
   */
  create: async (
    templateId: number,
    data: FormPageCreate
  ): Promise<FormPage> => {
    const response = await api.post<FormPage>(
      `/form-templates/${templateId}/pages`,
      data
    );
    return response.data;
  },

  /**
   * Atualizar página
   */
  update: async (
    templateId: number,
    pageId: number,
    data: FormPageUpdate
  ): Promise<FormPage> => {
    const response = await api.put<FormPage>(
      `/form-templates/${templateId}/pages/${pageId}`,
      data
    );
    return response.data;
  },

  /**
   * Excluir página
   */
  delete: async (templateId: number, pageId: number): Promise<void> => {
    await api.delete(`/form-templates/${templateId}/pages/${pageId}`);
  },

  /**
   * Reordenar páginas (atualiza ordem de múltiplas páginas em lote)
   */
  reorder: async (
    templateId: number,
    pages: { id: number; ordem: number }[]
  ): Promise<void> => {
    await api.post(`/form-templates/${templateId}/pages/reorder`, {
      pages: pages,
    });
  },
};

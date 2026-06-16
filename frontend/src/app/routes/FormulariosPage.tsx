/**
 * Formulários Page - CRUD de Templates de Formulários
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { formulariosApi } from '@/lib/api/formularios'
import { Plus, Search, Settings } from 'lucide-react'
import type { Formulario, FormularioCreate } from '@/lib/api/types'

export default function FormulariosPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingForm, setEditingForm] = useState<Formulario | null>(null)
  const [formData, setFormData] = useState<FormularioCreate>({
    nome: '',
    descricao: '',
  })

  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Query para listar formulários
  const { data, isLoading, error } = useQuery({
    queryKey: ['formularios'],
    queryFn: () => formulariosApi.list(),
  })

  // Mutation para criar formulário
  const createMutation = useMutation({
    mutationFn: (data: FormularioCreate) => formulariosApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['formularios'] })
      setIsModalOpen(false)
      resetForm()
    },
  })

  // Mutation para atualizar formulário
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: FormularioCreate }) =>
      formulariosApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['formularios'] })
      setIsModalOpen(false)
      resetForm()
    },
  })

  // Mutation para excluir formulário
  const deleteMutation = useMutation({
    mutationFn: (id: number) => formulariosApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['formularios'] })
    },
  })

  const resetForm = () => {
    setFormData({ nome: '', descricao: '' })
    setEditingForm(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingForm) {
      updateMutation.mutate({ id: editingForm.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleEdit = (formulario: Formulario) => {
    setEditingForm(formulario)
    setFormData({
      nome: formulario.nome,
      descricao: formulario.descricao || '',
    })
    setIsModalOpen(true)
  }

  const handleDelete = (id: number, nome: string) => {
    if (confirm(`Deseja realmente excluir o formulário "${nome}"?`)) {
      deleteMutation.mutate(id)
    }
  }

  const filteredFormularios = data?.formularios.filter((f) =>
    f.nome.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Formulários</h1>
          <p className="text-gray-500 mt-1">
            Gerencie os templates de formulários do sistema
          </p>
        </div>
        <button
          onClick={() => {
            resetForm()
            setIsModalOpen(true)
          }}
          className="btn-primary flex items-center"
        >
          <Plus size={20} className="mr-2" />
          Novo Formulário
        </button>
      </div>

      {/* Search */}
      <div className="card">
        <div className="relative">
          <Search
            size={20}
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            placeholder="Buscar formulários..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10"
          />
        </div>
      </div>

      {/* List */}
      <div className="card">
        {isLoading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-2 text-gray-600">Carregando formulários...</p>
          </div>
        )}

        {error && (
          <div className="text-center py-8 text-red-600">
            Erro ao carregar formulários. Tente novamente.
          </div>
        )}

        {filteredFormularios && filteredFormularios.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            Nenhum formulário encontrado.
          </div>
        )}

        {filteredFormularios && filteredFormularios.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Nome
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Descrição
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">
                    Páginas
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">
                    Campos
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Criado em
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredFormularios.map((formulario) => (
                  <tr
                    key={formulario.id}
                    className="border-b border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4 font-medium text-gray-900">
                      {formulario.nome}
                    </td>
                    <td className="py-3 px-4 text-gray-600">
                      {formulario.descricao || '-'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {formulario.total_paginas || 0}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {formulario.total_campos || 0}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-600 text-sm">
                      {new Date(formulario.criado_em).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => navigate(`/formularios/${formulario.id}`)}
                        className="text-green-600 hover:text-green-800"
                        title="Gerenciar Páginas e Campos"
                      >
                        <Settings size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                {editingForm ? 'Editar Formulário' : 'Novo Formulário'}
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label htmlFor="nome" className="label">
                  Nome *
                </label>
                <input
                  id="nome"
                  type="text"
                  value={formData.nome}
                  onChange={(e) =>
                    setFormData({ ...formData, nome: e.target.value })
                  }
                  className="input"
                  placeholder="Digite o nome do formulário"
                  required
                  minLength={3}
                  maxLength={100}
                />
              </div>

              <div>
                <label htmlFor="descricao" className="label">
                  Descrição
                </label>
                <textarea
                  id="descricao"
                  value={formData.descricao}
                  onChange={(e) =>
                    setFormData({ ...formData, descricao: e.target.value })
                  }
                  className="input"
                  placeholder="Digite a descrição (opcional)"
                  rows={3}
                  maxLength={500}
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setIsModalOpen(false)
                    resetForm()
                  }}
                  className="btn-secondary"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? 'Salvando...'
                    : editingForm
                    ? 'Atualizar'
                    : 'Criar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

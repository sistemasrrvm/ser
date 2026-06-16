/**
 * UsuariosPage - CRUD completo de usuários
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { usuariosApi, Usuario, UsuarioCreate, UsuarioUpdate } from '@/lib/api/usuarios'
import { rolesApi } from '@/lib/api/roles'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Plus, Pencil, Trash2, X, RotateCcw, AlertTriangle } from 'lucide-react'

type FilterType = 'all' | 'active' | 'inactive'

export default function UsuariosPage() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingUsuario, setEditingUsuario] = useState<Usuario | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<FilterType>('active')
  const [triedToSubmit, setTriedToSubmit] = useState(false)

  // Form state
  const [formData, setFormData] = useState<UsuarioCreate>({
    username: '',
    password: '',
    full_name: '',
    email: '',
    role_id: 0, // Será definido após carregar os roles
    is_active: true,
  })

  // Query para listar usuários com filtro
  const { data: usuariosResponse, isLoading } = useQuery({
    queryKey: ['usuarios', filterType],
    queryFn: () => {
      const isActive = filterType === 'all' ? undefined : filterType === 'active'
      return usuariosApi.list(isActive)
    },
  })

  // Query para listar roles
  const { data: rolesResponse, isLoading: isLoadingRoles } = useQuery({
    queryKey: ['roles'],
    queryFn: () => rolesApi.list(),
  })

  const usuarios = usuariosResponse?.users || []
  const roles = rolesResponse?.roles || []

  // Mutation para criar
  const createMutation = useMutation({
    mutationFn: (data: UsuarioCreate) => usuariosApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      closeModal()
    },
    onError: (error: any) => {
      alert(error?.response?.data?.detail || 'Erro ao criar usuário')
    },
  })

  // Mutation para atualizar
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UsuarioUpdate }) =>
      usuariosApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      closeModal()
    },
    onError: (error: any) => {
      alert(error?.response?.data?.detail || 'Erro ao atualizar usuário')
    },
  })

  // Mutation para deletar (soft delete)
  const deleteMutation = useMutation({
    mutationFn: (id: number) => usuariosApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
    },
    onError: (error: any) => {
      alert(error?.response?.data?.detail || 'Erro ao deletar usuário')
    },
  })

  // Mutation para reativar
  const reactivateMutation = useMutation({
    mutationFn: (id: number) => usuariosApi.reactivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
    },
    onError: (error: any) => {
      alert(error?.response?.data?.detail || 'Erro ao reativar usuário')
    },
  })

  // Mutation para excluir definitivamente
  const deletePermanentMutation = useMutation({
    mutationFn: (id: number) => usuariosApi.deletePermanent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
    },
    onError: (error: any) => {
      alert(error?.response?.data?.detail || 'Erro ao excluir usuário')
    },
  })

  const openCreateModal = () => {
    setEditingUsuario(null)
    setTriedToSubmit(false)
    setFormData({
      username: '',
      password: '',
      full_name: '',
      email: '',
      role_id: 0,
      is_active: true,
    })
    setIsModalOpen(true)
  }

  const openEditModal = (usuario: Usuario) => {
    setEditingUsuario(usuario)
    setTriedToSubmit(false)
    setFormData({
      username: '', // username não pode ser alterado
      password: '', // senha vazia = não alterar
      full_name: usuario.full_name,
      email: usuario.email || '',
      role_id: usuario.role.id,
      is_active: usuario.is_active,
    })
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingUsuario(null)
    setTriedToSubmit(false)
    setFormData({
      username: '',
      password: '',
      full_name: '',
      email: '',
      role_id: 0,
      is_active: true,
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setTriedToSubmit(true)

    if (editingUsuario) {
      // Atualizar
      if (!formData.email?.trim()) {
        alert('Email é obrigatório')
        return
      }
      const updateData: UsuarioUpdate = {
        full_name: formData.full_name,
        email: formData.email.trim(),
        role_id: formData.role_id,
        is_active: formData.is_active,
      }
      // Incluir password apenas se foi preenchido
      if (formData.password && formData.password.trim().length > 0) {
        if (formData.password.length < 8) {
          alert('Senha deve ter no mínimo 8 caracteres')
          return
        }
        updateData.password = formData.password.trim()
      }
      updateMutation.mutate({ id: editingUsuario.id, data: updateData })
    } else {
      // Criar
      if (!formData.username.trim()) {
        alert('Username é obrigatório')
        return
      }
      if (!formData.password || formData.password.length < 8) {
        alert('Senha deve ter no mínimo 8 caracteres')
        return
      }
      if (!formData.full_name.trim()) {
        alert('Nome completo é obrigatório')
        return
      }
      if (!formData.email?.trim()) {
        alert('Email é obrigatório')
        return
      }
      if (!formData.role_id || formData.role_id === 0) {
        alert('Por favor, selecione um perfil')
        return
      }
      
      // Preparar dados para envio
      const createData = {
        ...formData,
        email: formData.email.trim()
      }
      
      createMutation.mutate(createData)
    }
  }

  const handleDelete = (usuario: Usuario) => {
    if (
      confirm(
        `Tem certeza que deseja marcar "${usuario.full_name}" como inativo?\n\n` +
          `O usuário não poderá mais fazer login.`
      )
    ) {
      deleteMutation.mutate(usuario.id)
    }
  }

  const handleReactivate = (usuario: Usuario) => {
    if (
      confirm(
        `Deseja reativar o usuário "${usuario.full_name}"?\n\n` +
          `O usuário poderá fazer login novamente.`
      )
    ) {
      reactivateMutation.mutate(usuario.id)
    }
  }

  const handleDeletePermanent = (usuario: Usuario) => {
    if (
      confirm(
        `⚠️ ATENÇÃO: Exclusão Definitiva\n\n` +
          `Tem certeza que deseja excluir definitivamente o usuário "${usuario.full_name}"?\n\n` +
          `Esta ação NÃO pode ser desfeita e o usuário será removido permanentemente do sistema.`
      )
    ) {
      if (
        confirm(
          `Confirmação Final\n\n` +
            `Você tem certeza absoluta?\n\n` +
            `Usuário: ${usuario.full_name} (${usuario.username})\n` +
            `Esta ação é IRREVERSÍVEL!`
        )
      ) {
        deletePermanentMutation.mutate(usuario.id)
      }
    }
  }

  // Filtrar usuários por busca
  const filteredUsuarios = usuarios.filter((usuario) => {
    if (!searchTerm) return true
    const search = searchTerm.toLowerCase()
    return (
      usuario.username.toLowerCase().includes(search) ||
      usuario.full_name.toLowerCase().includes(search) ||
      (usuario.email && usuario.email.toLowerCase().includes(search))
    )
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Usuários</h1>
          <p className="text-gray-500 mt-1">
            Gerenciar usuários do sistema ({usuarios.length} {filterType === 'all' ? 'total' : filterType === 'active' ? 'ativos' : 'inativos'})
          </p>
        </div>
        <Button onClick={openCreateModal}>
          <Plus className="h-4 w-4 mr-2" />
          Novo Usuário
        </Button>
      </div>

      {/* Busca e Filtros */}
      <div className="flex gap-4">
        <div className="flex-1">
          <Input
            type="text"
            placeholder="Buscar por username, nome ou email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as FilterType)}
            className="min-w-[150px]"
          >
            <option value="active">Ativos</option>
            <option value="inactive">Inativos</option>
            <option value="all">Todos</option>
          </Select>
        </div>
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Username
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Nome Completo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    Carregando...
                  </td>
                </tr>
              ) : filteredUsuarios.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    {searchTerm ? 'Nenhum usuário encontrado' : 'Nenhum usuário cadastrado'}
                  </td>
                </tr>
              ) : (
                filteredUsuarios.map((usuario) => (
                  <tr 
                    key={usuario.id} 
                    className={`hover:bg-gray-50 ${!usuario.is_active ? 'bg-gray-50 opacity-75' : ''}`}
                  >
                    <td className="px-6 py-4 text-sm font-mono text-gray-900">
                      {usuario.username}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">{usuario.full_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {usuario.email || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                          usuario.role.level === 100
                            ? 'bg-purple-100 text-purple-800'
                            : usuario.role.level >= 50
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {usuario.role.name}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span
                        className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                          usuario.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {usuario.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-right space-x-2">
                      {usuario.is_active ? (
                        <>
                          <button
                            onClick={() => openEditModal(usuario)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Editar"
                          >
                            <Pencil className="h-4 w-4 inline" />
                          </button>
                          <button
                            onClick={() => handleDelete(usuario)}
                            className="text-red-600 hover:text-red-800"
                            title="Desativar"
                          >
                            <Trash2 className="h-4 w-4 inline" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => openEditModal(usuario)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Editar"
                          >
                            <Pencil className="h-4 w-4 inline" />
                          </button>
                          <button
                            onClick={() => handleReactivate(usuario)}
                            className="text-green-600 hover:text-green-800"
                            title="Reativar"
                            disabled={reactivateMutation.isPending}
                          >
                            <RotateCcw className="h-4 w-4 inline" />
                          </button>
                          <button
                            onClick={() => handleDeletePermanent(usuario)}
                            className="text-red-600 hover:text-red-800"
                            title="Excluir definitivamente"
                            disabled={deletePermanentMutation.isPending}
                          >
                            <AlertTriangle className="h-4 w-4 inline" />
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Criar/Editar */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">
                {editingUsuario ? 'Editar Usuário' : 'Novo Usuário'}
              </h2>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="p-6 space-y-4">
                {!editingUsuario && (
                  <div>
                    <Label htmlFor="username">
                      Username <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="username"
                      value={formData.username}
                      onChange={(e) =>
                        setFormData({ ...formData, username: e.target.value })
                      }
                      required
                      maxLength={50}
                    />
                  </div>
                )}

                {editingUsuario && (
                  <div>
                    <Label>Username</Label>
                    <Input value={editingUsuario.username} disabled />
                    <p className="text-xs text-gray-500 mt-1">
                      Username não pode ser alterado
                    </p>
                  </div>
                )}

                {!editingUsuario && (
                  <div>
                    <Label htmlFor="password">
                      Senha <span className="text-red-500">*</span>
                    </Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) =>
                        setFormData({ ...formData, password: e.target.value })
                      }
                      required
                      minLength={8}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Mínimo 8 caracteres
                    </p>
                  </div>
                )}

                {editingUsuario && (
                  <div>
                    <Label htmlFor="password">
                      Nova Senha <span className="text-gray-400 text-xs">(opcional)</span>
                    </Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) =>
                        setFormData({ ...formData, password: e.target.value })
                      }
                      placeholder="Deixe em branco para manter a senha atual"
                      minLength={8}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Preencha apenas se desejar redefinir a senha. Mínimo 8 caracteres.
                    </p>
                  </div>
                )}

                <div>
                  <Label htmlFor="full_name">
                    Nome Completo <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) =>
                      setFormData({ ...formData, full_name: e.target.value })
                    }
                    required
                    maxLength={100}
                  />
                </div>

                <div>
                  <Label htmlFor="email">
                    Email <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, email: e.target.value })
                    }
                    placeholder="usuario@exemplo.com"
                    maxLength={100}
                    required
                    className={
                      triedToSubmit && !formData.email?.trim()
                        ? 'border-red-500'
                        : ''
                    }
                  />
                  {triedToSubmit && !formData.email?.trim() && (
                    <p className="text-xs text-red-500 mt-1">
                      Email é obrigatório
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="role_id">
                    Perfil <span className="text-red-500">*</span>
                  </Label>
                  {isLoadingRoles ? (
                    <div className="text-sm text-gray-500">Carregando perfis...</div>
                  ) : (
                    <Select
                      id="role_id"
                      value={formData.role_id && formData.role_id > 0 ? formData.role_id : ''}
                      onChange={(e) => {
                        const value = e.target.value
                        setFormData({ 
                          ...formData, 
                          role_id: value ? Number(value) : 0 
                        })
                      }}
                      required
                      className={
                        triedToSubmit && (!formData.role_id || formData.role_id === 0)
                          ? 'border-red-500'
                          : ''
                      }
                    >
                      <option value="">Selecione um perfil</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.id}>
                          {role.name} {role.description && `- ${role.description}`}
                        </option>
                      ))}
                    </Select>
                  )}
                  {triedToSubmit && (!formData.role_id || formData.role_id === 0) && (
                    <p className="text-xs text-red-500 mt-1">Por favor, selecione um perfil</p>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) =>
                      setFormData({ ...formData, is_active: e.target.checked })
                    }
                    className="rounded"
                  />
                  <Label htmlFor="is_active">Usuário ativo</Label>
                </div>
              </div>

              <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={closeModal}>
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  disabled={
                    createMutation.isPending || updateMutation.isPending
                  }
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? 'Salvando...'
                    : editingUsuario
                    ? 'Atualizar'
                    : 'Criar'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

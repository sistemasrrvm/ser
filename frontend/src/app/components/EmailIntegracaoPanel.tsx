/**
 * Painel de parametrização SMTP — ticket #248
 */

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Mail, Save, RefreshCw } from 'lucide-react'
import {
  configuracoesApi,
  type EmailIntegracaoSettingsUpdate,
} from '@/lib/api/configuracoes'
import { getApiErrorMessage } from '@/lib/api/client'

const PASSWORD_MASK = '********'

const emptyForm: EmailIntegracaoSettingsUpdate = {
  enabled: true,
  smtp_host: '',
  smtp_port: 465,
  smtp_use_ssl: true,
  smtp_user: '',
  smtp_password: '',
  from_email: '',
  from_name: 'SER - Sistema de Emissão de Relatórios',
  frontend_base_url: '',
}

export function EmailIntegracaoPanel() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<EmailIntegracaoSettingsUpdate>(emptyForm)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['configuracoes', 'email-integracao'],
    queryFn: () => configuracoesApi.getEmailIntegracao(),
  })

  useEffect(() => {
    if (!data) return
    setForm({
      enabled: data.enabled ?? true,
      smtp_host: data.smtp_host || '',
      smtp_port: data.smtp_port ?? 465,
      smtp_use_ssl: data.smtp_use_ssl ?? true,
      smtp_user: data.smtp_user || '',
      smtp_password: data.smtp_password_configured ? PASSWORD_MASK : '',
      from_email: data.from_email || '',
      from_name: data.from_name || 'SER - Sistema de Emissão de Relatórios',
      frontend_base_url: data.frontend_base_url || '',
    })
  }, [data])

  const saveMutation = useMutation({
    mutationFn: (payload: EmailIntegracaoSettingsUpdate) =>
      configuracoesApi.updateEmailIntegracao(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configuracoes', 'email-integracao'] })
      queryClient.invalidateQueries({ queryKey: ['configuracoes'] })
      alert('Configuração de e-mail salva com sucesso!')
    },
    onError: (err: unknown) => {
      alert(getApiErrorMessage(err, 'Erro ao salvar configuração de e-mail'))
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.smtp_host?.trim() || !form.smtp_user?.trim() || !form.from_email?.trim()) {
      alert('Servidor SMTP, usuário e e-mail remetente são obrigatórios')
      return
    }
    saveMutation.mutate(form)
  }

  const sourceLabel =
    data?.source === 'database'
      ? 'Banco de dados'
      : data?.source === 'mixed'
        ? 'Banco + ambiente'
        : data?.source === 'env'
          ? 'Variáveis de ambiente'
          : data?.source || '-'

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-slate-50">
        <div className="flex items-center gap-3">
          <Mail className="w-6 h-6 text-emerald-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Notificações por E-mail (SMTP)</h2>
            <p className="text-sm text-gray-600">
              Envio automático ao avançar o fluxo de relatórios
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {data?.configured ? (
            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
              Configurado
            </span>
          ) : (
            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-amber-100 text-amber-800">
              Pendente
            </span>
          )}
          <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">
            Origem: {sourceLabel}
          </span>
        </div>
      </div>

      {isLoading && (
        <div className="px-6 py-8 text-center text-gray-600">Carregando configuração SMTP...</div>
      )}

      {error && (
        <div className="mx-6 my-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          Erro ao carregar parâmetros SMTP
        </div>
      )}

      {!isLoading && !error && (
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.enabled ?? true}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
              className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
            />
            Envio de e-mails habilitado
          </label>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Servidor SMTP *
              </label>
              <input
                type="text"
                value={form.smtp_host}
                onChange={(e) => setForm({ ...form, smtp_host: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="mail.rrvm.com.br"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Porta</label>
              <input
                type="number"
                min={1}
                max={65535}
                value={form.smtp_port ?? 465}
                onChange={(e) =>
                  setForm({ ...form, smtp_port: parseInt(e.target.value, 10) || 465 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Usuário SMTP *
              </label>
              <input
                type="text"
                value={form.smtp_user}
                onChange={(e) => setForm({ ...form, smtp_user: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="ser@rrvm.com.br"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Senha SMTP
                {data?.smtp_password_configured && (
                  <span className="text-gray-400 font-normal ml-1">— deixe ******** para manter</span>
                )}
              </label>
              <input
                type="password"
                value={form.smtp_password || ''}
                onChange={(e) => setForm({ ...form, smtp_password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder={data?.smtp_password_configured ? PASSWORD_MASK : 'Senha SMTP'}
                autoComplete="new-password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                E-mail remetente (From) *
              </label>
              <input
                type="email"
                value={form.from_email}
                onChange={(e) => setForm({ ...form, from_email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome remetente</label>
              <input
                type="text"
                value={form.from_name || ''}
                onChange={(e) => setForm({ ...form, from_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL do frontend (links nos e-mails)
              </label>
              <input
                type="url"
                value={form.frontend_base_url || ''}
                onChange={(e) => setForm({ ...form, frontend_base_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="https://laudonr13-frontend-prod.up.railway.app"
              />
            </div>

            <div className="md:col-span-2">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={form.smtp_use_ssl ?? true}
                  onChange={(e) => setForm({ ...form, smtp_use_ssl: e.target.checked })}
                  className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                />
                Usar SSL (porta 465 — desmarque para STARTTLS na porta 587)
              </label>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saveMutation.isPending ? 'Salvando...' : 'Salvar SMTP'}
            </button>
            <button
              type="button"
              onClick={() => refetch()}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition"
            >
              <RefreshCw className="w-4 h-4" />
              Recarregar
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

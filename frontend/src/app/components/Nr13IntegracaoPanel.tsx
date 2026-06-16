/**
 * Painel de parametrização da integração NR13 (API Botset) — ticket #292
 */

import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link2, Save, RefreshCw, Zap } from 'lucide-react'
import {
  configuracoesApi,
  type Nr13IntegracaoSettingsUpdate,
} from '@/lib/api/configuracoes'
import { getApiErrorMessage } from '@/lib/api/client'

const PASSWORD_MASK = '********'

const emptyForm: Nr13IntegracaoSettingsUpdate = {
  api_base_url: '',
  basic_user: '',
  basic_password: '',
  equipamento_tipo: '12',
  data_ref_days_back: 2,
  cron_secret: '',
  timeout_seconds: 120,
  enabled: true,
}

export function Nr13IntegracaoPanel() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<Nr13IntegracaoSettingsUpdate>(emptyForm)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['configuracoes', 'nr13-integracao'],
    queryFn: () => configuracoesApi.getNr13Integracao(),
  })

  useEffect(() => {
    if (!data) return
    setForm({
      api_base_url: data.api_base_url || '',
      basic_user: data.basic_user || '',
      basic_password: data.basic_password_configured ? PASSWORD_MASK : '',
      equipamento_tipo: data.equipamento_tipo || '12',
      data_ref_days_back: data.data_ref_days_back ?? 2,
      cron_secret: data.cron_secret_configured ? PASSWORD_MASK : '',
      timeout_seconds: data.timeout_seconds ?? 120,
      enabled: data.enabled ?? true,
    })
  }, [data])

  const saveMutation = useMutation({
    mutationFn: (payload: Nr13IntegracaoSettingsUpdate) =>
      configuracoesApi.updateNr13Integracao(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['configuracoes', 'nr13-integracao'] })
      queryClient.invalidateQueries({ queryKey: ['configuracoes'] })
      alert('Integração NR13 salva com sucesso!')
    },
    onError: (err: unknown) => {
      alert(getApiErrorMessage(err, 'Erro ao salvar integração NR13'))
    },
  })

  const testMutation = useMutation({
    mutationFn: () => configuracoesApi.testNr13Integracao(),
    onSuccess: (result) => {
      alert(`${result.message}\n\nURL: ${result.request_url}\ndataRef: ${result.data_ref}`)
    },
    onError: (err: unknown) => {
      alert(getApiErrorMessage(err, 'Falha no teste de conexão NR13'))
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.api_base_url?.trim() || !form.basic_user?.trim()) {
      alert('URL da API e usuário são obrigatórios')
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
          <Link2 className="w-6 h-6 text-indigo-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Integração NR13 (API Botset)</h2>
            <p className="text-sm text-gray-600">
              Parâmetros para sincronização de clientes e equipamentos
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {data?.configured ? (
            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
              Configurada
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
        <div className="px-6 py-8 text-center text-gray-600">Carregando integração NR13...</div>
      )}

      {error && (
        <div className="mx-6 my-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          Erro ao carregar parâmetros da integração NR13
        </div>
      )}

      {!isLoading && !error && (
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.enabled ?? true}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            Integração habilitada
          </label>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL base da API *
              </label>
              <input
                type="url"
                value={form.api_base_url}
                onChange={(e) => setForm({ ...form, api_base_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="https://bpm.api.botset.net/api/callback/RRVMNR13/RRVMNR13/cadastros"
                required
              />
              {data?.api_base_url_resolved && data.api_base_url_resolved !== form.api_base_url && (
                <p className="text-xs text-amber-700 mt-1">
                  URL normalizada: {data.api_base_url_resolved}/clientes
                </p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Use a base até <code>/cadastros</code> (sem <code>/clientes</code> no final).
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Usuário (Basic Auth) *
              </label>
              <input
                type="text"
                value={form.basic_user}
                onChange={(e) => setForm({ ...form, basic_user: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Senha (Basic Auth)
                {data?.basic_password_configured && (
                  <span className="text-gray-400 font-normal ml-1">— deixe ******** para manter</span>
                )}
              </label>
              <input
                type="password"
                value={form.basic_password || ''}
                onChange={(e) => setForm({ ...form, basic_password: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder={data?.basic_password_configured ? PASSWORD_MASK : 'Senha da API'}
                autoComplete="new-password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de equipamento
              </label>
              <input
                type="text"
                value={form.equipamento_tipo || '12'}
                onChange={(e) => setForm({ ...form, equipamento_tipo: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">Valor enviado como equipamentoTipo na API</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dias retroativos (dataRef)
              </label>
              <input
                type="number"
                min={0}
                value={form.data_ref_days_back ?? 2}
                onChange={(e) =>
                  setForm({ ...form, data_ref_days_back: parseInt(e.target.value, 10) || 0 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">dataRef = hoje − N dias (fuso SP)</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Secret carga noturna (X-Cron-Secret)
              </label>
              <input
                type="password"
                value={form.cron_secret || ''}
                onChange={(e) => setForm({ ...form, cron_secret: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder={data?.cron_secret_configured ? PASSWORD_MASK : 'Secret para cron'}
                autoComplete="new-password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timeout (segundos)
              </label>
              <input
                type="number"
                min={10}
                max={600}
                step={1}
                value={form.timeout_seconds ?? 120}
                onChange={(e) =>
                  setForm({ ...form, timeout_seconds: parseFloat(e.target.value) || 120 })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saveMutation.isPending ? 'Salvando...' : 'Salvar integração'}
            </button>
            <button
              type="button"
              onClick={() => testMutation.mutate()}
              disabled={testMutation.isPending || saveMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition disabled:opacity-50"
            >
              <Zap className="w-4 h-4" />
              {testMutation.isPending ? 'Testando...' : 'Testar conexão'}
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

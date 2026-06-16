/**
 * Painel de teste de e-mail do fluxo — ticket #248
 */

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Send, Zap, CheckCircle2, XCircle } from 'lucide-react'
import {
  configuracoesApi,
  type EmailIntegracaoTestRequest,
  type EmailIntegracaoTestResult,
} from '@/lib/api/configuracoes'
import { reportsApi } from '@/lib/api/reports'

const EVENTOS: { value: EmailIntegracaoTestRequest['evento']; label: string }[] = [
  { value: 'finalizar', label: 'Finalizar (aguardando revisão)' },
  { value: 'solicitar_correcao', label: 'Solicitar correção' },
  { value: 'aprovar', label: 'Aprovar relatório' },
]

export function EmailTestPanel() {
  const [reportId, setReportId] = useState<number | ''>('')
  const [evento, setEvento] = useState<EmailIntegracaoTestRequest['evento']>('finalizar')
  const [destinatario, setDestinatario] = useState('')
  const [lastResult, setLastResult] = useState<EmailIntegracaoTestResult | null>(null)

  const { data: reportsData, isLoading: loadingReports } = useQuery({
    queryKey: ['reports', 'email-test'],
    queryFn: () => reportsApi.list({ limit: 20, page: 1 }),
  })

  const testMutation = useMutation({
    mutationFn: (payload: EmailIntegracaoTestRequest) =>
      configuracoesApi.testEmailIntegracao(payload),
    onSuccess: (result) => {
      setLastResult(result)
    },
    onError: () => {
      setLastResult({
        success: false,
        message: 'Falha na comunicação com o servidor',
        subject: '',
        destinatario: '',
        log: ['ERRO: Não foi possível concluir a requisição HTTP (rede ou servidor indisponível)'],
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reportId || !destinatario.trim()) {
      alert('Selecione um relatório e informe o e-mail de teste')
      return
    }
    setLastResult(null)
    testMutation.mutate({
      report_id: Number(reportId),
      evento,
      destinatario_teste: destinatario.trim(),
    })
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6 overflow-hidden">
      <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-200 bg-slate-50">
        <Zap className="w-6 h-6 text-amber-600" />
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Testar envio de e-mail</h2>
          <p className="text-sm text-gray-600">
            Simula um evento do fluxo e envia apenas para o destinatário informado
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Relatório *</label>
            <select
              value={reportId}
              onChange={(e) =>
                setReportId(e.target.value ? parseInt(e.target.value, 10) : '')
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              disabled={loadingReports}
              required
            >
              <option value="">Selecione...</option>
              {reportsData?.reports?.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.numero} — {r.cliente_nome || 'Sem cliente'} ({r.status})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Evento *</label>
            <select
              value={evento}
              onChange={(e) =>
                setEvento(e.target.value as EmailIntegracaoTestRequest['evento'])
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            >
              {EVENTOS.map((ev) => (
                <option key={ev.value} value={ev.value}>
                  {ev.label}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Destinatário de teste *
            </label>
            <input
              type="email"
              value={destinatario}
              onChange={(e) => setDestinatario(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              placeholder="seu-email@example.com"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              O e-mail não será enviado aos usuários reais do fluxo (Suporte/Técnico).
            </p>
          </div>
        </div>

        <button
          type="submit"
          disabled={testMutation.isPending || loadingReports}
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
          {testMutation.isPending ? 'Enviando...' : 'Enviar e-mail de teste'}
        </button>
      </form>

      {lastResult && (
        <div
          className={`mx-6 mb-6 rounded-lg border p-4 ${
            lastResult.success
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}
        >
          <div className="flex items-start gap-2 mb-3">
            {lastResult.success ? (
              <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            )}
            <div>
              <p
                className={`font-medium ${
                  lastResult.success ? 'text-green-800' : 'text-red-800'
                }`}
              >
                {lastResult.message}
              </p>
              {lastResult.subject && (
                <p className="text-sm text-gray-600 mt-1">Assunto: {lastResult.subject}</p>
              )}
              {lastResult.destinatario && (
                <p className="text-sm text-gray-600">Destinatário: {lastResult.destinatario}</p>
              )}
            </div>
          </div>

          {lastResult.log.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Log de execução
              </p>
              <ol className="text-sm font-mono bg-white/80 rounded border border-gray-200 p-3 space-y-1 max-h-64 overflow-y-auto">
                {lastResult.log.map((line, index) => (
                  <li
                    key={index}
                    className={
                      line.startsWith('ERRO:') ? 'text-red-700 font-semibold' : 'text-gray-700'
                    }
                  >
                    {index + 1}. {line}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

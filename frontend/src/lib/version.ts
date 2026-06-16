/**
 * Sistema de versionamento do frontend
 * Hash do código fonte - mudanças no código alteram este hash
 */

// Hash do código fonte será injetado no build time pelo Vite
declare const __FRONTEND_CODE_HASH__: string | undefined

class FrontendVersion {
  private backendCodeHash: string | null = null
  private readonly frontendCodeHash: string

  constructor() {
    // Hash do código fonte (injeta no build ou usa fallback em dev)
    this.frontendCodeHash = this.getFrontendCodeHash()
  }

  private getFrontendCodeHash(): string {
    // Em produção: hash injetado no build time pelo Vite
    if (typeof __FRONTEND_CODE_HASH__ !== 'undefined' && __FRONTEND_CODE_HASH__) {
      return __FRONTEND_CODE_HASH__
    }
    
    // Em DEV: gerar hash baseado no código carregado (vai mudar a cada reload)
    // Usar hash do código fonte real, não timestamp
    const codeStr = this.getSourceCodeForHash()
    return this.hashString(codeStr).substring(0, 8)
  }

  private getSourceCodeForHash(): string {
    // Coletar strings de identificação do código para gerar hash
    // Em dev, vai mudar a cada reload de página
    return [
      typeof window !== 'undefined' ? window.location.href : '',
      typeof document !== 'undefined' ? document.scripts.length.toString() : '',
      Date.now().toString() // Fallback temporário para dev
    ].join('|')
  }

  private hashString(str: string): string {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return Math.abs(hash).toString(16).padStart(8, '0')
  }

  getFrontendId(): string {
    return this.frontendCodeHash
  }

  async fetchBackendVersion(): Promise<void> {
    try {
      const response = await fetch('/api/v1')
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      
      // Usar code_hash ou instance_id (compatibilidade)
      this.backendCodeHash = data.code_hash || data.instance_id || 'unknown'
      
      this.logVersions('✅ Versões carregadas com sucesso')
    } catch (error: any) {
      this.backendCodeHash = 'erro-conexao'
      const errorMsg = error?.message || String(error)
      console.error('[VERSOES] Erro ao buscar versão do backend:', errorMsg)
    }
  }

  private logVersions(_message: string): void {
    // Versões disponíveis via getFrontendId() / getBackendId() se necessário
  }

  getBackendId(): string {
    return this.backendCodeHash || 'aguardando...'
  }

  getLogPrefix(): string {
    const frontId = this.getFrontendId()
    const backId = this.getBackendId()
    return `[F:${frontId}|B:${backId}]`
  }
}

// Instância global
export const frontendVersion = new FrontendVersion()

// Buscar versão do backend automaticamente
frontendVersion.fetchBackendVersion()

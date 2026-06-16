/**
 * Plugin Vite para gerar hash do código fonte do frontend
 * Injeta __FRONTEND_CODE_HASH__ no código durante o build
 */

import { Plugin } from 'vite'
import { createHash } from 'crypto'
import { readdirSync, readFileSync, statSync } from 'fs'
import { join, relative } from 'path'

interface Options {
  root?: string
  include?: string[]
  exclude?: string[]
}

export function codeHashPlugin(options: Options = {}): Plugin {
  const root = options.root || process.cwd()
  const include = options.include || ['src/**/*.{ts,tsx,js,jsx}']
  const exclude = options.exclude || ['**/node_modules/**', '**/dist/**', '**/*.d.ts']

  return {
    name: 'vite-plugin-code-hash',
    buildStart() {
      // Gerar hash do código fonte
      const hash = generateCodeHash(root, include, exclude)
      
      // Injetar no código via define
      this.emitFile({
        type: 'asset',
        fileName: 'code-hash.json',
        source: JSON.stringify({ hash })
      })
    },
    configResolved(config) {
      // Gerar hash e definir variável global
      const hash = generateCodeHash(root, include, exclude)
      
      // Adicionar define para injetar no código
      config.define = config.define || {}
      config.define.__FRONTEND_CODE_HASH__ = JSON.stringify(hash)
    }
  }
}

function generateCodeHash(
  root: string,
  include: string[],
  exclude: string[]
): string {
  const srcDir = join(root, 'src')
  const files: string[] = []
  
  function collectFiles(dir: string, baseDir: string = srcDir): void {
    try {
      const entries = readdirSync(dir)
      
      for (const entry of entries) {
        const fullPath = join(dir, entry)
        const relPath = relative(baseDir, fullPath)
        const stat = statSync(fullPath)
        
        // Ignorar arquivos/diretórios excluídos
        if (shouldExclude(relPath, exclude)) {
          continue
        }
        
        if (stat.isDirectory()) {
          collectFiles(fullPath, baseDir)
        } else if (stat.isFile()) {
          // Incluir apenas arquivos TypeScript/JavaScript
          if (/\.(ts|tsx|js|jsx)$/.test(entry)) {
            files.push(fullPath)
          }
        }
      }
    } catch (error) {
      // Ignorar erros de leitura
      console.warn(`Warning: Could not read directory ${dir}:`, error)
    }
  }
  
  collectFiles(srcDir)
  
  // Ordenar arquivos para garantir hash consistente
  files.sort()
  
  // Ler conteúdo de todos os arquivos e gerar hash
  const hash = createHash('md5')
  
  for (const file of files) {
    try {
      const content = readFileSync(file, 'utf-8')
      hash.update(file)
      hash.update(content)
    } catch (error) {
      // Ignorar erros de leitura
      console.warn(`Warning: Could not read file ${file}:`, error)
    }
  }
  
  return hash.digest('hex').substring(0, 8)
}

function shouldExclude(path: string, exclude: string[]): boolean {
  return exclude.some(pattern => {
    const regex = new RegExp(
      pattern
        .replace(/\*\*/g, '.*')
        .replace(/\*/g, '[^/]*')
        .replace(/\//g, '\\/')
    )
    return regex.test(path)
  })
}


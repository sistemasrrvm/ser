/**
 * Botão de sincronização NR13 com opções: recentes (x dias) ou sem filtro de data.
 */

import { useEffect, useRef, useState } from 'react'
import { ChevronDown, Download } from 'lucide-react'

export type Nr13SyncMode = 'recent' | 'all'

interface Nr13SyncButtonProps {
  daysBack: number
  isPending?: boolean
  onSync: (mode: Nr13SyncMode) => void
}

export function Nr13SyncButton({
  daysBack,
  isPending = false,
  onSync,
}: Nr13SyncButtonProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handleClickOutside = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [open])

  const recentLabel = `Registros Recentes (${daysBack} ${daysBack === 1 ? 'dia' : 'dias'})`

  const handleSelect = (mode: Nr13SyncMode) => {
    setOpen(false)
    onSync(mode)
  }

  return (
    <div ref={rootRef} className="relative inline-flex">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        disabled={isPending}
        className="btn-primary flex items-center gap-2 rounded-r-none border-r border-blue-500/40"
      >
        <Download size={16} className={isPending ? 'animate-spin' : ''} />
        Sincronizar NR13
      </button>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        disabled={isPending}
        aria-label="Opções de sincronização NR13"
        className="btn-primary px-2 rounded-l-none"
      >
        <ChevronDown size={16} className={open ? 'rotate-180 transition-transform' : 'transition-transform'} />
      </button>

      {open && !isPending && (
        <div className="absolute right-0 top-full z-20 mt-1 min-w-[260px] rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
          <button
            type="button"
            onClick={() => handleSelect('recent')}
            className="w-full px-4 py-2.5 text-left text-sm text-gray-800 hover:bg-blue-50"
          >
            {recentLabel}
          </button>
          <button
            type="button"
            onClick={() => handleSelect('all')}
            className="w-full px-4 py-2.5 text-left text-sm text-gray-800 hover:bg-blue-50 border-t border-gray-100"
          >
            Sem filtro de Data
          </button>
        </div>
      )}
    </div>
  )
}

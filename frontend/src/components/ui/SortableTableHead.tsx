import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'
import type { SortDirection } from '@/hooks/useTableSort'

interface SortableTableHeadProps {
  label: string
  column: string
  activeColumn: string
  direction: SortDirection
  onSort: (column: string) => void
  align?: 'left' | 'center' | 'right'
  className?: string
}

export function SortableTableHead({
  label,
  column,
  activeColumn,
  direction,
  onSort,
  align = 'left',
  className = '',
}: SortableTableHeadProps) {
  const isActive = activeColumn === column
  const alignClass =
    align === 'center' ? 'text-center' : align === 'right' ? 'text-right' : 'text-left'

  return (
    <th
      className={`px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider ${alignClass} ${className}`}
    >
      <button
        type="button"
        onClick={() => onSort(column)}
        className={`inline-flex items-center gap-1 hover:text-gray-800 transition-colors ${
          align === 'center' ? 'mx-auto' : align === 'right' ? 'ml-auto' : ''
        } ${isActive ? 'text-gray-800' : ''}`}
      >
        <span>{label}</span>
        {isActive ? (
          direction === 'asc' ? (
            <ArrowUp size={14} className="shrink-0" />
          ) : (
            <ArrowDown size={14} className="shrink-0" />
          )
        ) : (
          <ArrowUpDown size={14} className="shrink-0 opacity-40" />
        )}
      </button>
    </th>
  )
}

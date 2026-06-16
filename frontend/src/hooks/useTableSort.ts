import { useCallback, useState } from 'react'

export type SortDirection = 'asc' | 'desc'

export function useTableSort(defaultColumn: string, defaultDir: SortDirection = 'asc') {
  const [sortBy, setSortBy] = useState(defaultColumn)
  const [sortDir, setSortDir] = useState<SortDirection>(defaultDir)

  const toggleSort = useCallback((column: string) => {
    setSortBy((current) => {
      if (current === column) {
        setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'))
        return current
      }
      setSortDir('asc')
      return column
    })
  }, [])

  return { sortBy, sortDir, toggleSort }
}

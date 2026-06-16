import { useCallback, useState } from 'react'

export type ReportListingViewMode = 'list' | 'kanban'

const STORAGE_KEY = 'ser:list:relatorios:view'

function readViewMode(): ReportListingViewMode {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    if (value === 'kanban') return 'kanban'
  } catch {
    /* noop */
  }
  return 'list'
}

function writeViewMode(mode: ReportListingViewMode) {
  try {
    localStorage.setItem(STORAGE_KEY, mode)
  } catch {
    /* noop */
  }
}

export function useReportListingPrefs() {
  const [viewMode, setViewModeState] = useState<ReportListingViewMode>(readViewMode)

  const setViewMode = useCallback((mode: ReportListingViewMode) => {
    setViewModeState(mode)
    writeViewMode(mode)
  }, [])

  return { viewMode, setViewMode }
}

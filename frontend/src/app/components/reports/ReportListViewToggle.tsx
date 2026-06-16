import { Button } from '@/components/ui/button'
import type { ReportListingViewMode } from '@/hooks/useReportListingPrefs'
import { Columns3, Table2 } from 'lucide-react'

type Props = {
  viewMode: ReportListingViewMode
  onViewModeChange: (mode: ReportListingViewMode) => void
}

export function ReportListViewToggle({ viewMode, onViewModeChange }: Props) {
  return (
    <div className="flex items-center gap-1 rounded-md border border-gray-200 bg-gray-50 p-0.5">
      <Button
        type="button"
        variant={viewMode === 'list' ? 'default' : 'ghost'}
        size="sm"
        className="h-8 px-2.5"
        onClick={() => onViewModeChange('list')}
        aria-pressed={viewMode === 'list'}
        title="Lista"
      >
        <Table2 className="h-4 w-4" />
        <span className="ml-1.5 hidden sm:inline">Lista</span>
      </Button>
      <Button
        type="button"
        variant={viewMode === 'kanban' ? 'default' : 'ghost'}
        size="sm"
        className="h-8 px-2.5"
        onClick={() => onViewModeChange('kanban')}
        aria-pressed={viewMode === 'kanban'}
        title="Kanban"
      >
        <Columns3 className="h-4 w-4" />
        <span className="ml-1.5 hidden sm:inline">Kanban</span>
      </Button>
    </div>
  )
}

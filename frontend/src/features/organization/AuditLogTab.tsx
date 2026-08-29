import * as React from 'react'
import { Eye } from 'lucide-react'

import { useAuditLog } from '@/features/audit/api'
import type { AuditLogEntry, AuditLogFilters } from '@/features/audit/types'
import { ApiError } from '@/lib/api-client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'

function Json({ value }: { value: unknown }) {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground">—</span>
  }
  return (
    <pre className="max-h-64 overflow-auto rounded-md bg-muted p-2 text-xs">
      {JSON.stringify(value, null, 2)}
    </pre>
  )
}

function DiffDialog({
  entry,
  onOpenChange,
}: {
  entry: AuditLogEntry | null
  onOpenChange: (open: boolean) => void
}) {
  if (!entry) return null
  return (
    <Dialog open={Boolean(entry)} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {entry.action} · {entry.entity_type}
          </DialogTitle>
          <DialogDescription>
            {entry.actor ?? 'Unknown actor'} · {new Date(entry.timestamp).toLocaleString()}
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <p className="mb-1 text-xs font-medium text-muted-foreground">Before</p>
            <Json value={entry.previous_value_json} />
          </div>
          <div>
            <p className="mb-1 text-xs font-medium text-muted-foreground">After</p>
            <Json value={entry.new_value_json} />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

const ACTION_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  create: 'secondary',
  update: 'default',
  delete: 'destructive',
}

function actionVariant(action: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  const key = action.split('.').pop() ?? action
  return ACTION_VARIANT[key] ?? 'outline'
}

export function AuditLogTab() {
  const [filters, setFilters] = React.useState<AuditLogFilters>({})
  const [selected, setSelected] = React.useState<AuditLogEntry | null>(null)
  const { data, isLoading, error } = useAuditLog(filters)

  const columns: DataTableColumn<AuditLogEntry>[] = [
    {
      key: 'timestamp',
      header: 'When',
      render: (row) => new Date(row.timestamp).toLocaleString(),
      className: 'whitespace-nowrap',
      sortValue: (row) => new Date(row.timestamp),
      exportValue: (row) => row.timestamp,
    },
    {
      key: 'actor',
      header: 'Actor',
      render: (row) => row.actor ?? <span className="text-muted-foreground">Unknown</span>,
      sortValue: (row) => row.actor ?? '',
      exportValue: (row) => row.actor ?? '',
    },
    {
      key: 'action',
      header: 'Action',
      render: (row) => <Badge variant={actionVariant(row.action)}>{row.action}</Badge>,
      sortValue: (row) => row.action,
    },
    {
      key: 'entity',
      header: 'Entity',
      render: (row) => (
        <span className="font-mono text-xs">
          {row.entity_type}
          {row.entity_id ? ` · ${row.entity_id.slice(0, 8)}…` : ''}
        </span>
      ),
      sortValue: (row) => row.entity_type,
      exportValue: (row) => `${row.entity_type}${row.entity_id ? ` (${row.entity_id})` : ''}`,
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="audit-entity-type">
            Entity type
          </label>
          <Input
            id="audit-entity-type"
            placeholder="e.g. Assessment"
            className="w-40"
            value={filters.entity_type ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, entity_type: e.target.value || undefined }))
            }
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="audit-action">
            Action
          </label>
          <Input
            id="audit-action"
            placeholder="e.g. update"
            className="w-40"
            value={filters.action ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, action: e.target.value || undefined }))}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="audit-from">
            From
          </label>
          <Input
            id="audit-from"
            type="date"
            className="w-40"
            value={filters.date_from?.slice(0, 10) ?? ''}
            onChange={(e) =>
              setFilters((f) => ({ ...f, date_from: e.target.value || undefined }))
            }
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="audit-to">
            To
          </label>
          <Input
            id="audit-to"
            type="date"
            className="w-40"
            value={filters.date_to?.slice(0, 10) ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value || undefined }))}
          />
        </div>
        {(filters.entity_type || filters.action || filters.date_from || filters.date_to) && (
          <Button variant="ghost" size="sm" onClick={() => setFilters({})}>
            Clear filters
          </Button>
        )}
      </div>

      <DataTable
        data={data}
        columns={columns}
        rowKey={(row) => row.id}
        isLoading={isLoading}
        error={error instanceof ApiError ? new Error(error.detail) : error}
        emptyMessage="No audit activity matches these filters."
        pageSize={20}
        density
        exportable
        exportFilename="audit-log"
        actions={(row) => (
          <Button variant="ghost" size="sm" onClick={() => setSelected(row)}>
            <Eye className="size-4" /> Diff
          </Button>
        )}
      />

      <DiffDialog entry={selected} onOpenChange={(open) => !open && setSelected(null)} />
    </div>
  )
}

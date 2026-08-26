import * as React from 'react'
import { X } from 'lucide-react'

import type { MappingScale } from '@/features/curriculum/types'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Skeleton } from '@/components/ui/skeleton'

export interface MatrixItem {
  id: string
  code: string
  label: string
}

export interface MatrixCell {
  /** The mapping row id, needed to DELETE it (backend has no PATCH for
   * mappings — changing a level means delete-then-recreate). */
  mappingId: string
  levelId: string
}

interface MappingMatrixProps {
  rows: MatrixItem[]
  cols: MatrixItem[]
  rowHeader: string
  colHeader: string
  scale: MappingScale | undefined
  /** key: `${rowId}:${colId}` */
  cells: Map<string, MatrixCell>
  isLoading?: boolean
  readOnly?: boolean
  onSetCell: (rowId: string, colId: string, levelId: string) => Promise<void>
  onClearCell: (rowId: string, colId: string, mappingId: string) => Promise<void>
}

/**
 * Heatmap-style CO-PO / PEO-PO mapping matrix — the flagship UI of this
 * pass (spec §19/§35). Click a cell to pick a mapping-scale level (or clear
 * it). Color intensity scales with the level's numeric value.
 */
export function MappingMatrix({
  rows,
  cols,
  rowHeader,
  colHeader,
  scale,
  cells,
  isLoading,
  readOnly,
  onSetCell,
  onClearCell,
}: MappingMatrixProps) {
  const levels = React.useMemo(
    () => [...(scale?.levels ?? [])].sort((a, b) => a.value - b.value),
    [scale],
  )
  const maxValue = levels.length > 0 ? Math.max(...levels.map((l) => l.value), 1) : 1

  if (isLoading) {
    return <Skeleton className="h-80 w-full" />
  }

  if (rows.length === 0 || cols.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Need at least one {rowHeader.toLowerCase()} and one {colHeader.toLowerCase()} to build the
        matrix.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {levels.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          <span>Legend:</span>
          {levels.map((l) => (
            <span key={l.id} className="flex items-center gap-1.5">
              <span
                className="inline-block size-3 rounded-sm border"
                style={{ backgroundColor: heatColor(l.value, maxValue) }}
              />
              {l.label} ({l.value})
            </span>
          ))}
        </div>
      )}

      <div className="overflow-auto rounded-md border">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="sticky left-0 z-10 min-w-40 border-b border-r bg-muted/50 p-2 text-left font-medium">
                {rowHeader} \ {colHeader}
              </th>
              {cols.map((c) => (
                <th
                  key={c.id}
                  className="min-w-16 border-b p-2 text-center font-medium"
                  title={c.label}
                >
                  {c.code}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <th
                  className="sticky left-0 z-10 border-r bg-background p-2 text-left font-medium"
                  title={row.label}
                >
                  {row.code}
                </th>
                {cols.map((col) => {
                  const key = `${row.id}:${col.id}`
                  const cell = cells.get(key)
                  const level = levels.find((l) => l.id === cell?.levelId)
                  return (
                    <td key={col.id} className="border-b border-l p-1 text-center">
                      <MatrixCellButton
                        levels={levels}
                        maxValue={maxValue}
                        currentLevelId={cell?.levelId ?? null}
                        currentLevelLabel={level?.label}
                        readOnly={readOnly}
                        onPick={(levelId) => onSetCell(row.id, col.id, levelId)}
                        onClear={cell ? () => onClearCell(row.id, col.id, cell.mappingId) : undefined}
                      />
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function heatColor(value: number, maxValue: number): string {
  if (value <= 0) return 'transparent'
  const ratio = Math.min(1, value / maxValue)
  // Primary-ish blue ramp, light -> saturated. Works acceptably in both themes
  // since it's used as an inline background behind dark text.
  const alpha = 0.18 + ratio * 0.62
  return `rgba(37, 99, 235, ${alpha.toFixed(2)})`
}

function MatrixCellButton({
  levels,
  maxValue,
  currentLevelId,
  currentLevelLabel,
  readOnly,
  onPick,
  onClear,
}: {
  levels: MappingScale['levels']
  maxValue: number
  currentLevelId: string | null
  currentLevelLabel: string | undefined
  readOnly?: boolean
  onPick: (levelId: string) => void
  onClear: (() => void) | undefined
}) {
  const [open, setOpen] = React.useState(false)
  const [pending, setPending] = React.useState(false)
  const currentLevel = levels.find((l) => l.id === currentLevelId)

  if (readOnly) {
    return (
      <div
        className="flex size-9 items-center justify-center rounded-sm border text-xs font-medium"
        style={{ backgroundColor: heatColor(currentLevel?.value ?? 0, maxValue) }}
        title={currentLevelLabel ?? 'Not mapped'}
      >
        {currentLevel?.value ?? ''}
      </div>
    )
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            'flex size-9 items-center justify-center rounded-sm border text-xs font-medium transition-colors hover:ring-2 hover:ring-ring',
          )}
          style={{ backgroundColor: heatColor(currentLevel?.value ?? 0, maxValue) }}
          title={currentLevelLabel ?? 'Not mapped — click to set'}
        >
          {currentLevel?.value ?? ''}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-48 p-2">
        <div className="flex flex-col gap-1">
          {levels.length === 0 ? (
            <p className="px-1 py-1 text-xs text-muted-foreground">No mapping scale levels found.</p>
          ) : (
            levels.map((l) => (
              <button
                key={l.id}
                type="button"
                disabled={pending}
                className={cn(
                  'flex items-center justify-between rounded px-2 py-1.5 text-left text-sm hover:bg-accent',
                  currentLevelId === l.id && 'bg-accent',
                )}
                onClick={async () => {
                  setPending(true)
                  try {
                    await onPick(l.id)
                    setOpen(false)
                  } finally {
                    setPending(false)
                  }
                }}
              >
                <span className="flex items-center gap-2">
                  <span
                    className="inline-block size-3 rounded-sm border"
                    style={{ backgroundColor: heatColor(l.value, maxValue) }}
                  />
                  {l.label}
                </span>
                <span className="text-muted-foreground">{l.value}</span>
              </button>
            ))
          )}
          {onClear && (
            <Button
              size="sm"
              variant="ghost"
              disabled={pending}
              className="mt-1 justify-start text-muted-foreground"
              onClick={async () => {
                setPending(true)
                try {
                  await onClear()
                  setOpen(false)
                } finally {
                  setPending(false)
                }
              }}
            >
              <X className="size-3.5" /> Clear
            </Button>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}

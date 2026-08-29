import * as React from 'react'
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Columns3,
  Download,
  Inbox,
  Rows3,
  Search,
  X,
} from 'lucide-react'

import { cn } from '@/lib/utils'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Skeleton } from '@/components/ui/skeleton'

export interface DataTableColumn<T> {
  key: string
  header: string
  render: (row: T) => React.ReactNode
  className?: string
  /** Only used when `searchKeys` is not supplied — falls back to stringifying this accessor. */
  searchValue?: (row: T) => string
  /** Enables click-to-sort on this column's header. Return a string, number, or Date. */
  sortValue?: (row: T) => string | number | Date | null | undefined
  /** Text used for CSV export; falls back to `searchValue`, then rendered text. */
  exportValue?: (row: T) => string
  /** Set false to keep this column always visible (exempt from the column-visibility menu). */
  hideable?: boolean
}

type Density = 'comfortable' | 'compact'

const DENSITY_CELL_CLASS: Record<Density, string> = {
  comfortable: '',
  compact: 'py-1.5',
}

interface DataTableProps<T> {
  data: T[] | undefined
  columns: DataTableColumn<T>[]
  rowKey: (row: T) => string
  isLoading?: boolean
  error?: unknown
  /** Enables the client-side search box; matched against `searchValue` (or all string cells) of each row. */
  searchable?: boolean
  searchPlaceholder?: string
  emptyMessage?: string
  pageSize?: number
  onRowClick?: (row: T) => void
  actions?: (row: T) => React.ReactNode
  toolbar?: React.ReactNode
  /** Shows a "Columns" toggle in the toolbar for columns with `hideable !== false`. */
  columnVisibility?: boolean
  /** Shows a compact/comfortable row-density toggle in the toolbar. */
  density?: boolean
  /** Shows a "Export CSV" button in the toolbar, exporting all filtered+sorted rows (not just the current page). */
  exportable?: boolean
  /** Filename (without extension) used for CSV export. Defaults to "export". */
  exportFilename?: string
  /** Adds a selection checkbox column. Combine with `bulkActions`. */
  selectable?: boolean
  /** Rendered in place of the toolbar while 1+ rows are selected (only relevant when `selectable`). */
  bulkActions?: (selectedRows: T[], clearSelection: () => void) => React.ReactNode
}

function csvCell(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replace(/"/g, '""')}"`
  }
  return value
}

function downloadCsv(filename: string, headers: string[], rows: string[][]) {
  const lines = [headers, ...rows].map((row) => row.map(csvCell).join(','))
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

/**
 * Generic list table used for every plain-CRUD entity in the app (campuses,
 * courses, PEOs, sections, ...). Fetches happen in the caller via
 * useEntityList; this component owns only client-side search + pagination,
 * since none of the backend list endpoints support server-side paging yet.
 *
 * Sorting, column visibility, density, export, and row-selection/bulk-actions
 * are all opt-in via props — existing callers are unaffected until they ask
 * for one.
 */
export function DataTable<T>({
  data,
  columns,
  rowKey,
  isLoading,
  error,
  searchable,
  searchPlaceholder = 'Search…',
  emptyMessage = 'No records yet.',
  pageSize = 20,
  onRowClick,
  actions,
  toolbar,
  columnVisibility,
  density,
  exportable,
  exportFilename = 'export',
  selectable,
  bulkActions,
}: DataTableProps<T>) {
  const [search, setSearch] = React.useState('')
  const [page, setPage] = useResetOnChange(`${search}|${data?.length ?? 0}`, 0)
  const [sort, setSort] = React.useState<{ key: string; direction: 'asc' | 'desc' } | null>(null)
  const [hiddenColumns, setHiddenColumns] = React.useState<Set<string>>(() => new Set())
  const [rowDensity, setRowDensity] = React.useState<Density>('comfortable')
  const [selectedKeys, setSelectedKeys] = React.useState<Set<string>>(() => new Set())

  const filtered = React.useMemo(() => {
    if (!data) return []
    if (!search.trim()) return data
    const needle = search.trim().toLowerCase()
    return data.filter((row) => {
      const haystacks =
        columns
          .map((c) => c.searchValue?.(row))
          .filter((v): v is string => typeof v === 'string') ??
        []
      if (haystacks.length === 0) {
        // Fall back to rendered cell text.
        return columns.some((c) => {
          const rendered = c.render(row)
          return typeof rendered === 'string' && rendered.toLowerCase().includes(needle)
        })
      }
      return haystacks.some((h) => h.toLowerCase().includes(needle))
    })
  }, [data, search, columns])

  const sorted = React.useMemo(() => {
    if (!sort) return filtered
    const column = columns.find((c) => c.key === sort.key)
    if (!column?.sortValue) return filtered
    const withKeys = filtered.map((row) => ({ row, key: column.sortValue!(row) }))
    withKeys.sort((a, b) => {
      if (a.key == null && b.key == null) return 0
      if (a.key == null) return 1
      if (b.key == null) return -1
      if (a.key < b.key) return sort.direction === 'asc' ? -1 : 1
      if (a.key > b.key) return sort.direction === 'asc' ? 1 : -1
      return 0
    })
    return withKeys.map((w) => w.row)
  }, [filtered, sort, columns])

  const visibleColumns = React.useMemo(
    () => columns.filter((c) => !hiddenColumns.has(c.key)),
    [columns, hiddenColumns],
  )

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const currentPage = Math.min(page, totalPages - 1)
  const paged = sorted.slice(currentPage * pageSize, currentPage * pageSize + pageSize)

  const selectedRows = React.useMemo(
    () => (data ?? []).filter((row) => selectedKeys.has(rowKey(row))),
    [data, selectedKeys, rowKey],
  )
  const pagedKeys = paged.map(rowKey)
  const allPagedSelected = pagedKeys.length > 0 && pagedKeys.every((k) => selectedKeys.has(k))
  const somePagedSelected = pagedKeys.some((k) => selectedKeys.has(k))

  function clearSelection() {
    setSelectedKeys(new Set())
  }

  function toggleRow(key: string, checked: boolean) {
    setSelectedKeys((prev) => {
      const next = new Set(prev)
      if (checked) next.add(key)
      else next.delete(key)
      return next
    })
  }

  function togglePage(checked: boolean) {
    setSelectedKeys((prev) => {
      const next = new Set(prev)
      for (const key of pagedKeys) {
        if (checked) next.add(key)
        else next.delete(key)
      }
      return next
    })
  }

  function toggleSort(columnKey: string) {
    setSort((prev) => {
      if (prev?.key !== columnKey) return { key: columnKey, direction: 'asc' }
      if (prev.direction === 'asc') return { key: columnKey, direction: 'desc' }
      return null
    })
  }

  function handleExport() {
    const exportColumns = visibleColumns
    const headers = exportColumns.map((c) => c.header)
    const rows = sorted.map((row) =>
      exportColumns.map((c) => {
        if (c.exportValue) return c.exportValue(row)
        if (c.searchValue) return c.searchValue(row)
        const rendered = c.render(row)
        return typeof rendered === 'string' || typeof rendered === 'number'
          ? String(rendered)
          : ''
      }),
    )
    downloadCsv(exportFilename, headers, rows)
  }

  const showToolbarRow = searchable || toolbar || columnVisibility || density || exportable
  const showBulkBar = selectable && selectedRows.length > 0

  return (
    <div className="flex flex-col gap-3">
      {showBulkBar ? (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border bg-accent/50 px-3 py-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <span>
              {selectedRows.length} selected
            </span>
            <Button variant="ghost" size="sm" className="h-auto gap-1 px-2 py-1" onClick={clearSelection}>
              <X className="size-3.5" /> Clear
            </Button>
          </div>
          {bulkActions?.(selectedRows, clearSelection)}
        </div>
      ) : (
        showToolbarRow && (
          <div className="flex flex-wrap items-center justify-between gap-2">
            {searchable ? (
              <div className="relative w-full max-w-xs">
                <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
                <Input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder={searchPlaceholder}
                  className="pl-8"
                />
              </div>
            ) : (
              <div />
            )}
            <div className="flex flex-wrap items-center gap-1.5">
              {toolbar}
              {density && (
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-1.5"
                  onClick={() =>
                    setRowDensity((d) => (d === 'comfortable' ? 'compact' : 'comfortable'))
                  }
                >
                  <Rows3 className="size-3.5" />
                  {rowDensity === 'comfortable' ? 'Comfortable' : 'Compact'}
                </Button>
              )}
              {columnVisibility && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="gap-1.5">
                      <Columns3 className="size-3.5" />
                      Columns
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Toggle columns</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {columns
                      .filter((c) => c.hideable !== false)
                      .map((c) => (
                        <DropdownMenuCheckboxItem
                          key={c.key}
                          checked={!hiddenColumns.has(c.key)}
                          onCheckedChange={(checked) =>
                            setHiddenColumns((prev) => {
                              const next = new Set(prev)
                              if (checked) next.delete(c.key)
                              else next.add(c.key)
                              return next
                            })
                          }
                        >
                          {c.header}
                        </DropdownMenuCheckboxItem>
                      ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
              {exportable && (
                <Button variant="outline" size="sm" className="gap-1.5" onClick={handleExport}>
                  <Download className="size-3.5" />
                  Export CSV
                </Button>
              )}
            </div>
          </div>
        )
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {selectable && (
                <TableHead className="w-px">
                  <Checkbox
                    checked={allPagedSelected ? true : somePagedSelected ? 'indeterminate' : false}
                    onCheckedChange={(checked) => togglePage(checked === true)}
                    aria-label="Select all rows on this page"
                  />
                </TableHead>
              )}
              {visibleColumns.map((col) => (
                <TableHead key={col.key} className={col.className}>
                  {col.sortValue ? (
                    <button
                      type="button"
                      className="flex items-center gap-1 hover:text-foreground"
                      onClick={() => toggleSort(col.key)}
                    >
                      {col.header}
                      {sort?.key === col.key ? (
                        sort.direction === 'asc' ? (
                          <ArrowUp className="size-3.5" />
                        ) : (
                          <ArrowDown className="size-3.5" />
                        )
                      ) : (
                        <ArrowUpDown className="size-3.5 opacity-40" />
                      )}
                    </button>
                  ) : (
                    col.header
                  )}
                </TableHead>
              ))}
              {actions ? <TableHead className="w-px text-right">Actions</TableHead> : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {selectable && (
                    <TableCell>
                      <Skeleton className="size-4" />
                    </TableCell>
                  )}
                  {visibleColumns.map((col) => (
                    <TableCell key={col.key}>
                      <Skeleton className="h-4 w-full max-w-32" />
                    </TableCell>
                  ))}
                  {actions ? (
                    <TableCell>
                      <Skeleton className="h-4 w-16" />
                    </TableCell>
                  ) : null}
                </TableRow>
              ))
            ) : error ? (
              <TableRow>
                <TableCell
                  colSpan={visibleColumns.length + (actions ? 1 : 0) + (selectable ? 1 : 0)}
                  className="py-8 text-center text-sm text-destructive"
                >
                  {error instanceof Error ? error.message : 'Failed to load data.'}
                </TableCell>
              </TableRow>
            ) : paged.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={visibleColumns.length + (actions ? 1 : 0) + (selectable ? 1 : 0)}
                  className="py-12 text-center"
                >
                  <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Inbox className="size-6 opacity-50" />
                    <span className="text-sm">{emptyMessage}</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              paged.map((row) => {
                const key = rowKey(row)
                return (
                  <TableRow
                    key={key}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                    className={cn(onRowClick && 'cursor-pointer')}
                    data-state={selectedKeys.has(key) ? 'selected' : undefined}
                  >
                    {selectable && (
                      <TableCell
                        className={DENSITY_CELL_CLASS[rowDensity]}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Checkbox
                          checked={selectedKeys.has(key)}
                          onCheckedChange={(checked) => toggleRow(key, checked === true)}
                          aria-label="Select row"
                        />
                      </TableCell>
                    )}
                    {visibleColumns.map((col) => (
                      <TableCell
                        key={col.key}
                        className={cn(col.className, DENSITY_CELL_CLASS[rowDensity])}
                      >
                        {col.render(row)}
                      </TableCell>
                    ))}
                    {actions ? (
                      <TableCell
                        className={cn('text-right', DENSITY_CELL_CLASS[rowDensity])}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="flex justify-end gap-1">{actions(row)}</div>
                      </TableCell>
                    ) : null}
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>

      {!isLoading && sorted.length > pageSize && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {sorted.length} record{sorted.length === 1 ? '' : 's'} · page {currentPage + 1} of{' '}
            {totalPages}
          </span>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              <ChevronLeft className="size-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= totalPages - 1}
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

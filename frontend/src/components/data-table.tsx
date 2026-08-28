import * as React from 'react'
import { ChevronLeft, ChevronRight, Inbox, Search } from 'lucide-react'

import { cn } from '@/lib/utils'
import { useResetOnChange } from '@/lib/use-reset-on-change'
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
import { Skeleton } from '@/components/ui/skeleton'

export interface DataTableColumn<T> {
  key: string
  header: string
  render: (row: T) => React.ReactNode
  className?: string
  /** Only used when `searchKeys` is not supplied — falls back to stringifying this accessor. */
  searchValue?: (row: T) => string
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
}

/**
 * Generic list table used for every plain-CRUD entity in the app (campuses,
 * courses, PEOs, sections, ...). Fetches happen in the caller via
 * useEntityList; this component owns only client-side search + pagination,
 * since none of the backend list endpoints support server-side paging yet.
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
}: DataTableProps<T>) {
  const [search, setSearch] = React.useState('')
  const [page, setPage] = useResetOnChange(`${search}|${data?.length ?? 0}`, 0)

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

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const currentPage = Math.min(page, totalPages - 1)
  const paged = filtered.slice(currentPage * pageSize, currentPage * pageSize + pageSize)

  return (
    <div className="flex flex-col gap-3">
      {(searchable || toolbar) && (
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
          {toolbar}
        </div>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead key={col.key} className={col.className}>
                  {col.header}
                </TableHead>
              ))}
              {actions ? <TableHead className="w-px text-right">Actions</TableHead> : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {columns.map((col) => (
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
                  colSpan={columns.length + (actions ? 1 : 0)}
                  className="py-8 text-center text-sm text-destructive"
                >
                  {error instanceof Error ? error.message : 'Failed to load data.'}
                </TableCell>
              </TableRow>
            ) : paged.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length + (actions ? 1 : 0)}
                  className="py-12 text-center"
                >
                  <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Inbox className="size-6 opacity-50" />
                    <span className="text-sm">{emptyMessage}</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              paged.map((row) => (
                <TableRow
                  key={rowKey(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={cn(onRowClick && 'cursor-pointer')}
                >
                  {columns.map((col) => (
                    <TableCell key={col.key} className={col.className}>
                      {col.render(row)}
                    </TableCell>
                  ))}
                  {actions ? (
                    <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex justify-end gap-1">{actions(row)}</div>
                    </TableCell>
                  ) : null}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {!isLoading && filtered.length > pageSize && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {filtered.length} record{filtered.length === 1 ? '' : 's'} · page {currentPage + 1} of{' '}
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

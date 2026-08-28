import * as React from 'react'
import { Database, Pencil, Plus, Search, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { useAuth } from '@/features/auth/useAuth'
import { ApiError } from '@/lib/api-client'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ConfirmAction } from '@/components/confirm-action'
import { Input } from '@/components/ui/input'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  useDeleteRow,
  useInsertRow,
  useInstitutions,
  useRawDataTables,
  useTableRows,
  useTableSchema,
  useUpdateRow,
} from '@/features/raw-data/api'
import { RowFormDialog } from '@/features/raw-data/RowFormDialog'
import type { RawRow, RowMutationResult } from '@/features/raw-data/types'

const RAW_DATA_ANY_PERMISSIONS = [
  'raw_data.manage_all',
  'raw_data.manage_institution',
  'raw_data.manage_scoped',
  'raw_data.propose_scoped',
]

const PAGE_SIZE = 50

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

/** After a write: "propose" means it was NOT applied — surface that
 * distinctly from a normal success toast so a Program Coordinator doesn't
 * think their edit took effect immediately. */
const PAST_TENSE: Record<string, string> = { insert: 'inserted', update: 'updated', delete: 'deleted' }

function announceMutation(result: RowMutationResult, verb: 'insert' | 'update' | 'delete') {
  if (result.mode === 'propose') {
    toast.info('Submitted for approval', {
      description: `This ${verb} was not applied yet — it's pending Program Administrator review (request ${result.change_request_id}).`,
      duration: 8000,
    })
  } else {
    toast.success(`Row ${PAST_TENSE[verb]}`)
  }
}

export function RawDataConsolePage() {
  const { hasPermission } = useAuth()
  const canSwitchInstitution = hasPermission('raw_data.manage_all')
  const canApprove = hasPermission('raw_data.approve')

  const [institutionSlug, setInstitutionSlug] = React.useState<string | null>(null)
  const [selectedTable, setSelectedTable] = React.useState<string | null>(null)
  const [tableSearch, setTableSearch] = React.useState('')
  const [page, setPage] = React.useState(1)
  const [createOpen, setCreateOpen] = React.useState(false)
  const [editRow, setEditRow] = React.useState<RawRow | null>(null)

  const institutions = useInstitutions(canSwitchInstitution)
  const tables = useRawDataTables(institutionSlug)
  const schema = useTableSchema(selectedTable, institutionSlug)
  const rows = useTableRows(selectedTable, institutionSlug, page, PAGE_SIZE)

  const insertRow = useInsertRow(selectedTable ?? '', institutionSlug)
  const updateRow = useUpdateRow(selectedTable ?? '', institutionSlug)
  const deleteRow = useDeleteRow(selectedTable ?? '', institutionSlug)

  const filteredTables = React.useMemo(() => {
    const list = tables.data ?? []
    if (!tableSearch.trim()) return list
    const needle = tableSearch.trim().toLowerCase()
    return list.filter((t) => t.toLowerCase().includes(needle))
  }, [tables.data, tableSearch])

  function selectTable(name: string) {
    setSelectedTable(name)
    setPage(1)
  }

  const pkColumn = schema.data?.columns.find((c) => c.is_primary_key)

  async function handleCreate(payload: RawRow) {
    try {
      const result = await insertRow.mutateAsync(payload)
      announceMutation(result, 'insert')
    } catch (err) {
      throw err instanceof ApiError ? err : new ApiError('Unable to add row.')
    }
  }

  async function handleUpdate(pk: string, payload: RawRow) {
    try {
      const result = await updateRow.mutateAsync({ pk, payload })
      announceMutation(result, 'update')
    } catch (err) {
      throw err instanceof ApiError ? err : new ApiError('Unable to save row.')
    }
  }

  async function handleDelete(pk: string) {
    try {
      const result = await deleteRow.mutateAsync(pk)
      announceMutation(result, 'delete')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to delete row.')
    }
  }

  return (
    <RequirePermission anyOf={RAW_DATA_ANY_PERMISSIONS}>
      <PageHeader
        title="Raw Data Console"
        description="Direct table browser/editor — every write is audit-logged; course-level writes by a Program Coordinator go through approval instead of applying immediately."
        actions={
          canApprove ? (
            <Button variant="outline" asChild>
              <Link to="/raw-data/pending-changes">Pending changes</Link>
            </Button>
          ) : undefined
        }
      />

      {canSwitchInstitution && (
        <div className="mb-4 flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Institution:</span>
          <Select
            value={institutionSlug ?? '__home__'}
            onValueChange={(v) => {
              setInstitutionSlug(v === '__home__' ? null : v)
              setSelectedTable(null)
              setPage(1)
            }}
          >
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Your institution" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__home__">Your institution</SelectItem>
              {(institutions.data ?? []).map((inst) => (
                <SelectItem key={inst.slug} value={inst.slug}>
                  {inst.name} ({inst.slug})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-[260px_1fr]">
        <Card className="h-fit">
          <CardContent className="flex flex-col gap-2 p-3">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
              <Input
                value={tableSearch}
                onChange={(e) => setTableSearch(e.target.value)}
                placeholder="Filter tables…"
                className="pl-8"
              />
            </div>
            <div className="flex max-h-[65vh] flex-col gap-0.5 overflow-y-auto">
              {tables.isLoading ? (
                Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-7 w-full" />)
              ) : tables.error ? (
                <p className="p-2 text-sm text-destructive">Failed to load tables.</p>
              ) : filteredTables.length === 0 ? (
                <p className="p-2 text-sm text-muted-foreground">No tables match.</p>
              ) : (
                filteredTables.map((name) => (
                  <button
                    key={name}
                    type="button"
                    onClick={() => selectTable(name)}
                    className={cn(
                      'cursor-pointer rounded-md px-2 py-1.5 text-left text-sm font-mono transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring',
                      selectedTable === name
                        ? 'bg-primary/10 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                    )}
                  >
                    {name}
                  </button>
                ))
              )}
            </div>
            <p className="border-t px-2 pt-2 text-xs text-muted-foreground">
              {tables.data?.length ?? 0} table{tables.data?.length === 1 ? '' : 's'} accessible
            </p>
          </CardContent>
        </Card>

        <div className="min-w-0">
          {!selectedTable ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
                <Database className="size-8 text-muted-foreground" />
                <p className="font-medium">Select a table to browse its rows</p>
                <p className="max-w-sm text-sm text-muted-foreground">
                  {tables.data?.length ?? 0} tables are available to you based on your current
                  role grants.
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="font-mono text-lg font-semibold">{selectedTable}</h2>
                  {rows.data ? (
                    <p className="text-sm text-muted-foreground">{rows.data.total} row(s)</p>
                  ) : null}
                </div>
                <Button
                  size="sm"
                  onClick={() => setCreateOpen(true)}
                  disabled={!schema.data}
                >
                  <Plus className="size-4" /> Add row
                </Button>
              </div>

              {schema.error ? (
                <p
                  role="alert"
                  className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive"
                >
                  Failed to load schema:{' '}
                  {schema.error instanceof ApiError ? schema.error.detail : 'Unknown error.'}
                </p>
              ) : null}

              <div className="overflow-x-auto rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {(schema.data?.columns ?? []).map((col) => (
                        <TableHead key={col.name} className="whitespace-nowrap font-mono text-xs">
                          {col.name}
                          {col.is_primary_key ? (
                            <Badge variant="outline" className="ml-1.5 px-1 py-0 text-[10px]">
                              PK
                            </Badge>
                          ) : null}
                        </TableHead>
                      ))}
                      <TableHead className="w-px text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {schema.isLoading || rows.isLoading ? (
                      Array.from({ length: 5 }).map((_, i) => (
                        <TableRow key={i}>
                          {(schema.data?.columns ?? Array.from({ length: 4 })).map((_c, j) => (
                            <TableCell key={j}>
                              <Skeleton className="h-4 w-full max-w-32" />
                            </TableCell>
                          ))}
                          <TableCell>
                            <Skeleton className="h-4 w-16" />
                          </TableCell>
                        </TableRow>
                      ))
                    ) : rows.error ? (
                      <TableRow>
                        <TableCell
                          colSpan={(schema.data?.columns.length ?? 0) + 1}
                          className="py-8 text-center text-sm text-destructive"
                        >
                          {rows.error instanceof ApiError ? rows.error.detail : 'Failed to load rows.'}
                        </TableCell>
                      </TableRow>
                    ) : (rows.data?.rows.length ?? 0) === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={(schema.data?.columns.length ?? 0) + 1}
                          className="py-8 text-center text-sm text-muted-foreground"
                        >
                          No rows yet.
                        </TableCell>
                      </TableRow>
                    ) : (
                      rows.data?.rows.map((row) => {
                        const pk = pkColumn ? String(row[pkColumn.name]) : undefined
                        return (
                          <TableRow key={pk ?? JSON.stringify(row)}>
                            {(schema.data?.columns ?? []).map((col) => (
                              <TableCell key={col.name} className="max-w-64 truncate font-mono text-xs">
                                {formatCell(row[col.name])}
                              </TableCell>
                            ))}
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-0.5">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="size-8"
                                  aria-label={`Edit row${pk ? ` ${pk}` : ''}`}
                                  onClick={() => setEditRow(row)}
                                >
                                  <Pencil className="size-4" />
                                </Button>
                                <ConfirmAction
                                  trigger={
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="size-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                                      aria-label={`Delete row${pk ? ` ${pk}` : ''}`}
                                    >
                                      <Trash2 className="size-4" />
                                    </Button>
                                  }
                                  title="Delete this row?"
                                  description={`This permanently removes row ${pk} from ${selectedTable}. This cannot be undone (unless it goes through the approval queue).`}
                                  confirmLabel="Delete"
                                  onConfirm={() => {
                                    if (pk) return handleDelete(pk)
                                  }}
                                />
                              </div>
                            </TableCell>
                          </TableRow>
                        )
                      })
                    )}
                  </TableBody>
                </Table>
              </div>

              {rows.data && rows.data.total > PAGE_SIZE ? (
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>
                    Page {rows.data.page} of {Math.max(1, Math.ceil(rows.data.total / PAGE_SIZE))}
                  </span>
                  <div className="flex gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page * PAGE_SIZE >= rows.data.total}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {schema.data && (
        <RowFormDialog
          open={createOpen}
          onOpenChange={setCreateOpen}
          mode="create"
          schema={schema.data}
          onSubmit={handleCreate}
        />
      )}

      {schema.data && editRow && pkColumn && (
        <RowFormDialog
          open={Boolean(editRow)}
          onOpenChange={(open) => !open && setEditRow(null)}
          mode="edit"
          schema={schema.data}
          initialRow={editRow}
          onSubmit={(payload) => handleUpdate(String(editRow[pkColumn.name]), payload)}
        />
      )}
    </RequirePermission>
  )
}

import * as React from 'react'
import { Database, LayoutDashboard, LogOut, Pencil, Plus, Search, Trash2 } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { ApiError } from '@/lib/api-client'
import { usePlatformAuth } from '@/lib/platform-auth-context'
import { useInstitutions } from '@/features/platform/api'
import {
  usePlatformDeleteRow,
  usePlatformInsertRow,
  usePlatformRawDataTables,
  usePlatformTableRows,
  usePlatformTableSchema,
  usePlatformUpdateRow,
} from '@/features/platform/raw-data-api'
import { RowFormDialog } from '@/features/raw-data/RowFormDialog'
import type { RawRow } from '@/features/raw-data/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ConfirmAction } from '@/components/confirm-action'
import { Footer } from '@/components/footer'
import { Input } from '@/components/ui/input'
import { Logo } from '@/components/logo'
import { PageHeader } from '@/components/page-header'
import { ThemeToggleButton } from '@/components/theme-toggle'
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
import { cn } from '@/lib/utils'

const PAGE_SIZE = 50

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function announceMutation(verb: 'insert' | 'update' | 'delete') {
  const past = { insert: 'inserted', update: 'updated', delete: 'deleted' }[verb]
  toast.success(`Row ${past}`)
}

/** Platform-admin raw-data console — full, unscoped CRUD across every
 * institution's data (see app/api/v1/endpoints/platform_raw_data.py).
 * Unlike the tenant console (features/raw-data/RawDataConsolePage.tsx),
 * institution selection is mandatory (a platform admin has no "home"
 * institution) and there's no propose/approval mode — every write is
 * immediate, since a platform admin's write is already the highest
 * authority in the system.
 */
export function PlatformRawDataPage() {
  const { admin, logout } = usePlatformAuth()
  const navigate = useNavigate()

  const [institutionSlug, setInstitutionSlug] = React.useState<string | null>(null)
  const [programCode, setProgramCode] = React.useState<string | null>(null)
  const [selectedTable, setSelectedTable] = React.useState<string | null>(null)
  const [tableSearch, setTableSearch] = React.useState('')
  const [page, setPage] = React.useState(1)
  const [createOpen, setCreateOpen] = React.useState(false)
  const [editRow, setEditRow] = React.useState<RawRow | null>(null)

  const institutions = useInstitutions()
  const tables = usePlatformRawDataTables(institutionSlug)
  const programsTable = usePlatformTableRows('programs', institutionSlug, null, 1, 200)
  const schema = usePlatformTableSchema(selectedTable)
  const rows = usePlatformTableRows(selectedTable, institutionSlug, programCode, page, PAGE_SIZE)

  const insertRow = usePlatformInsertRow(selectedTable ?? '', institutionSlug, programCode)
  const updateRow = usePlatformUpdateRow(selectedTable ?? '', institutionSlug, programCode)
  const deleteRow = usePlatformDeleteRow(selectedTable ?? '', institutionSlug, programCode)

  const programs = React.useMemo(
    () =>
      (programsTable.data?.rows ?? []).map((r) => ({
        code: String(r.code),
        name: String(r.name),
      })),
    [programsTable.data],
  )

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

  function handleLogout() {
    logout()
    navigate('/platform-login', { replace: true })
  }

  const pkColumn = schema.data?.columns.find((c) => c.is_primary_key)

  async function handleCreate(payload: RawRow) {
    try {
      await insertRow.mutateAsync(payload)
      announceMutation('insert')
    } catch (err) {
      throw err instanceof ApiError ? err : new ApiError('Unable to add row.')
    }
  }

  async function handleUpdate(pk: string, payload: RawRow) {
    try {
      await updateRow.mutateAsync({ pk, payload })
      announceMutation('update')
    } catch (err) {
      throw err instanceof ApiError ? err : new ApiError('Unable to save row.')
    }
  }

  async function handleDelete(pk: string) {
    try {
      await deleteRow.mutateAsync(pk)
      announceMutation('delete')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to delete row.')
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-muted/40">
      <header className="flex h-16 shrink-0 items-center justify-between border-b bg-card px-4 md:px-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Logo className="text-lg" />
            <Badge variant="outline" className="font-normal text-muted-foreground">
              Platform Admin
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-2 sm:gap-4">
          <Button variant="outline" size="sm" asChild>
            <Link to="/platform">
              <LayoutDashboard className="size-4" />
              Dashboard
            </Link>
          </Button>
          <span className="hidden text-sm text-muted-foreground sm:inline">{admin?.email}</span>
          <ThemeToggleButton />
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="size-4" />
            Log out
          </Button>
        </div>
      </header>

      <main className="flex-1 p-4 md:p-8">
        <div className="mx-auto w-full max-w-7xl">
          <PageHeader
            title="Raw Data Console"
            description="Direct, unscoped table browser/editor across every institution — every write is audit-logged and applies immediately."
          />

          <div className="mb-4 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Institution:</span>
              <Select
                value={institutionSlug ?? ''}
                onValueChange={(v) => {
                  setInstitutionSlug(v)
                  setProgramCode(null)
                  setSelectedTable(null)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-64">
                  <SelectValue placeholder="Select an institution…" />
                </SelectTrigger>
                <SelectContent>
                  {(institutions.data ?? []).map((inst) => (
                    <SelectItem key={inst.slug} value={inst.slug}>
                      {inst.name} ({inst.slug})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {institutionSlug && programs.length > 0 ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Program:</span>
                <Select
                  value={programCode ?? '__none__'}
                  onValueChange={(v) => {
                    setProgramCode(v === '__none__' ? null : v)
                    setPage(1)
                  }}
                >
                  <SelectTrigger className="w-56">
                    <SelectValue placeholder="None selected" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">None selected</SelectItem>
                    {programs.map((p) => (
                      <SelectItem key={p.code} value={p.code}>
                        {p.name} ({p.code})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ) : null}
          </div>

          {!institutionSlug ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
                <Database className="size-8 text-muted-foreground" />
                <p className="font-medium">Select an institution to browse its data</p>
                <p className="max-w-sm text-sm text-muted-foreground">
                  Every table across every institution is accessible here — pick one to start.
                </p>
              </CardContent>
            </Card>
          ) : (
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
                      Array.from({ length: 8 }).map((_, i) => (
                        <Skeleton key={i} className="h-7 w-full" />
                      ))
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
                    {tables.data?.length ?? 0} tables total
                  </p>
                </CardContent>
              </Card>

              <div className="min-w-0">
                {!selectedTable ? (
                  <Card className="border-dashed">
                    <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
                      <Database className="size-8 text-muted-foreground" />
                      <p className="font-medium">Select a table to browse its rows</p>
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
                      <Button size="sm" onClick={() => setCreateOpen(true)} disabled={!schema.data}>
                        <Plus className="size-4" /> Add row
                      </Button>
                    </div>

                    {schema.error || rows.error ? (
                      <p
                        role="alert"
                        className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive"
                      >
                        {(schema.error instanceof ApiError && schema.error.detail) ||
                          (rows.error instanceof ApiError && rows.error.detail) ||
                          'Failed to load table.'}
                      </p>
                    ) : null}

                    <div className="rounded-md border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            {(schema.data?.columns ?? []).map((col) => (
                              <TableHead
                                key={col.name}
                                className="whitespace-nowrap font-mono text-xs"
                              >
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
                                {(schema.data?.columns ?? Array.from({ length: 4 })).map(
                                  (_c, j) => (
                                    <TableCell key={j}>
                                      <Skeleton className="h-4 w-full max-w-32" />
                                    </TableCell>
                                  ),
                                )}
                                <TableCell>
                                  <Skeleton className="h-4 w-16" />
                                </TableCell>
                              </TableRow>
                            ))
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
                                    <TableCell
                                      key={col.name}
                                      className="max-w-64 truncate font-mono text-xs"
                                    >
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
                                        description={`This permanently removes row ${pk} from ${selectedTable}. This cannot be undone.`}
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
                          Page {rows.data.page} of{' '}
                          {Math.max(1, Math.ceil(rows.data.total / PAGE_SIZE))}
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
          )}
        </div>
      </main>

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

      <Footer />
    </div>
  )
}

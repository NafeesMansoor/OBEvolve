import * as React from 'react'

import { ApiError } from '@/lib/api-client'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import type { ColumnSchema, RawRow, TableSchema } from '@/features/raw-data/types'

type FormValue = string | boolean

/**
 * Generic row create/edit form, fields generated straight from the table's
 * column metadata (no per-table hand-authored schema — that's the whole
 * point of a raw-data console). Deliberately simpler than
 * components/entity-form-dialog.tsx: field shape here is only known at
 * runtime, so per-row zod schemas would need to be synthesized dynamically
 * for little benefit — HTML5 `required` on non-nullable columns plus
 * surfacing the backend's own validation error covers this pass.
 */

function editableColumns(schema: TableSchema): ColumnSchema[] {
  // PK is never submitted: on edit it's immutable (server rule), on insert
  // every PK in this schema is a server-generated UUID default, so asking
  // for it would just add friction for the common case. A table that truly
  // needs a hand-entered PK on insert will surface that as a clear backend
  // validation error instead — an accepted simplification for this pass.
  return schema.columns.filter((c) => !c.is_primary_key)
}

function toFormValue(col: ColumnSchema, raw: unknown): FormValue {
  if (col.type === 'boolean') return Boolean(raw)
  if (raw === null || raw === undefined) return ''
  if (col.type === 'json' && typeof raw === 'object') return JSON.stringify(raw)
  if (col.type === 'datetime' && typeof raw === 'string') return raw.slice(0, 16)
  return String(raw)
}

function buildInitialValues(schema: TableSchema, initialRow: RawRow | undefined): Record<string, FormValue> {
  const values: Record<string, FormValue> = {}
  for (const col of editableColumns(schema)) {
    values[col.name] = toFormValue(col, initialRow?.[col.name])
  }
  return values
}

function buildPayload(schema: TableSchema, values: Record<string, FormValue>): RawRow {
  const payload: RawRow = {}
  for (const col of editableColumns(schema)) {
    const v = values[col.name]
    if (col.type === 'boolean') {
      payload[col.name] = Boolean(v)
      continue
    }
    if (v === '' || v === undefined) {
      if (col.nullable) payload[col.name] = null
      continue
    }
    if (col.type === 'integer') {
      const n = Number(v)
      payload[col.name] = Number.isFinite(n) ? n : v
    } else if (col.type === 'numeric') {
      payload[col.name] = String(v)
    } else if (col.type === 'json') {
      try {
        payload[col.name] = JSON.parse(String(v))
      } catch {
        payload[col.name] = v
      }
    } else if (col.type === 'datetime') {
      const s = String(v)
      payload[col.name] = s.length === 16 ? `${s}:00` : s
    } else {
      payload[col.name] = v
    }
  }
  return payload
}

interface RowFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  mode: 'create' | 'edit'
  schema: TableSchema
  initialRow?: RawRow
  onSubmit: (payload: RawRow) => Promise<void>
}

export function RowFormDialog({
  open,
  onOpenChange,
  mode,
  schema,
  initialRow,
  onSubmit,
}: RowFormDialogProps) {
  const pkColumn = schema.columns.find((c) => c.is_primary_key)
  // Resets whenever the dialog (re)opens for a possibly-different row —
  // render-time adjustment (see lib/use-reset-on-change.ts) rather than an
  // effect that calls setState, which the repo's lint config flags.
  const resetKey = `${open}|${schema.table_name}|${
    initialRow && pkColumn ? String(initialRow[pkColumn.name]) : ''
  }`
  const [values, setValues] = useResetOnChange<Record<string, FormValue>>(
    resetKey,
    buildInitialValues(schema, initialRow),
  )
  const [serverError, setServerError] = useResetOnChange<string | null>(open, null)
  const [isSubmitting, setIsSubmitting] = React.useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setServerError(null)
    setIsSubmitting(true)
    try {
      await onSubmit(buildPayload(schema, values))
      onOpenChange(false)
    } catch (err) {
      setServerError(err instanceof ApiError ? err.detail : 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? `Add row · ${schema.table_name}` : `Edit row · ${schema.table_name}`}
          </DialogTitle>
          <DialogDescription>
            Fields are generated from this table&apos;s own column metadata.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          {mode === 'edit' && pkColumn ? (
            <div className="space-y-1.5">
              <Label className="font-mono text-xs">
                {pkColumn.name}{' '}
                <span className="font-sans text-xs font-normal text-muted-foreground">
                  (primary key, read-only)
                </span>
              </Label>
              <Input value={String(initialRow?.[pkColumn.name] ?? '')} disabled className="font-mono text-sm" />
            </div>
          ) : null}

          {editableColumns(schema).map((col) => (
            <div key={col.name} className="space-y-1.5">
              <Label htmlFor={`rd-field-${col.name}`} className="font-mono text-xs">
                {col.name}
                {!col.nullable ? <span className="text-destructive"> *</span> : null}
                {col.foreign_key ? (
                  <span className="ml-1.5 font-sans text-xs font-normal text-muted-foreground">
                    → {col.foreign_key}
                  </span>
                ) : null}
              </Label>

              {col.type === 'boolean' ? (
                <div className="flex h-9 items-center">
                  <Checkbox
                    id={`rd-field-${col.name}`}
                    checked={Boolean(values[col.name])}
                    onCheckedChange={(checked) =>
                      setValues((prev) => ({ ...prev, [col.name]: Boolean(checked) }))
                    }
                  />
                </div>
              ) : col.type === 'text' || col.type === 'json' ? (
                <Textarea
                  id={`rd-field-${col.name}`}
                  required={!col.nullable}
                  value={(values[col.name] as string) ?? ''}
                  onChange={(e) => setValues((prev) => ({ ...prev, [col.name]: e.target.value }))}
                  placeholder={col.type === 'json' ? '{"key": "value"}' : undefined}
                  className="font-mono text-sm"
                />
              ) : (
                <Input
                  id={`rd-field-${col.name}`}
                  required={!col.nullable}
                  type={
                    col.type === 'integer' || col.type === 'numeric'
                      ? 'number'
                      : col.type === 'date'
                        ? 'date'
                        : col.type === 'datetime'
                          ? 'datetime-local'
                          : 'text'
                  }
                  step={col.type === 'numeric' ? 'any' : undefined}
                  value={(values[col.name] as string) ?? ''}
                  onChange={(e) => setValues((prev) => ({ ...prev, [col.name]: e.target.value }))}
                />
              )}
            </div>
          ))}

          {serverError ? (
            <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {serverError}
            </p>
          ) : null}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving…' : mode === 'create' ? 'Add row' : 'Save changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

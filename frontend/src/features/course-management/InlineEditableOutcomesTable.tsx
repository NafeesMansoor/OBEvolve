import * as React from 'react'
import { Check, X } from 'lucide-react'

import type { CourseOutcome } from '@/features/curriculum/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'

interface OutcomeDraftRow {
  code: string
  statement: string
  sequence: number
  delivery_methods: string | null
  assessment_tools: string | null
}

type CellField = 'code' | 'statement' | 'delivery_methods' | 'assessment_tools'

function toDraft(outcomes: CourseOutcome[]): OutcomeDraftRow[] {
  return outcomes.map((co) => ({
    code: co.code,
    statement: co.statement,
    sequence: co.sequence,
    delivery_methods: co.delivery_methods ?? null,
    assessment_tools: co.assessment_tools ?? null,
  }))
}

/** Wix-editor-style inline editing for the Course Outcomes table:
 * double-click a cell to edit it in place; a Save/Discard bar appears once
 * anything differs from the original. Save submits the *whole* outcomes
 * array as structured `{"outcomes": [...]}` JSON — matching
 * `app.services.course_type_config._apply_outcomes`'s real auto-apply
 * shape, unlike a free-text proposal (which that applier deliberately
 * refuses to guess at — see its docstring). */
export function InlineEditableOutcomesTable({
  outcomes,
  editable,
  onSave,
}: {
  outcomes: CourseOutcome[] | undefined
  editable: boolean
  onSave: (newOutcomes: OutcomeDraftRow[], message: string) => Promise<void>
}) {
  const [draft, setDraft] = React.useState<OutcomeDraftRow[] | null>(null)
  const [editingCell, setEditingCell] = React.useState<{ row: number; field: CellField } | null>(
    null,
  )
  const [message, setMessage] = React.useState('')
  const [messageError, setMessageError] = React.useState(false)
  const [saving, setSaving] = React.useState(false)

  if (!outcomes) return <Skeleton className="h-24 w-full" />
  if (outcomes.length === 0 && !editable) {
    return <p className="text-sm text-muted-foreground">No course outcomes defined yet.</p>
  }

  const rows = draft ?? toDraft(outcomes)
  const isDirty = draft !== null && JSON.stringify(draft) !== JSON.stringify(toDraft(outcomes))

  function beginEdit(row: number, field: CellField) {
    if (!editable) return
    if (draft === null) setDraft(toDraft(outcomes ?? []))
    setEditingCell({ row, field })
  }

  function updateCell(row: number, field: CellField, value: string) {
    setDraft((prev) => {
      const base = prev ?? toDraft(outcomes ?? [])
      const next = base.map((r, i) => (i === row ? { ...r, [field]: value } : r))
      return next
    })
  }

  function discard() {
    setDraft(null)
    setEditingCell(null)
    setMessage('')
    setMessageError(false)
  }

  async function save() {
    if (!message.trim()) {
      setMessageError(true)
      return
    }
    setSaving(true)
    try {
      await onSave(draft ?? toDraft(outcomes ?? []), message.trim())
      discard()
    } finally {
      setSaving(false)
    }
  }

  function cell(row: number, field: CellField, value: string, width?: string) {
    const isEditingThis = editingCell?.row === row && editingCell.field === field
    if (isEditingThis) {
      return (
        <Input
          autoFocus
          value={value}
          onChange={(e) => updateCell(row, field, e.target.value)}
          onBlur={() => setEditingCell(null)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') setEditingCell(null)
          }}
          className="h-8"
        />
      )
    }
    return (
      <div
        onDoubleClick={() => beginEdit(row, field)}
        className={cn(
          'min-h-[1.5rem] rounded px-1 py-0.5',
          editable && 'cursor-pointer hover:outline hover:outline-dashed hover:outline-1 hover:outline-emerald-500',
          width,
        )}
        title={editable ? 'Double-click to edit' : undefined}
      >
        {value || (editable ? <span className="text-muted-foreground">—</span> : '—')}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">Code</TableHead>
            <TableHead>Statement</TableHead>
            <TableHead>Delivery methods</TableHead>
            <TableHead>Assessment tools</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground">
                No course outcomes defined yet.
              </TableCell>
            </TableRow>
          ) : (
            rows.map((co, i) => (
              <TableRow key={co.code || i}>
                <TableCell className="font-medium">{cell(i, 'code', co.code, 'w-14')}</TableCell>
                <TableCell>{cell(i, 'statement', co.statement)}</TableCell>
                <TableCell className="text-muted-foreground">
                  {cell(i, 'delivery_methods', co.delivery_methods ?? '')}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {cell(i, 'assessment_tools', co.assessment_tools ?? '')}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {isDirty && (
        <div className="flex flex-col gap-1.5 rounded-md border border-primary/40 bg-muted/30 p-2">
          <Input
            placeholder="Message to your reviewer — why this change? (required)"
            value={message}
            onChange={(e) => {
              setMessage(e.target.value)
              if (e.target.value.trim()) setMessageError(false)
            }}
            disabled={saving}
            className={cn(messageError && 'border-destructive')}
          />
          {messageError && <p className="text-xs text-destructive">A message is required.</p>}
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="outline" onClick={discard} disabled={saving}>
              <X className="size-4" /> Discard
            </Button>
            <Button size="sm" onClick={() => void save()} disabled={saving}>
              <Check className="size-4" /> {saving ? 'Sending…' : 'Save'}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

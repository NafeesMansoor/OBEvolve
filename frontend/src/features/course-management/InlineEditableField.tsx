import * as React from 'react'
import { Check, Pencil, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

/** Wix-editor-style inline editing for a single course-content field:
 * double-click to turn the displayed text into an editable box, then a
 * Save/Discard bar (with a short message to the reviewer) appears instead
 * of a separate button + modal dialog. Save calls `onSave` with the new
 * value and message — the caller still submits it as a normal change
 * request (section_key/target_field/proposed_value_json/reason), this
 * component only changes how the teacher provides the input. */
export function InlineEditableField({
  value,
  editable,
  onSave,
  emptyPlaceholder = 'No content yet — double-click to propose one.',
  multiline = true,
  renderDisplay,
  className,
}: {
  value: string | null | undefined
  editable: boolean
  onSave: (newValue: string, message: string) => Promise<void>
  emptyPlaceholder?: string
  multiline?: boolean
  renderDisplay?: (value: string) => React.ReactNode
  className?: string
}) {
  const [isEditing, setIsEditing] = React.useState(false)
  const [draft, setDraft] = React.useState('')
  const [message, setMessage] = React.useState('')
  const [messageError, setMessageError] = React.useState(false)
  const [saving, setSaving] = React.useState(false)

  function startEditing() {
    if (!editable || isEditing) return
    setDraft(value ?? '')
    setMessage('')
    setMessageError(false)
    setIsEditing(true)
  }

  function discard() {
    setIsEditing(false)
    setDraft('')
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
      await onSave(draft, message.trim())
      setIsEditing(false)
    } finally {
      setSaving(false)
    }
  }

  if (isEditing) {
    const Field = multiline ? Textarea : Input
    return (
      <div className={cn('flex flex-col gap-2 rounded-md border border-primary/40 bg-muted/30 p-2', className)}>
        <Field
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          autoFocus
          rows={multiline ? 5 : undefined}
          disabled={saving}
        />
        <div className="flex flex-col gap-1.5 border-t pt-2">
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
      </div>
    )
  }

  return (
    <div
      onDoubleClick={startEditing}
      className={cn(
        'group relative rounded-md p-1.5 -m-1.5',
        editable && 'cursor-pointer hover:outline hover:outline-dashed hover:outline-1 hover:outline-emerald-500',
        className,
      )}
      title={editable ? 'Double-click to propose a change' : undefined}
    >
      {value ? (
        (renderDisplay ?? ((v: string) => <p className="whitespace-pre-line text-sm">{v}</p>))(value)
      ) : (
        <p className="text-sm text-muted-foreground">
          {editable ? emptyPlaceholder : 'No content on file.'}
        </p>
      )}
      {editable && (
        <Pencil className="absolute right-1 top-1 size-3.5 text-emerald-600 opacity-0 transition-opacity group-hover:opacity-100" />
      )}
    </div>
  )
}

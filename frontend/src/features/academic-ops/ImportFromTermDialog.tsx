import * as React from 'react'

import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface TermOption {
  label: string
  value: string
}

/**
 * "Carry forward" a previous term's rows into the currently-worked-on term
 * — the general shape of the "import" request across Academic Operations
 * tabs (course offerings today; the same pattern applies to sections,
 * faculty assignments, and enrollments, whose "previous term" is usually
 * the same source data). Deliberately dumb about *what* gets imported —
 * `onImport(sourceTermId, targetTermId)` does the actual copying, since
 * that logic is entity-specific (which fields carry over, how duplicates
 * are detected) while the "pick two terms and go" interaction is not.
 */
export function ImportFromTermDialog({
  open,
  onOpenChange,
  termOptions,
  onImport,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  termOptions: TermOption[]
  onImport: (sourceTermId: string, targetTermId: string) => Promise<void>
}) {
  const [sourceTermId, setSourceTermId] = useResetOnChange(open, '')
  const [targetTermId, setTargetTermId] = useResetOnChange(open, '')
  const [isImporting, setIsImporting] = React.useState(false)

  const canImport = sourceTermId && targetTermId && sourceTermId !== targetTermId && !isImporting

  async function handleImport() {
    setIsImporting(true)
    try {
      await onImport(sourceTermId, targetTermId)
      onOpenChange(false)
    } finally {
      setIsImporting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Import from a previous term</DialogTitle>
          <DialogDescription>
            Copies every row from the source term into the target term, skipping any that already
            exist there.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label>From term</Label>
            <Select value={sourceTermId} onValueChange={setSourceTermId}>
              <SelectTrigger>
                <SelectValue placeholder="Source term" />
              </SelectTrigger>
              <SelectContent>
                {termOptions.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Into term</Label>
            <Select value={targetTermId} onValueChange={setTargetTermId}>
              <SelectTrigger>
                <SelectValue placeholder="Target term" />
              </SelectTrigger>
              <SelectContent>
                {termOptions.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {sourceTermId && sourceTermId === targetTermId ? (
          <p className="text-sm text-destructive">Source and target term must be different.</p>
        ) : null}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button disabled={!canImport} onClick={handleImport}>
            {isImporting ? 'Importing…' : 'Import'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

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

interface OfferingOption {
  label: string
  value: string
}

/**
 * Carries rows forward from the SAME course's offering in a different term
 * into the offering currently selected on screen — the shape Sections and
 * Faculty Assignments need (both are scoped to one offering at a time, not
 * a whole term like Course Offerings' own import — see
 * ImportFromTermDialog). `candidateOfferings` is pre-filtered by the caller
 * to "same course_version_id, different term" so this dialog only ever
 * offers choices that actually make sense to import from.
 */
export function ImportFromOfferingDialog({
  open,
  onOpenChange,
  entityLabel,
  candidateOfferings,
  onImport,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  entityLabel: string
  candidateOfferings: OfferingOption[]
  onImport: (sourceOfferingId: string) => Promise<void>
}) {
  const [sourceOfferingId, setSourceOfferingId] = useResetOnChange(open, '')
  const [isImporting, setIsImporting] = React.useState(false)

  async function handleImport() {
    setIsImporting(true)
    try {
      await onImport(sourceOfferingId)
      onOpenChange(false)
    } finally {
      setIsImporting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Import {entityLabel} from another term</DialogTitle>
          <DialogDescription>
            Copies {entityLabel.toLowerCase()} from the same course's offering in a previous term
            into this one, skipping any that already exist here.
          </DialogDescription>
        </DialogHeader>

        {candidateOfferings.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            This course has no other offerings to import from yet.
          </p>
        ) : (
          <div className="space-y-1.5">
            <Label>Import from</Label>
            <Select value={sourceOfferingId} onValueChange={setSourceOfferingId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a term" />
              </SelectTrigger>
              <SelectContent>
                {candidateOfferings.map((o) => (
                  <SelectItem key={o.value} value={o.value}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button disabled={!sourceOfferingId || isImporting} onClick={handleImport}>
            {isImporting ? 'Importing…' : 'Import'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

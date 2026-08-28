import * as React from 'react'
import { Pencil, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'

export interface DetailField {
  label: string
  value: React.ReactNode
  /** Span both grid columns — for long text (statements, descriptions). */
  full?: boolean
}

interface RecordDetailSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: React.ReactNode
  subtitle?: React.ReactNode
  badge?: React.ReactNode
  fields: DetailField[]
  /** Extra content rendered below the field grid — related records, etc. */
  children?: React.ReactNode
  onEdit?: () => void
  onDelete?: () => void
  editLabel?: string
}

/**
 * The one detail view every clickable table row in the app opens into
 * (spec: "all table items should be clickable and will take to detailed
 * info page" — a slide-over rather than a real route, so every entity gets
 * this for free without a bespoke page per table). Read-only by design:
 * `onEdit`/`onDelete` hand off to whatever edit dialog / delete flow the
 * calling tab already has, rather than duplicating that logic here.
 */
export function RecordDetailSheet({
  open,
  onOpenChange,
  title,
  subtitle,
  badge,
  fields,
  children,
  onEdit,
  onDelete,
  editLabel = 'Edit',
}: RecordDetailSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg">
        <SheetHeader>
          <div className="flex items-start justify-between gap-3 pr-6">
            <SheetTitle>{title}</SheetTitle>
            {badge}
          </div>
          {subtitle ? <SheetDescription>{subtitle}</SheetDescription> : null}
        </SheetHeader>

        <Separator />

        <div className="grid grid-cols-2 gap-x-4 gap-y-4 overflow-y-auto py-2">
          {fields.map((f, i) => (
            <div key={i} className={f.full ? 'col-span-2' : undefined}>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {f.label}
              </p>
              <div className="mt-1 text-sm">{f.value ?? <span className="text-muted-foreground">—</span>}</div>
            </div>
          ))}
        </div>

        {children ? (
          <>
            <Separator />
            <div className="flex flex-col gap-3">{children}</div>
          </>
        ) : null}

        {(onEdit || onDelete) && (
          <SheetFooter>
            {onDelete ? (
              <Button variant="outline" className="text-destructive hover:text-destructive" onClick={onDelete}>
                <Trash2 className="size-4" />
                Delete
              </Button>
            ) : null}
            {onEdit ? (
              <Button onClick={onEdit}>
                <Pencil className="size-4" />
                {editLabel}
              </Button>
            ) : null}
          </SheetFooter>
        )}
      </SheetContent>
    </Sheet>
  )
}

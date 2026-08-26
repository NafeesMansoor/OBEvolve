import * as React from 'react'

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button, type ButtonProps } from '@/components/ui/button'

interface ConfirmActionProps {
  trigger: React.ReactNode
  title: string
  description?: string
  confirmLabel?: string
  onConfirm: () => void | Promise<void>
  variant?: ButtonProps['variant']
}

/** Shared destructive-action confirmation (delete, revoke, ...). */
export function ConfirmAction({
  trigger,
  title,
  description,
  confirmLabel = 'Confirm',
  onConfirm,
  variant = 'destructive',
}: ConfirmActionProps) {
  const [isPending, setIsPending] = React.useState(false)

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>{trigger}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description ? <AlertDialogDescription>{description}</AlertDialogDescription> : null}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <Button
            variant={variant}
            disabled={isPending}
            onClick={async (e) => {
              e.preventDefault()
              setIsPending(true)
              try {
                await onConfirm()
              } finally {
                setIsPending(false)
              }
            }}
          >
            {isPending ? 'Working…' : confirmLabel}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

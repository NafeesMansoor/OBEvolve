import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import type { ZodType } from 'zod'

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
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

export type EntityFieldType = 'text' | 'textarea' | 'number' | 'select' | 'date' | 'checkbox'

export interface EntityFieldOption {
  label: string
  value: string
}

export interface EntityField {
  name: string
  label: string
  type: EntityFieldType
  options?: EntityFieldOption[]
  placeholder?: string
  description?: string
  step?: string
  disabled?: boolean
}

interface EntityFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  fields: EntityField[]
  /** Zod schema the raw form values (all strings/booleans) are parsed/coerced through. */
  schema: ZodType<Record<string, unknown>>
  defaultValues: Record<string, unknown>
  onSubmit: (values: Record<string, unknown>) => Promise<void>
  submitLabel?: string
}

/**
 * Generic create/edit dialog shared by every entity page. Field shape is
 * declarative (EntityField[]) so each entity only needs to describe its
 * fields + a zod schema, not re-implement the form.
 */
export function EntityFormDialog({
  open,
  onOpenChange,
  title,
  description,
  fields,
  schema,
  defaultValues,
  onSubmit,
  submitLabel = 'Save',
}: EntityFormDialogProps) {
  // Resets to null every time the dialog opens/closes — exactly the
  // behavior we want (stale errors from a previous attempt shouldn't
  // linger), implemented as a render-time adjustment rather than an effect.
  const [serverError, setServerError] = useResetOnChange<string | null>(open, null)
  const form = useForm<Record<string, unknown>>({
    // The declarative field system means the exact shape varies per entity,
    // so the schema is typed loosely (ZodType<Record<string, unknown>>) —
    // zodResolver's generic inference doesn't like that looseness, hence the cast.
    resolver: zodResolver(schema as ZodType<Record<string, unknown>, Record<string, unknown>>),
    defaultValues,
  })

  React.useEffect(() => {
    // Imperative call into react-hook-form (an external system), not a
    // setState — the lint rule only flags the latter.
    if (open) {
      form.reset(defaultValues)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  async function handleSubmit(values: Record<string, unknown>) {
    setServerError(null)
    try {
      await onSubmit(values)
      onOpenChange(false)
    } catch (err) {
      setServerError(err instanceof ApiError ? err.detail : 'Something went wrong. Please try again.')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description ? <DialogDescription>{description}</DialogDescription> : null}
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4" noValidate>
            {fields.map((field) => (
              <FormField
                key={field.name}
                control={form.control}
                name={field.name}
                render={({ field: rhfField }) => (
                  <FormItem>
                    <FormLabel>{field.label}</FormLabel>
                    <FormControl>
                      {field.type === 'textarea' ? (
                        <Textarea
                          placeholder={field.placeholder}
                          disabled={field.disabled}
                          value={(rhfField.value as string) ?? ''}
                          onChange={rhfField.onChange}
                          onBlur={rhfField.onBlur}
                          name={rhfField.name}
                        />
                      ) : field.type === 'select' ? (
                        <Select
                          value={(rhfField.value as string) ?? undefined}
                          onValueChange={rhfField.onChange}
                          disabled={field.disabled}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder={field.placeholder ?? 'Select…'} />
                          </SelectTrigger>
                          <SelectContent>
                            {(field.options ?? []).length === 0 ? (
                              <div className="px-2 py-1.5 text-sm text-muted-foreground">
                                None available yet
                              </div>
                            ) : (
                              field.options?.map((opt) => (
                                <SelectItem key={opt.value} value={opt.value}>
                                  {opt.label}
                                </SelectItem>
                              ))
                            )}
                          </SelectContent>
                        </Select>
                      ) : field.type === 'checkbox' ? (
                        <div className="flex h-9 items-center">
                          <Checkbox
                            checked={Boolean(rhfField.value)}
                            onCheckedChange={rhfField.onChange}
                            disabled={field.disabled}
                          />
                        </div>
                      ) : (
                        <Input
                          type={field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'}
                          step={field.step}
                          placeholder={field.placeholder}
                          disabled={field.disabled}
                          value={(rhfField.value as string | number) ?? ''}
                          onChange={rhfField.onChange}
                          onBlur={rhfField.onBlur}
                          name={rhfField.name}
                        />
                      )}
                    </FormControl>
                    {field.description ? (
                      <FormDescription>{field.description}</FormDescription>
                    ) : null}
                    <FormMessage />
                  </FormItem>
                )}
              />
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
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? 'Saving…' : submitLabel}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

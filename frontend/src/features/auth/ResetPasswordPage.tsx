import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import axios, { type AxiosError } from 'axios'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { z } from 'zod'

import { API_BASE_URL, type ApiErrorShape } from '@/lib/api-client'
import { Footer } from '@/components/footer'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'

const resetPasswordSchema = z
  .object({
    newPassword: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string().min(1, 'Please confirm your new password'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const institution = searchParams.get('institution') ?? ''
  const [serverError, setServerError] = React.useState<string | null>(null)

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { newPassword: '', confirmPassword: '' },
  })

  const linkIsIncomplete = !token || !institution

  async function onSubmit(values: ResetPasswordFormValues) {
    setServerError(null)
    try {
      // Login (and password reset) is tenant-scoped, and the institution
      // this link was issued for may not match VITE_INSTITUTION_SLUG for
      // this deployment (e.g. a Super Admin testing a link across
      // tenants). apiClient's request interceptor always stamps the
      // env-configured slug onto every request (see src/lib/api-client.ts)
      // and can't be overridden per-call, so this one request bypasses it
      // and hits the API directly with an explicit header — the same
      // pattern api-client.ts's own attemptRefresh() uses for the token
      // refresh call.
      await axios.post(
        `${API_BASE_URL}/auth/reset-password`,
        { token, new_password: values.newPassword },
        { headers: { 'X-Institution-Slug': institution } },
      )
      toast.success('Your password has been reset. Please sign in.')
      navigate('/login', { replace: true })
    } catch (err) {
      const axiosError = err as AxiosError<ApiErrorShape>
      setServerError(
        axiosError.response?.data?.detail ?? 'Unable to reset password. Please try again.',
      )
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-muted/40">
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex flex-col items-center gap-2 text-center">
            <div className="flex size-10 items-center justify-center rounded-lg bg-primary text-lg font-semibold text-primary-foreground">
              OB
            </div>
            <h1 className="text-xl font-semibold tracking-tight">OBEvolve</h1>
            <p className="text-sm text-muted-foreground">
              Outcome-Based Education &amp; accreditation platform
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Reset password</CardTitle>
              <CardDescription>Choose a new password for your account.</CardDescription>
            </CardHeader>
            <CardContent>
              {linkIsIncomplete ? (
                <p
                  role="alert"
                  className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive"
                >
                  This reset link is missing or malformed. Request a new one from the{' '}
                  <Link to="/forgot-password" className="underline underline-offset-4">
                    forgot password
                  </Link>{' '}
                  page.
                </p>
              ) : (
                <Form {...form}>
                  <form
                    onSubmit={form.handleSubmit(onSubmit)}
                    className="space-y-4"
                    noValidate
                  >
                    <FormField
                      control={form.control}
                      name="newPassword"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>New password</FormLabel>
                          <FormControl>
                            <Input
                              type="password"
                              autoComplete="new-password"
                              placeholder="••••••••"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="confirmPassword"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Confirm new password</FormLabel>
                          <FormControl>
                            <Input
                              type="password"
                              autoComplete="new-password"
                              placeholder="••••••••"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {serverError ? (
                      <p
                        role="alert"
                        className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive"
                      >
                        {serverError}
                      </p>
                    ) : null}

                    <Button
                      type="submit"
                      className="w-full"
                      disabled={form.formState.isSubmitting}
                    >
                      {form.formState.isSubmitting ? 'Resetting…' : 'Reset password'}
                    </Button>
                  </form>
                </Form>
              )}
            </CardContent>
          </Card>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            <Link to="/login" className="underline underline-offset-4 hover:text-foreground">
              Back to sign in
            </Link>
          </p>
        </div>
      </div>

      <Footer />
    </div>
  )
}

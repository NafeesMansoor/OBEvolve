import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'

import { apiClient } from '@/lib/api-client'
import { Footer } from '@/components/footer'
import { ThemeToggleButton } from '@/components/theme-toggle'
import { Logo } from '@/components/logo'
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

const forgotPasswordSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
})

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>

const GENERIC_MESSAGE =
  "If that email is registered, we've sent a link to reset your password. It's valid for 1 hour."

export function ForgotPasswordPage() {
  const [submitted, setSubmitted] = React.useState(false)

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  })

  async function onSubmit(values: ForgotPasswordFormValues) {
    // Always land on the same generic confirmation, whether or not the
    // email is registered — the backend itself never reveals account
    // existence (POST /auth/forgot-password always returns 200), and we
    // keep that guarantee here even in the unlikely event of a network
    // error, rather than surface anything that could be used to probe for
    // registered emails.
    try {
      await apiClient.post('/auth/forgot-password', { email: values.email })
    } finally {
      setSubmitted(true)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-muted/40">
      <div className="flex justify-end p-4">
        <ThemeToggleButton />
      </div>
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex flex-col items-center gap-2 text-center">
            <div className="flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Logo className="size-6" />
            </div>
            <h1 className="font-display text-xl font-semibold tracking-tight">OBEvolve</h1>
            <p className="text-sm text-muted-foreground">
              Outcome-Based Education &amp; accreditation platform
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Forgot password</CardTitle>
              <CardDescription>
                {submitted
                  ? 'Check your email'
                  : "Enter your account email and we'll send you a reset link."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {submitted ? (
                <p className="rounded-md bg-muted px-3 py-2 text-sm text-foreground">
                  {GENERIC_MESSAGE}
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
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email</FormLabel>
                          <FormControl>
                            <Input
                              type="email"
                              autoComplete="email"
                              placeholder="you@institution.edu"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <Button
                      type="submit"
                      className="w-full"
                      disabled={form.formState.isSubmitting}
                    >
                      {form.formState.isSubmitting ? 'Sending…' : 'Send reset link'}
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

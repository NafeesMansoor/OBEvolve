import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'

import { ApiError } from '@/lib/api-client'
import { usePlatformAuth } from '@/lib/platform-auth-context'
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

const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFormValues = z.infer<typeof loginSchema>

/** Separate login surface for `public.platform_admins` — the
 * cross-institution Super Administrator account, distinct from a regular
 * tenant `User` (see /login). Deliberately not linked from the regular
 * login page's UI; reached directly at /platform-login. */
export function PlatformLoginPage() {
  const { login, isAuthenticated } = usePlatformAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [serverError, setServerError] = React.useState<string | null>(null)

  const from = (location.state as { from?: string } | null)?.from ?? '/platform'

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, from, navigate])

  async function onSubmit(values: LoginFormValues) {
    setServerError(null)
    try {
      await login(values.email, values.password)
      navigate(from, { replace: true })
    } catch (err) {
      setServerError(
        err instanceof ApiError ? err.detail : 'Unable to sign in. Please try again.',
      )
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
            <Logo className="text-3xl" />
            <p className="text-sm font-medium tracking-tight text-foreground">Platform Admin</p>
            <p className="text-sm text-muted-foreground">
              Cross-institution administration — separate from institution logins.
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Sign in</CardTitle>
              <CardDescription>Platform administrator credentials only.</CardDescription>
            </CardHeader>
            <CardContent>
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
                            placeholder="admin@example.com"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Password</FormLabel>
                        <FormControl>
                          <Input
                            type="password"
                            autoComplete="current-password"
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
                    {form.formState.isSubmitting ? 'Signing in…' : 'Sign in'}
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            Looking for the institution login?{' '}
            <Link
              to="/login"
              className="text-foreground underline underline-offset-4 hover:text-primary"
            >
              Sign in here
            </Link>
          </p>
        </div>
      </div>

      <Footer />
    </div>
  )
}

import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { AlertCircle, Building2, Database, LogOut, Plus } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { z } from 'zod'

import { ApiError } from '@/lib/api-client'
import { usePlatformAuth } from '@/lib/platform-auth-context'
import { useCreateInstitution, useInstitutions } from '@/features/platform/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Footer } from '@/components/footer'
import { Logo } from '@/components/logo'
import { ThemeToggleButton } from '@/components/theme-toggle'
import { PageHeader } from '@/components/page-header'

const createInstitutionSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  code: z.string().min(1, 'Code is required'),
  slug: z
    .string()
    .min(1, 'Slug is required')
    .regex(/^[a-z0-9-]+$/, 'Lowercase letters, digits, and hyphens only'),
  contact_email: z.string().min(1, 'Contact email is required').email('Enter a valid email'),
  seed_demo: z.boolean(),
})

type CreateInstitutionFormValues = z.infer<typeof createInstitutionSchema>

function statusVariant(status: string): 'default' | 'secondary' | 'destructive' {
  if (status === 'active') return 'default'
  if (status === 'trial') return 'secondary'
  return 'destructive'
}

function CreateInstitutionDialog() {
  const [open, setOpen] = React.useState(false)
  const createInstitution = useCreateInstitution()

  const form = useForm<CreateInstitutionFormValues>({
    resolver: zodResolver(createInstitutionSchema),
    defaultValues: { name: '', code: '', slug: '', contact_email: '', seed_demo: false },
  })

  async function onSubmit(values: CreateInstitutionFormValues) {
    try {
      await createInstitution.mutateAsync(values)
      toast.success(`Institution "${values.name}" provisioned.`)
      form.reset()
      setOpen(false)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Failed to create institution.')
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" />
          New institution
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Provision a new institution</DialogTitle>
          <DialogDescription>
            Creates a new tenant schema with its default roles and permissions.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="University of Example" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="code"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Code</FormLabel>
                  <FormControl>
                    <Input placeholder="UOE" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="slug"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Slug</FormLabel>
                  <FormControl>
                    <Input placeholder="uoe" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="contact_email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contact email</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="admin@uoe.edu" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? 'Provisioning…' : 'Provision'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export function PlatformDashboardPage() {
  const { admin, logout } = usePlatformAuth()
  const navigate = useNavigate()
  const { data: institutions, isLoading, isError } = useInstitutions()

  function handleLogout() {
    logout()
    navigate('/platform-login', { replace: true })
  }

  return (
    <div className="flex min-h-screen flex-col bg-muted/40">
      <header className="flex h-16 shrink-0 items-center justify-between border-b bg-card px-4 md:px-6">
        <div className="flex items-center gap-3">
          <div className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Logo className="size-5" />
          </div>
          <div className="flex items-center gap-2">
            <span className="font-display text-sm font-semibold tracking-tight">OBEvolve</span>
            <Badge variant="outline" className="font-normal text-muted-foreground">
              Platform Admin
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-2 sm:gap-4">
          <Button variant="outline" size="sm" asChild>
            <Link to="/platform/raw-data">
              <Database className="size-4" />
              Raw data console
            </Link>
          </Button>
          <span className="hidden text-sm text-muted-foreground sm:inline">{admin?.email}</span>
          <ThemeToggleButton />
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="size-4" />
            Log out
          </Button>
        </div>
      </header>

      <main className="flex-1 p-4 md:p-8">
        <div className="mx-auto w-full max-w-7xl">
          <PageHeader
            title="Institutions"
            description="Provision and monitor every institution tenant on the platform."
            actions={<CreateInstitutionDialog />}
          />

          <Card>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="flex flex-col gap-3 p-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-8 w-full" />
                  ))}
                </div>
              ) : isError ? (
                <div className="flex flex-col items-center gap-2 py-16 text-center">
                  <AlertCircle className="size-8 text-destructive" />
                  <p className="text-sm text-destructive">Failed to load institutions.</p>
                </div>
              ) : institutions && institutions.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Slug</TableHead>
                      <TableHead>Schema</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Contact</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {institutions.map((inst) => (
                      <TableRow key={inst.id}>
                        <TableCell className="font-medium">{inst.name}</TableCell>
                        <TableCell>{inst.slug}</TableCell>
                        <TableCell className="font-mono text-xs">{inst.schema_name}</TableCell>
                        <TableCell>
                          <Badge variant={statusVariant(inst.status)} className="capitalize">
                            {inst.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{inst.contact_email}</TableCell>
                        <TableCell>
                          {new Date(inst.created_at).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="flex flex-col items-center gap-2 py-16 text-center">
                  <Building2 className="size-8 text-muted-foreground" />
                  <p className="font-medium">No institutions yet</p>
                  <p className="max-w-sm text-sm text-muted-foreground">
                    Provision your first institution to start onboarding programs and users.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>

      <Footer />
    </div>
  )
}

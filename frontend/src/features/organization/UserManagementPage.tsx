import { useAuth } from '@/features/auth/useAuth'
import { RoleMatrixTab } from '@/features/organization/RoleMatrixTab'
import { UsersTab } from '@/features/organization/UsersTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

/** "Users & Roles and Role Matrix need to be in a new Menu item named User"
 * (Institute Settings feedback) — moved out of Institute Settings into its
 * own top-level nav item (see layout.tsx), since user/role administration
 * isn't really "institute settings" so much as its own admin surface. */
export function UserManagementPage() {
  const { hasPermission } = useAuth()

  const tabs = [
    { value: 'users', label: 'Users & roles', show: hasPermission('user.view'), content: <UsersTab /> },
    {
      value: 'role-matrix',
      label: 'Role matrix',
      show: hasPermission('role.manage'),
      content: <RoleMatrixTab />,
    },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['user.view', 'role.manage']}>
      <PageHeader
        title="User"
        description="Program Administrator/Coordinator accounts and role definitions."
      />
      {tabs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No user management sections available.</p>
      ) : (
        <Tabs defaultValue={tabs[0]?.value}>
          <TabsList className="flex-wrap">
            {tabs.map((t) => (
              <TabsTrigger key={t.value} value={t.value}>
                {t.label}
              </TabsTrigger>
            ))}
          </TabsList>
          {tabs.map((t) => (
            <TabsContent key={t.value} value={t.value}>
              {t.content}
            </TabsContent>
          ))}
        </Tabs>
      )}
    </RequirePermission>
  )
}

import type { UserRoleGrant } from '@/features/organization/types'

/**
 * The backend exposes POST /users/user-roles and DELETE /users/user-roles/{id}
 * but no GET to list existing grants (app/api/v1/endpoints/users.py has no
 * such route) — so there is no server-side way to show "this user's current
 * roles" after a page reload. As a pragmatic UI-only workaround, grants made
 * through this admin console are cached in localStorage so the Users page
 * can still show role badges for assignments made here. This will not
 * reflect grants made outside this browser/session (including the seed
 * data's initial admin role) — see ProfilePage/DashboardPage's own
 * roles-from-/auth/me for the one place that's always authoritative for the
 * signed-in user themselves.
 */
const KEY = 'obevolve.role_grants_cache'

function readAll(): UserRoleGrant[] {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as UserRoleGrant[]) : []
  } catch {
    return []
  }
}

function writeAll(grants: UserRoleGrant[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(grants))
  } catch {
    // ignore — best-effort cache only
  }
}

export function getCachedGrantsForUser(userId: string): UserRoleGrant[] {
  return readAll().filter((g) => g.user_id === userId)
}

export function addCachedGrant(grant: UserRoleGrant) {
  const all = readAll()
  all.push(grant)
  writeAll(all)
}

export function removeCachedGrant(grantId: string) {
  writeAll(readAll().filter((g) => g.id !== grantId))
}

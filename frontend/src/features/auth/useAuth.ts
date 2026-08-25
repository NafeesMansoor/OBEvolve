import { useAuthContext } from '@/lib/auth-context'

/**
 * Public entry point for consuming auth state/actions from feature code.
 * Wraps the context hook so feature modules don't import lib/auth-context
 * directly (keeps the provider implementation swappable).
 */
export function useAuth() {
  return useAuthContext()
}

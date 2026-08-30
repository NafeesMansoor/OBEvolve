/**
 * Copyright footer, rendered on every page (see app/layout.tsx's
 * AppLayout, features/auth/LoginPage.tsx, and app/not-found.tsx — the three
 * page-level entry points in this SPA). Centralized here rather than
 * duplicated per page so there is exactly one place that carries the notice.
 */
import drgeekLogo from '@/assets/brand/drgeek-logo.png'

export function Footer() {
  return (
    <footer className="flex shrink-0 items-center justify-center gap-2 border-t bg-card px-4 py-3 text-center text-xs text-muted-foreground md:px-6">
      <span>© 2026 DrGeek. All rights reserved.</span>
      <img src={drgeekLogo} alt="Dr.Geek" className="h-4 w-auto rounded-sm" />
    </footer>
  )
}

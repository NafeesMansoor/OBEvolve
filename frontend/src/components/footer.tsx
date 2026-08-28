/**
 * Copyright footer, rendered on every page (see app/layout.tsx's
 * AppLayout, features/auth/LoginPage.tsx, and app/not-found.tsx — the three
 * page-level entry points in this SPA). Centralized here rather than
 * duplicated per page so there is exactly one place that carries the notice.
 */
export function Footer() {
  return (
    <footer className="shrink-0 border-t bg-card px-4 py-3 text-center text-xs text-muted-foreground md:px-6">
      © 2026 DrGeek. All rights reserved.
    </footer>
  )
}

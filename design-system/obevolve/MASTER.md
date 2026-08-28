# OBEvolve Design System — MASTER

Source of truth for the full-application redesign. Read this before touching any page.
Product: multi-tenant OBE (Outcome-Based Education) accreditation/administration SaaS for
universities — faculty, program admins, deans, students. Stack: React 19 + Vite + Tailwind +
shadcn/Radix primitives, `class-variance-authority`, `lucide-react` icons.

## Style
**Primary:** Data-Dense Dashboard. **Secondary:** Minimalism & Swiss Style, Accessible & Ethical.
Flat/bordered surfaces over heavy shadows. Elevation reserved for truly-floating layers
(dialog, popover, dropdown, sheet) — regular cards use a 1px border, not a drop shadow.
No glassmorphism/blur — this app is read constantly at a desk; blur hurts table legibility.

## Do NOT change
- Any data-fetching, mutation, API call, prop, or business-logic branch. Redesign is
  markup/className/structure only. If a file mixes logic and markup, touch only JSX/className.
- Component *names* or exported prop shapes used by other files (breaks the app).
- The permission-gating logic in nav/pages (`hasPermission`, `anyOfPermissions`, `require-permission.tsx`).

## Color tokens (already wired via `hsl(var(--token))` in `tailwind.config.ts` — edit ONLY `src/index.css`)
**Revision 2** (superseding the original institutional-navy palette): warm cream + sage/olive +
raspberry-rose, per explicit reference hexes from the user: `#FFF7EB`, `#F9F0E0`, `#A2AB73`,
`#CC3A63`. All pairs below are WCAG-verified (4.5:1 text / 3:1 non-text minimum) — the ref hues
are preserved but lightness was tuned per-role for contrast (e.g. primary uses the `A2AB73`
hue/saturation at L30 instead of its literal L56, since the literal tone fails 4.5:1 with white
button text). Don't "correct" these back toward the literal ref hex values without re-running
the contrast math.
Light:
```
--background: 38 68% 93%       (F9F0E0 — warm parchment canvas)
--foreground: 70 20% 15%       (dark olive ink, not cold slate)
--card / --popover: 36 100% 96% (FFF7EB — lighter cream, pops off the canvas)
--card-foreground / --popover-foreground: 70 20% 15%
--primary: 74 32% 30%          (deep moss/sage — A2AB73's hue, darkened for AA text contrast)
--primary-foreground: 36 60% 98%
--secondary: 38 45% 91%
--secondary-foreground: 70 20% 15%
--muted: 38 35% 90%
--muted-foreground: 70 12% 36%
--accent: 38 40% 89%           (neutral hover bg — NOT the brand accent, don't repurpose)
--accent-foreground: 70 20% 15%
--destructive: 343 59% 42%     (CC3A63's hue, darkened slightly for AA with white text)
--destructive-foreground: 36 60% 98%
--success: 152 45% 28%         (kept a separate green hue from primary to avoid confusion)
--success-foreground: 36 60% 98%
--warning: 32 85% 34%          (amber, shifted off the background's own hue-38 so it doesn't
                                 blend in)
--warning-foreground: 36 60% 98%
--border / --input: 38 30% 80%
--ring: 74 40% 38%             (brighter than primary — must stay visible as focus indicator)
--radius: 0.5rem
```
Dark (`.dark`):
```
--background: 35 12% 9%        (warm near-black, not cold navy-black)
--foreground: 38 35% 92%       (cream text — echoes the light-mode canvas color, inverted role)
--card / --popover: 35 12% 12%
--card-foreground / --popover-foreground: 38 35% 92%
--primary: 75 38% 60%          (bright sage, paired with dark ink text — not white text)
--primary-foreground: 70 15% 10%
--secondary / --muted / --accent: 35 12% 16%-18%
--secondary-foreground / --accent-foreground: 38 35% 92%
--muted-foreground: 38 15% 65%
--destructive: 343 60% 62%
--destructive-foreground: 70 15% 10%
--success: 152 42% 48%
--success-foreground: 70 15% 10%
--warning: 32 80% 55%
--warning-foreground: 70 15% 10%
--border / --input: 35 12% 20%
--ring: 75 45% 62%
```
Workflow status colors (`status-badge.tsx`) stay in their existing blue/amber/emerald/violet
family — already distinct from primary/accent and already accessible; do not merge them into
the new primary/warning tokens.

## Question authoring: Bloom's Level + CO mapping, not "difficulty"
`Question.difficulty` (free-text column) is no longer shown in any create/edit UI — a question
is classified by **Bloom's cognitive level** (single select, `BloomLevel` catalogue seeded per
institution with the 6 standard levels via `app/seed/bloom_defaults.py`, exposed read-only at
`GET /curriculum/bloom-levels`) and **which course outcome(s) it targets** (multi-select CO
checklist). Both are relations (junction tables `question_bloom_mappings` /
`question_co_mappings`), not columns on `Question`, so question creation uses a bespoke dialog
(`features/assessment/NewQuestionDialog.tsx`) rather than the generic `EntityFormDialog` —
it creates the question, then fires the mapping POSTs. Editing an existing question's Bloom/CO
mappings happens via the existing per-row "Mappings" button/dialog
(`QuestionMappingsDialog` in `QuestionsTab.tsx`).

## Light/dark mode toggle
The app now has a real theme switch (`next-themes` `ThemeProvider` wraps `<App />`, `class`
attribute strategy matching `tailwind.config.ts`'s `darkMode: ['class']`, default `system`,
`localStorage`-persisted). The toggle lives in the account dropdown in `app/layout.tsx`
(and equivalently on the platform-admin chrome). Don't add a second theme mechanism anywhere
— always read/write theme via `next-themes`' `useTheme()`, never a hand-rolled context.

## Typography
- Headings (`font-display`, used via `h1,h2,h3 { @apply font-display }` in index.css):
  **Plus Jakarta Sans** (weights 500/600/700/800), replacing Lexend.
- Body/UI/data (`font-sans`, default): **keep Inter** (400/500/600) — proven at 12-13px in
  dense tables; do not swap body font.
- Google Fonts `<link>` in `index.html` must be updated to pull Plus Jakarta Sans instead of
  Lexend (keep Inter import).
- Page titles: `text-2xl font-display font-semibold tracking-tight` (was `font-semibold` on
  the default sans). Section/card titles: `font-display font-semibold`.
- KPI/stat numbers: `font-display font-semibold tabular-nums`.

## Spacing / density
Comfortable-dense, not cramped: table rows ~40px, header row ~36-40px, card padding
`p-5`/`p-6` (unchanged), page container gutter `p-4 md:p-8` (unchanged). Sidebar stays 256px
(`w-64`). Header stays `h-16` (keeps room for program/role switchers + avatar on desktop).

## Elevation
- `Card`: `rounded-lg border bg-card text-card-foreground shadow-sm` → drop the heavier
  `shadow` default, keep only `shadow-sm`, rely on the border for definition.
- Dialog/Sheet/Popover/DropdownMenu content: keep/increase to `shadow-lg` — these are the
  layers allowed real elevation.
- Table container: `rounded-md border` (unchanged pattern), no shadow.

## Icons
Keep `lucide-react` (already the icon set in use — matches the "no emoji, one consistent SVG
family" rule). Consistent sizing: `size-4` inline/inside controls, `size-5` for standalone nav
icons. Icon-only buttons must keep/get an `aria-label` (audit `DataTable` row actions, most
`ImportFromXDialog`/`RowFormDialog` trigger buttons).

## Known structural gap to fix
`app/layout.tsx`'s sidebar is `hidden md:flex` with **no mobile fallback nav at all** — below
the `md` breakpoint there is currently no way to navigate. Fix: add a `Sheet`-based drawer
(trigger = hamburger `Menu` icon in the mobile header) reusing the same `navItems`/permission
filtering. This is the single highest-priority functional fix in the redesign
(`adaptive-navigation`, `persistent-nav` rules).

## Per-page redesign checklist (apply everywhere)
1. `PageHeader`: title in `font-display`, consistent action-button placement (primary action
   rightmost, `variant="default"`; secondary actions `variant="outline"`/`"ghost"` to its left).
2. Empty states: icon + message + (if applicable) a primary action, not just bare text.
3. Loading states: `Skeleton` matching the real content's shape (already the pattern in
   `DataTable` — replicate for card/detail views that roll their own loading branch).
4. Forms: labels always visible (never placeholder-only), errors inline below the field,
   required fields marked, submit buttons show a loading state while pending.
5. Destructive actions (delete/reject/unpublish) always `variant="destructive"` and spatially
   separated from primary actions — never adjacent same-style buttons.
6. Status/workflow badges always use `StatusBadge`/`Badge`, never raw colored text.
7. All interactive elements get `cursor-pointer` where not already implied, and visible
   `focus-visible` rings (inherited from `ui/button.tsx` etc. — don't strip `focus-visible`
   classes when restyling).
8. Dark mode: verify every new/changed color against `.dark` — don't hardcode hex/raw colors
   in feature files, only semantic Tailwind classes (`bg-card`, `text-muted-foreground`, ...).
9. No horizontal page scroll on mobile; wide tables get `overflow-x-auto` wrappers (already
   the `DataTable`/`Table` pattern — preserve it).

## Feature areas (for the parallel rebuild pass)
- `features/dashboard/` — landing page + student attainment panel + admin overview stats
- `features/academic-ops/` — offerings/sections/enrollments/faculty-assignments/students tabs
- `features/curriculum/` — PEOs/POs/COs, mapping matrices, program/course settings, analytics
- `features/assessment/` — assessments/questions/rubrics/types/marks-entry/attainment tabs
- `features/organization/` — institution/campuses/schools/departments/programs/users/calendar
- `features/grading/`, `features/improvement/`, `features/analytics/`
- `features/auth/` — login/forgot/reset password, Google sign-in
- `features/platform/` — platform-admin login/dashboard/raw-data (separate tenant context)
- `features/raw-data/` — generic table browser/editor console + pending changes
- `features/profile/`, `features/about/`
- Shared: `app/layout.tsx`, `app/not-found.tsx`, `components/*` (non-`ui/`), `components/ui/*`

Shared/foundation files are owned by the first pass (tokens, `ui/` primitives, layout, shared
`components/*`). Feature-area passes build on top of the already-redesigned primitives —
don't re-invent card/button/table styling per page, compose the shared components.

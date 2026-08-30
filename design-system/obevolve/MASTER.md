# OBEvolve Design System — MASTER

Source of truth for the full-application redesign. Read this before touching any page.
Product: multi-tenant OBE (Outcome-Based Education) accreditation/administration SaaS for
universities — faculty, program admins, deans, students. Stack: React 19 + Vite + Tailwind +
shadcn/Radix primitives, `class-variance-authority`, `lucide-react` icons.

## Style
**Primary:** Data-Dense Dashboard. **Secondary:** Minimalism & Swiss Style, Accessible & Ethical.
As of Revision 3, cards use the shadcn default `shadow-sm` + 0.75rem radius (soft-elevated,
rounded-xl) rather than a flat 1px border — this is the modern analytics-SaaS-dashboard
convention (see Revision 3 note below) and reads as more "product," less "spreadsheet," without
adding real elevation depth. Heavier elevation (`shadow-md`/`shadow-lg`) stays reserved for
truly-floating layers (dialog, popover, dropdown, sheet). No glassmorphism/blur — this app is
read constantly at a desk; blur hurts table legibility even though Framer's own site uses it.

## Do NOT change
- Any data-fetching, mutation, API call, prop, or business-logic branch. Redesign is
  markup/className/structure only. If a file mixes logic and markup, touch only JSX/className.
- Component *names* or exported prop shapes used by other files (breaks the app).
- The permission-gating logic in nav/pages (`hasPermission`, `anyOfPermissions`, `require-permission.tsx`).

## Color tokens (already wired via `hsl(var(--token))` in `tailwind.config.ts` — edit ONLY `src/index.css`)
**Revision 3** (current — supersedes Revision 2's cream/sage/rose palette below): a real
visual-direction change, not a refresh, requested explicitly by the user to align with
`docs/UI_UX_redesign.md` §2-3, which names two references —
a Dribbble SaaS-analytics-dashboard light theme (cool near-white canvas, white cards, single
vivid-indigo accent — the standard genre convention for that whole category of shot, not one
exact shot's literal pixels) and Framer.com's dark theme (near-black canvas, bright accent
popping off it). One brand hue (229°, indigo-blue) carries across both themes for continuity —
only lightness/saturation shift between light and dark, which is why `--primary`/`--ring` share
a hue in both blocks below. All pairs are WCAG-verified (4.5:1 text minimum; computed via a
one-off relative-luminance script, not eyeballed) — see git history on this file for the exact
numbers if you need to re-derive. `--radius` moved from 0.5rem to 0.75rem (rounded-xl) to match
the softer card language both references use; see the Style section above for the accompanying
shadow-vs-border change.
Light:
```
--background: 220 25% 98%      (cool near-white canvas, not warm cream)
--foreground: 222 30% 12%      (deep slate-navy ink)
--card / --popover: 0 0% 100%  (pure white — pops off the tinted canvas)
--card-foreground / --popover-foreground: 222 30% 12%
--primary: 229 84% 58%         (vivid indigo-blue — the single brand accent)
--primary-foreground: 0 0% 100%
--secondary: 222 20% 95%
--secondary-foreground: 222 30% 12%
--muted: 222 20% 95%
--muted-foreground: 222 15% 40%
--accent: 222 20% 94%          (neutral hover bg — NOT the brand accent, don't repurpose)
--accent-foreground: 222 30% 12%
--destructive: 356 75% 48%
--destructive-foreground: 0 0% 100%
--success: 152 55% 32%
--success-foreground: 0 0% 100%
--warning: 38 92% 45%
--warning-foreground: 222 30% 12%
--border / --input: 220 18% 90%
--ring: 229 84% 58%            (same hue as primary — the vivid accent doubles as the focus ring)
--radius: 0.75rem
```
Dark (`.dark`):
```
--background: 240 8% 6%        (near-black, Framer-style — not warm, not navy)
--foreground: 210 20% 96%
--card / --popover: 240 6% 10%
--card-foreground / --popover-foreground: 210 20% 96%
--primary: 229 90% 65%         (brightened for contrast on near-black; paired with dark-ink text)
--primary-foreground: 240 8% 6%
--secondary / --muted: 240 6% 14%
--accent: 240 6% 16%
--secondary-foreground / --accent-foreground: 210 20% 96%
--muted-foreground: 215 12% 65%
--destructive: 356 80% 62%
--destructive-foreground: 240 8% 6%
--success: 152 50% 52%
--success-foreground: 240 8% 6%
--warning: 38 90% 58%
--warning-foreground: 240 8% 6%
--border / --input: 240 8% 18%
--ring: 229 90% 65%
```
Workflow status colors (`status-badge.tsx`) stay in their existing blue/amber/emerald/violet
family — already distinct from primary/accent and already accessible; do not merge them into
the new primary/warning tokens.

<details>
<summary>Revision 2 (superseded 2026-08 — kept for history, do not reapply)</summary>

Warm cream + sage/olive + raspberry-rose, per explicit reference hexes from the user:
`#FFF7EB`, `#F9F0E0`, `#A2AB73`, `#CC3A63`.
```
--background: 38 68% 93%   --foreground: 70 20% 15%
--card/--popover: 36 100% 96%
--primary: 74 32% 30%      --primary-foreground: 36 60% 98%
--secondary: 38 45% 91%    --muted: 38 35% 90%   --muted-foreground: 70 12% 36%
--accent: 38 40% 89%       --destructive: 343 59% 42%
--success: 152 45% 28%     --warning: 32 85% 34%
--border/--input: 38 30% 80%  --ring: 74 40% 38%  --radius: 0.5rem
```
</details>

**Revision 4** (superseded by Revision 5 — kept for history): retuned `--primary`/`--ring` to
228° indigo-blue to match the logo that existed at the time (`ref/OBEvolve_logo.png`, an
icon+gradient wordmark). That logo was replaced; none of Revision 4's values are live — see
git history on this file if the indigo direction is ever needed again.

**Revision 5** (current — red rebrand, 2026-08): the OBEvolve logo changed to a plain red
wordmark (`ref/logo.png` — "OBE" set in white with a red keyline, "volve" solid red; no icon
glyph, no gradient). `--primary`/`--ring` were retuned to the logo's exact sampled red — 9°
hue, fully saturated (RGB 222,29,0, sampled directly from the "volve" pixels) — re-verified
against WCAG AA (light: 4.76:1 vs white, 4.54:1 as text on canvas; dark: 5.76:1 vs dark-ink).
`--destructive` was deliberately shifted from 356° to 348° (a visibly pinker/cooler red) to
keep a clear hue gap from the new brand-red primary — a same-hue primary and destructive is a
real mistap risk on a red-themed product (a "Save"/"Submit" button must never look like a
"Delete" button); 21° of separation plus the warm-vs-cool split reads as two different reds at
a glance, matching the separation used by red-primary products more broadly (rose/crimson
primary + pure-red destructive is a common, deliberate pairing, not sloppiness). Neutral tokens
(`--background`/`--foreground`/`--secondary`/`--muted`/`--accent`/`--border`) were also rotated
from the old cool blue-gray hue (~220°) to a true-neutral warm gray (~15°) — same S/L values,
so contrast ratios are unchanged — because a blue-tinted gray fights a red accent by
simultaneous contrast (reds look muddier next to cool grays than true-neutral ones).
`--brand-violet`/`--brand-cyan` (tied to the old gradient logo) are retired; replaced with a
monochrome tint/shade pair of the one brand hue:
```
--brand-red-light: 9 90% 68%  (dark: 9 90% 72%)  — light tint, for gradient starts/washes
--brand-red-deep:  9 85% 28%  (dark: 9 80% 32%)   — dark shade, for gradient ends/depth
```
Tailwind exposes these as `bg-brand-red-light`/`bg-brand-red-deep`/`text-brand-red-light` etc.,
plus a `bg-brand-gradient` utility (light → primary → deep, 135deg, all one hue — "shades of
red," not a multi-hue gradient) for hero/decorative surfaces only (e.g. the About page banner's
top accent strip) — never for body text, buttons, or anything already carrying a semantic
token, and never as a backdrop directly behind the white-filled "OBE" half of the wordmark
(the white fill needs a neutral or dark backdrop to read — see Logo assets below).

### Logo assets

`ref/logo.png` (source, 145×52 after trim — too small to use as a raster UI asset above
favicon size) is reproduced as real text, not an image: `frontend/src/components/logo.tsx`
exports `Logo` (the full "OBEvolve" wordmark — "OBE" white with a `-webkit-text-stroke` in
`--primary` reproducing the source's red keyline, `paint-order: stroke fill` so the stroke
doesn't eat into the fill; "volve" solid `text-primary`; sized via font-size utilities like
`text-lg`/`text-3xl`, not `size-*`) and `LogoMark` (a compact single-letter "O" monogram badge
for spaces too tight for the full wordmark — collapsed sidebar, favicon-adjacent contexts;
sized via `size-*`, it's a square). The source logo has no separate icon glyph, so `LogoMark`
is a derived monogram, not a cropped asset. Because "OBE" relies on its red stroke for contrast,
never place `Logo` directly on a `bg-primary`/`bg-brand-gradient`/other red surface — the white
fill and stroke both read as the same hue as the background and the wordmark disappears; only
neutral (`bg-card`, `bg-background`, `bg-popover`) or dark surfaces are safe backdrops. Favicon
PNGs (`frontend/public/favicon-32.png`/`-48.png`/`apple-touch-icon.png`) are regenerated
straight from the trimmed source raster (`sips`/Pillow, LANCZOS upscale, centered on a padded
transparent square) since a 32-48px tab icon is small enough that the low source resolution
doesn't show. `ref/drgeek_logo.jpg` (developer credit) is unrelated to this rebrand — still
cropped to `frontend/src/assets/brand/drgeek-logo.png` and shown small in `Footer`.

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

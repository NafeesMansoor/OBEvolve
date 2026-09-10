> **For OBEvolve:** this is the origin reference. It was adopted and absorbed into
> [`design-system/obevolve/MASTER.md`](../design-system/obevolve/MASTER.md)'s Revision 6,
> then Revision 7 retuned the one accent hue off amber to a neon green (explicit user hex
> request) — read that file as the live spec (exact HSL tokens, WCAG numbers, and the
> handful of deliberate deltas from this doc, e.g. one accent hue carried across both
> light/dark instead of dark-only). The swatch table below is updated to match Revision 7's
> dark-mode values so this reference stays internally consistent, but this file remains
> portable reference/history, not a second source of truth for this repo.

# Design System — "Ink & Amber"

A portable design language extracted from SQL Case Files. Drop this file into any
React + Tailwind CSS project's `Docs/` folder (or hand it to Claude at the start of a
new project) to get the same clean, confident, dark-first UI: neutral slate/ink
surfaces stepped by elevation, a single warm amber accent used sparingly, monospace
for anything numeric or code-like, and borders instead of heavy shadows for structure.

This is a **system**, not just a palette: it defines *how many* colors to use and
*when*, not only which hex codes. Section 10 explains how to re-skin it with a
different accent hue while keeping everything else — the part that actually makes it
look designed — intact.

---

## 1. Design principles

1. **One accent color, used deliberately.** Amber marks the single most important
   action or piece of information on a screen (primary button, active nav item, XP/key
   metric, links). Everything else is neutral. If more than ~20% of a screen is
   colored, the accent has stopped being an accent.
2. **Hierarchy through elevation, not decoration.** Five steps of one neutral hue
   (`ink-950` → `ink-600`) do all the layout work: darkest = page background, each
   step up = one level "closer" to the user (card → input/hover surface → border).
   No drop shadows, no gradients, no glassmorphism beyond a single blurred sticky nav.
3. **Borders separate, backgrounds elevate.** A 1px `border-ink-700` (or the subtler
   `border-ink-800`) is the default way to define a card or divide a table row —
   reach for a shadow only if you truly need to imply floating above content (rare).
4. **Monospace = data.** Anything numeric, code-like, or an identifier (XP counts,
   table/column names, SQL, join codes, IDs) renders in the mono stack. Everything a
   human reads as prose renders in the sans stack. This single rule does a lot of the
   "feels like a serious tool" work.
5. **Semantic color is categorical, not decorative.** Green/red/amber/blue/purple only
   ever mean something specific (success, danger, warning/mid, info, a category tier)
   and always follow the same recipe: a low-opacity tinted background + a matching
   border + a saturated text color (see §4).
6. **Generous, consistent spacing over dense chrome.** Cards breathe (`p-4`/`p-5`),
   page containers cap width (`max-w-7xl` for dashboards, `max-w-sm`/`max-w-lg` for
   forms) and center (`mx-auto`), sections stack with `gap-4`–`gap-6`.
7. **Respect the platform.** `prefers-reduced-motion` is honored globally, focus is
   always visible (`focus:border-amber-500`, never `outline-none` without a
   replacement), and interactive elements always show a `disabled:opacity-50` state
   rather than disappearing.

---

## 2. Color tokens

Add these to `tailwind.config.js`. `ink` is the neutral scale everything sits on;
`amber` is the single accent; `case.blue` is an optional *secondary* accent reserved
for one specific recurring action (see §4.2) — rename it per project (e.g. `brand.blue`).

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0b0e14", // page background
          900: "#11151d", // card / panel surface
          800: "#171c26", // input fields, hover surfaces, secondary chips
          700: "#212836", // default border, active nav pill background
          600: "#2c3444", // input borders, subtle dividers, scrollbar thumb
        },
        amber: {
          // OBEvolve Revision 7 ("Ink & Neon"): these three swatches were
          // retuned from amber to a neon green per explicit user hex
          // request — the `amber` key name is kept (this doc is meant to
          // be re-skinned in place per §10, not renamed) but the values
          // are OBEvolve's live dark-mode palette.
          300: "#39FF14", // rare: bright inline highlight text on dark success/info banners
          400: "#7FFF00", // links, hover accent, secondary emphasis text
          500: "#CCFF00", // primary button fill, active/selected state
        },
        case: {
          blue: "#4c8dff", // secondary accent for one recurring "go/run" action
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};
```

Everything else — text, success, danger, info, category tiers — is stock Tailwind
`slate`, `emerald`, `red`, `blue`, `purple`. Do not invent new neutrals or accents
beyond what's above; the discipline of a small palette is what reads as "designed."

### Text color scale (stock `slate`, used consistently)

| Token | Usage |
|---|---|
| `text-white` | Headings, primary button/card labels on dark surfaces, high-emphasis values |
| `text-slate-200` / `text-slate-300` | Body copy, secondary emphasis, table cell values |
| `text-slate-400` | Descriptions, nav inactive state, muted labels |
| `text-slate-500` | Meta text (timestamps, counts, placeholders), disabled-adjacent |
| `text-slate-600` | Rarely — the quietest text (e.g. `NULL` in a data table) |

### Base surface + text (global)

```css
:root {
  color-scheme: dark;
}
body {
  @apply bg-ink-950 text-slate-100;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}
```

---

## 3. Typography

- **Sans** (default, prose/UI text): `ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif`
- **Mono** (`font-mono`, data/code/identifiers): `ui-monospace, SFMono-Regular, Menlo, monospace`

| Role | Classes |
|---|---|
| Page title | `text-2xl font-semibold text-white` |
| Section title (card header) | `text-sm font-semibold uppercase tracking-wide text-slate-400` (an "eyebrow" label, not a big heading — used constantly instead of `<h2>`-sized headings inside cards) |
| Card / list-item title | `text-lg font-semibold text-white` |
| Body copy | `text-sm text-slate-300` (or `leading-relaxed` for longer prose blocks) |
| Meta / caption | `text-xs text-slate-500` |
| Tiny tag / chip text | `text-[11px]` |
| Data value (stat tile number) | `text-2xl font-semibold text-white` |
| Data value (inline, table/pill) | `font-mono` + a color per §2/§4 |
| Eyebrow / kicker above a title | `text-xs uppercase tracking-wide text-amber-500` |

Rule of thumb: **`uppercase tracking-wide` + small size + `text-slate-400`/`text-slate-500`**
is the recurring "label" treatment used for section headers, table headers, and stat
tile captions throughout. Reach for it instead of a bigger, bolder heading.

---

## 4. Semantic color recipes

### 4.1 Status / feedback (banners, inline messages)

Every semantic color follows the same three-part recipe: `border-{color}-900`
+ `bg-{color}-950/40` (or `/30`) + `text-{color}-200`–`300`. Never use a solid
saturated background on dark UI — always the very dark tint at 30–40% opacity.

```html
<!-- Success -->
<div class="rounded-lg border border-emerald-800 bg-emerald-950/40 p-4 text-emerald-200">
  <p class="font-semibold">✓ Success headline</p>
  <p class="mt-1 text-sm text-emerald-300/90">Supporting detail.</p>
</div>

<!-- Error -->
<div class="rounded-lg border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">
  Error message text.
</div>

<!-- Inline field error (no border box, just text) -->
<p class="rounded-md bg-red-950/50 px-3 py-2 text-sm text-red-300">Inline validation message.</p>
```

### 4.2 Two accents, two distinct jobs

Don't let two accent colors blur together — give each a fixed job and never swap them:

- **Amber** = the primary/default action, selection, and "this matters" marker
  (primary buttons, active nav, XP counters, links, focus rings).
- **Secondary blue** (`case-blue` / rename per project) = reserved for exactly one
  recurring *secondary* action that always appears alongside an amber primary action
  (e.g. "Run" next to "Submit", or "Preview" next to "Publish"). If you don't have such
  a paired action, skip blue entirely and stay single-accent.

### 4.3 Categorical / tier badges

For any small fixed set of categories (difficulty, role, plan tier, status type), map
each value to one of these five recipes and reuse the *same* five across the whole app
— don't invent a sixth without a reason:

```js
const TIER_COLOR = {
  tierA: "text-emerald-400 border-emerald-900 bg-emerald-950/40", // easiest / lowest / free
  tierB: "text-blue-400   border-blue-900    bg-blue-950/40",     // 2nd
  tierC: "text-purple-400 border-purple-900  bg-purple-950/40",   // 3rd
  tierD: "text-amber-400  border-amber-900   bg-amber-950/40",    // 4th / caution
  tierE: "text-red-400    border-red-900     bg-red-950/40",      // hardest / highest / danger
};
```
```html
<span class="rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide {{TIER_COLOR[value]}}">
  {{label}}
</span>
```

### 4.4 Progress / mastery bars

Three-way threshold coloring for any 0–100% metric:

```jsx
const color = pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";
```
```html
<div class="h-2 flex-1 overflow-hidden rounded-full bg-ink-700">
  <div class="h-full {{color}} transition-all" style="width: {{pct}}%"></div>
</div>
```

---

## 5. Core component recipes

Copy these directly. `rounded-md` (buttons, inputs, small chips) and `rounded-lg`
(cards, panels, banners) are the only two radii used — never mix in `rounded-xl`/`2xl`.

### 5.1 Buttons

```html
<!-- Primary (amber) -->
<button class="rounded-md bg-amber-500 px-4 py-1.5 text-sm font-semibold text-ink-950
               hover:bg-amber-400 disabled:opacity-50 transition">
  Primary action
</button>

<!-- Secondary action (only when it's a distinct recurring paired action, see 4.2) -->
<button class="rounded-md bg-case-blue px-4 py-1.5 text-sm font-medium text-white
               hover:bg-blue-500 disabled:opacity-50">
  Run
</button>

<!-- Neutral / outline (default for anything not primary) -->
<button class="rounded-md border border-ink-600 px-3 py-1.5 text-sm text-slate-300
               hover:border-ink-500 hover:text-white">
  Cancel
</button>

<!-- Small outline (toolbar-style, e.g. table header actions) -->
<button class="rounded border border-ink-600 px-2 py-0.5 text-xs text-slate-300
               enabled:hover:border-amber-500 enabled:hover:text-amber-400 disabled:opacity-40">
  Export
</button>

<!-- Text link -->
<a class="text-amber-400 hover:underline">Link text</a>
```

### 5.2 Form fields

Always pair a real `<label htmlFor>` / `id` (accessibility — screen readers, and lets
tests/automation use `getByLabel`). Label styling is the same "eyebrow" treatment as
section headers.

```html
<div>
  <label for="email" class="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-400">
    Email
  </label>
  <input id="email" type="email"
         class="w-full rounded-md border border-ink-600 bg-ink-800 px-3 py-2 text-sm text-white
                outline-none focus:border-amber-500" />
</div>
```

### 5.3 Cards / panels

```html
<!-- Static panel -->
<div class="rounded-lg border border-ink-700 bg-ink-900 p-5">
  ...
</div>

<!-- Interactive card (clickable / link) -->
<a href="#" class="group flex flex-col rounded-lg border border-ink-700 bg-ink-900 p-5
                    transition hover:border-amber-500/60">
  <h2 class="text-lg font-semibold text-white group-hover:text-amber-400">Title</h2>
</a>

<!-- Disabled / locked card -->
<div class="flex flex-col rounded-lg border border-ink-800 bg-ink-900/50 p-5 opacity-60
            cursor-not-allowed">
  ...
</div>
```

### 5.4 Stat tile

```html
<div class="rounded-lg border border-ink-700 bg-ink-900 p-4">
  <div class="text-xs uppercase tracking-wide text-slate-500">Label</div>
  <div class="mt-1 text-2xl font-semibold text-white">{{value}}</div>
</div>
```

### 5.5 Pills, tags, chips

```html
<!-- Metric pill (e.g. a counter in the nav bar) -->
<span class="rounded-full bg-ink-800 px-3 py-1 font-mono text-amber-400">{{value}}</span>

<!-- Small neutral tag (e.g. a concept/skill chip) -->
<span class="rounded bg-ink-800 px-2 py-0.5 text-[11px] text-slate-400">{{label}}</span>

<!-- Status pill — see §4.3 for the color recipe -->
<span class="rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide
             text-emerald-400 border-emerald-900 bg-emerald-950/40">{{status}}</span>
```

### 5.6 Tables

```html
<table class="w-full border-collapse text-left text-xs">
  <thead class="sticky top-0 bg-ink-900">
    <tr>
      <th class="whitespace-nowrap border-b border-ink-700 px-3 py-2 font-mono text-slate-300">
        column_name
      </th>
    </tr>
  </thead>
  <tbody>
    <tr class="border-b border-ink-800 hover:bg-ink-800/60">
      <td class="px-3 py-1.5 font-mono text-slate-200">value</td>
    </tr>
  </tbody>
</table>
```

Rules: header row = `bg-ink-900` + `border-b border-ink-700` + `font-mono` (columns
read as identifiers); body rows = `border-b border-ink-800` (one step subtler) +
`hover:bg-ink-800/60` for row-level interactivity instead of zebra striping.

### 5.7 Navigation bar

```html
<header class="sticky top-0 z-30 border-b border-ink-700 bg-ink-950/95 backdrop-blur">
  <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
    <!-- logo mark: colored square + glyph -->
    <div class="grid h-7 w-7 place-items-center rounded bg-amber-500 text-ink-950">◎</div>
    <nav class="flex gap-1">
      <!-- active -->
      <a class="rounded-md bg-ink-700 px-3 py-2 text-sm text-amber-400">Active</a>
      <!-- inactive -->
      <a class="rounded-md px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-ink-800">Inactive</a>
    </nav>
  </div>
</header>
```

The single blurred sticky header (`bg-ink-950/95 backdrop-blur`) is the *only* place
translucency/blur is used in the whole system — keep it that way, it stays special.

### 5.8 Mobile tab bar

For content too dense to show all at once on small screens (used instead of just
shrinking the desktop layout — see §7):

```html
<div class="flex gap-1">
  <button class="flex-1 rounded-md px-2 py-1.5 text-xs capitalize bg-ink-700 text-amber-400">Active tab</button>
  <button class="flex-1 rounded-md px-2 py-1.5 text-xs capitalize bg-ink-900 text-slate-400">Tab</button>
</div>
```

### 5.9 Brand mark

A single glyph (emoji, simple unicode symbol, or 1-color SVG) centered in a colored
square is the whole "logo" — no illustrated logo needed for an MVP:

```html
<div class="grid h-12 w-12 place-items-center rounded-lg bg-amber-500 text-xl text-ink-950">◎</div>
```

---

## 6. Spacing, layout & radius scale

- **Radii**: `rounded` (chips/small icons) · `rounded-md` (buttons, inputs) ·
  `rounded-lg` (cards, panels, banners) · `rounded-full` (pills, avatars). Nothing else.
- **Page container**: `mx-auto max-w-7xl px-4 py-8` for dashboards/lists;
  `mx-auto max-w-sm` / `max-w-lg` centered with `min-h-screen grid place-items-center`
  for auth/focused forms.
- **Card padding**: `p-4` (compact, stat tiles) or `p-5` (standard panel).
- **Vertical rhythm**: stack sections with `space-y-4`/`space-y-6`/`space-y-8` (page
  level) or `gap-4`/`gap-6` in a grid; stack form fields with `space-y-4`.
- **Borders as the default separator**: `border border-ink-700` around a whole panel;
  `border-t`/`border-b border-ink-800` between rows/items inside one.

---

## 7. Responsive pattern

Do not just shrink the desktop grid. For any screen with multiple dense panels
(e.g. a workspace with a sidebar + main content + a results panel):

1. Desktop (`lg:` and up): CSS grid, e.g. `hidden lg:grid lg:grid-cols-[320px_1fr]`.
2. Mobile (below `lg:`): render the *same* panels as separate views switched by the
   tab bar in §5.8, each shown/hidden by a `mobileTab` state variable — not by
   scrolling a squeezed grid.
3. Nav: full link row on `sm:` and up; on mobile, add a second horizontally-scrollable
   row (`flex gap-1 overflow-x-auto`) below the main header bar rather than a hamburger
   menu, when there are only a handful of top-level destinations.

---

## 8. Motion & accessibility

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}
```

- Transitions are short and functional (`transition`, `transition-all` on hover/width
  changes) — never decorative page-load animation.
- Every disabled control gets `disabled:opacity-50` (or `:40` for smaller ghost
  buttons) — never just a `cursor-not-allowed` with no visual change.
- Every focusable input gets a visible focus state: `outline-none focus:border-amber-500`
  (replacing the browser default with an intentional one — never remove focus styling
  without replacing it).
- Every `<label>` is wired to its input via `htmlFor`/`id` (real accessibility, and it
  makes the UI testable via accessible-name queries).
- Custom scrollbar (webkit) kept subtle and on-theme:

```css
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2c3444; border-radius: 6px; } /* ink-600 */
```

---

## 9. Worked example: a "form + list" page

Putting §2–§6 together — this shape (title, description, action row, grid of cards)
recurs for almost any index/list page in this system:

```jsx
<div className="mx-auto max-w-7xl px-4 py-8">
  <h1 className="text-2xl font-semibold text-white">Page Title</h1>
  <p className="mt-1 text-slate-400">One-line description of what this page is for.</p>

  <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {items.map((item) => (
      <a key={item.id} href={`/items/${item.id}`}
         className="group flex flex-col rounded-lg border border-ink-700 bg-ink-900 p-5
                     transition hover:border-amber-500/60">
        <div className="flex items-center justify-between">
          <span className="rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-wide
                            text-emerald-400 border-emerald-900 bg-emerald-950/40">
            {item.category}
          </span>
          <span className="text-xs text-slate-500">{item.status}</span>
        </div>
        <h2 className="mt-3 text-lg font-semibold text-white group-hover:text-amber-400">
          {item.title}
        </h2>
        <p className="mt-1 text-xs text-slate-500">{item.meta}</p>
      </a>
    ))}
  </div>
</div>
```

---

## 10. Re-skinning: keeping the system, changing the color

To reuse this system with a different brand color, change exactly three things and
nothing else:

1. Swap the `amber` values in `tailwind.config.js` for your hue (keep two shades: a
   mid tone ~500 for fills, a lighter ~400 for hover/links/text-on-dark).
2. Swap every `text-amber-*`, `bg-amber-*`, `border-amber-*`, `hover:*-amber-*`
   utility for your new color name (a find/replace, since it's one token family).
3. Leave **everything else untouched**: the `ink` neutral scale, the semantic
   emerald/red/blue/purple recipes, typography, radii, and spacing are what make this
   read as a coherent system — they are not "amber-specific."

If you need a **light mode** variant: keep the same structural rules (one accent,
neutral elevation scale, mono-for-data) but build a parallel light neutral scale
(e.g. white → slate-50 → slate-100 → slate-200 borders) rather than trying to invert
`ink` automatically — dark and light neutral scales are rarely true inverses of each
other at the same steps.

---

## 11. Checklist for a new page

- [ ] Page background is inherited (`bg-ink-950` on `body`) — don't set it per-page.
- [ ] Container is `mx-auto max-w-7xl px-4 py-8` (or a centered `max-w-sm`/`lg` for a
      single-purpose form).
- [ ] Every panel is `rounded-lg border border-ink-700 bg-ink-900 p-5` (or `p-4` if
      compact) — no ad hoc panel styles.
- [ ] Exactly one amber primary action is visually dominant per screen.
- [ ] Any numeric/code/identifier value uses `font-mono`.
- [ ] Any status/category uses one of the five fixed semantic recipes (§4.3), not a
      new color.
- [ ] Labels are `text-xs uppercase tracking-wide text-slate-400/500`, not ad hoc sizes.
- [ ] Every input has a real `<label htmlFor>`; every disabled control shows
      `disabled:opacity-50`; focus is visible.
- [ ] Mobile isn't just a squeezed version of desktop — check it at ~390px wide.

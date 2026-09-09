import { cn } from '@/lib/utils'

/**
 * OBEvolve's wordmark: "OBE" set in white with a neon-green keyline, "volve"
 * solid neon-green (Revision 7, "Ink & Neon" — see design-system/obevolve/
 * MASTER.md) — reproduced as real text so it stays crisp at any size and
 * repaints automatically with the theme via the `--primary` token.
 * `-webkit-text-stroke` on "OBE" is what makes the white fill read against a
 * light canvas — light mode only; dark mode drops the stroke (plain white
 * reads fine on a dark surface, and the keyline looked heavy there) via a
 * `dark:` override. `paint-order: stroke fill` (light mode) keeps the
 * stroke from eating into the white fill. Size via font-size utilities on
 * `className` (e.g. `text-lg`, `text-3xl`), not `size-*`.
 */
export function Logo({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-baseline font-display font-extrabold leading-none tracking-tight',
        className,
      )}
    >
      <span className="text-white [-webkit-text-stroke:0.16em_hsl(var(--primary))] [paint-order:stroke_fill] dark:[-webkit-text-stroke:0]">
        OBE
      </span>
      <span className="text-primary">volve</span>
    </span>
  )
}

/** Compact monogram for tight spaces (collapsed sidebar, badge-sized
 * contexts) where the full wordmark won't fit — the source logo has no
 * separate icon glyph, so this derives one echoing the wordmark's own
 * "OBE" / "volve" split rather than an arbitrary single letter: "O" from
 * the white-stroked half, "v" from the solid-amber half. Size via `size-*`
 * (it's a square badge, not a font-size context like `Logo`). */
export function LogoMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-md bg-primary font-display text-sm font-extrabold leading-none tracking-tighter text-primary-foreground',
        className,
      )}
      aria-hidden="true"
    >
      O<span className="italic">v</span>
    </span>
  )
}

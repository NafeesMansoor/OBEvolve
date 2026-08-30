import { cn } from '@/lib/utils'

/**
 * OBEvolve's wordmark (ref/logo.png): "OBE" set in white with a red
 * keyline, "volve" solid red — reproduced as real text (not the source
 * raster, which is only 145×52px and blurs past favicon size) so it stays
 * crisp at any size and respects dark/light theme automatically via the
 * `--primary` token. `-webkit-text-stroke` on "OBE" is what makes it read
 * on any background, light or dark, exactly like the red keyline in the
 * source mark — `paint-order: stroke fill` keeps the stroke from eating
 * into the white fill. Size via font-size utilities on `className` (e.g.
 * `text-lg`, `text-3xl`), not `size-*`.
 */
export function Logo({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-baseline font-display font-extrabold leading-none tracking-tight',
        className,
      )}
    >
      <span
        className="text-white"
        style={{ WebkitTextStroke: '0.16em hsl(var(--primary))', paintOrder: 'stroke fill' }}
      >
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
 * the white-stroked half, "v" from the solid-red half. Size via `size-*`
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

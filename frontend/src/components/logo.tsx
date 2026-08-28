/**
 * OBEvolve's mark: an ascending, connected node graph — reads as both a
 * knowledge/outcome network (PEO → PO → CO mapping is literally this shape
 * elsewhere in the app) and an upward trajectory ("evolve"). Renders in
 * `currentColor` so it inherits whatever text color its container sets
 * (e.g. `text-primary-foreground` on the usual `bg-primary` badge).
 */
export function Logo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M4.5 17.5L9.5 12.5L13.5 15.5L19.5 6.5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M13.5 15.5L16 18"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.55"
      />
      <circle cx="4.5" cy="17.5" r="1.6" fill="currentColor" />
      <circle cx="9.5" cy="12.5" r="1.6" fill="currentColor" />
      <circle cx="13.5" cy="15.5" r="1.6" fill="currentColor" />
      <circle cx="16" cy="18" r="1.3" fill="currentColor" opacity="0.55" />
      <circle cx="19.5" cy="6.5" r="1.8" fill="currentColor" />
    </svg>
  )
}

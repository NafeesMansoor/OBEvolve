/** Renders newline-separated text as a bullet list — shared between
 * OverviewTab and CourseSettingsTab for objectives/TLA/materials/weights,
 * all of which store one line per item in a single text column. */
export function BulletList({ text, empty }: { text: string | null | undefined; empty: string }) {
  const lines = (text ?? '').split('\n').map((l) => l.trim()).filter(Boolean)
  if (lines.length === 0) return <p className="text-sm text-muted-foreground">{empty}</p>
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm">
      {lines.map((line, i) => (
        <li key={i}>{line}</li>
      ))}
    </ul>
  )
}

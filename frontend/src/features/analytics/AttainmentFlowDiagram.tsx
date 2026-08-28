export type AttainmentStage = 'marks' | 'course' | 'program' | 'rollup'

const STAGES: { key: AttainmentStage; label: string; sub: string }[] = [
  { key: 'marks', label: 'Marks Entry', sub: 'per question' },
  { key: 'course', label: 'Course Outcomes', sub: '(CO)' },
  { key: 'program', label: 'Program Outcomes', sub: '(PO)' },
  { key: 'rollup', label: 'Program Analytics', sub: 'across offerings' },
]

const ARROW_LABELS = [
  'weighted by question→CO map',
  'rolled up via CO→PO matrix',
  'aggregated across sections',
]

const BOX_W = 170
const BOX_H = 56
const GAP = 60
const BOX_Y = 54
const CENTER_Y = BOX_Y + BOX_H / 2
const MARGIN = 20
const LABEL_Y = 20

function boxX(i: number) {
  return MARGIN + i * (BOX_W + GAP)
}

const VIEW_W = MARGIN * 2 + STAGES.length * BOX_W + (STAGES.length - 1) * GAP
const VIEW_H = 122

/**
 * Shows the actual mechanism behind the numbers on the three Analytics tabs
 * — a question's marks don't become a "PO attainment %" by magic, they pass
 * through two explicit weighted roll-ups (question→CO map, then the CO→PO
 * mapping matrix) before Program Analytics aggregates across offerings.
 * `activeStage` highlights whichever tab is currently open so the diagram
 * stays anchored to what the viewer is looking at.
 */
export function AttainmentFlowDiagram({ activeStage }: { activeStage: AttainmentStage }) {
  return (
    <figure className="mb-2">
      <div className="overflow-x-auto rounded-lg border bg-card p-4 text-foreground">
        <svg
          viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
          role="img"
          aria-label="Attainment flow: Marks Entry weighted by the question-to-CO map becomes Course Outcome attainment, rolled up via the CO-to-PO mapping matrix into Program Outcome attainment, then aggregated across offerings into Program Analytics."
          className="mx-auto h-auto w-full max-w-3xl"
        >
          <defs>
            <marker
              id="attainment-flow-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M0,0 L10,5 L0,10 z" fill="currentColor" />
            </marker>
          </defs>

          {STAGES.map((stage, i) => {
            const isActive = stage.key === activeStage
            const x = boxX(i)
            return (
              <g key={stage.key} className={isActive ? 'text-primary' : 'text-muted-foreground'}>
                <rect
                  x={x}
                  y={BOX_Y}
                  width={BOX_W}
                  height={BOX_H}
                  rx={8}
                  fill={isActive ? 'currentColor' : 'none'}
                  fillOpacity={isActive ? 0.12 : 1}
                  stroke="currentColor"
                  strokeWidth={isActive ? 2 : 1.25}
                />
                <text
                  x={x + BOX_W / 2}
                  y={CENTER_Y - 4}
                  textAnchor="middle"
                  className={isActive ? 'fill-primary' : 'fill-foreground'}
                  fontSize={13}
                  fontWeight={600}
                >
                  {stage.label}
                </text>
                <text
                  x={x + BOX_W / 2}
                  y={CENTER_Y + 14}
                  textAnchor="middle"
                  fill="currentColor"
                  fontSize={11}
                >
                  {stage.sub}
                </text>
              </g>
            )
          })}

          {ARROW_LABELS.map((label, i) => {
            const x1 = boxX(i) + BOX_W
            const x2 = boxX(i + 1)
            const midX = (x1 + x2) / 2
            return (
              <g key={label} className="text-muted-foreground">
                <line
                  x1={x1 + 4}
                  y1={CENTER_Y}
                  x2={x2 - 6}
                  y2={CENTER_Y}
                  stroke="currentColor"
                  strokeWidth={1.5}
                  markerEnd="url(#attainment-flow-arrow)"
                />
                <text
                  x={midX}
                  y={LABEL_Y}
                  textAnchor="middle"
                  fill="currentColor"
                  fontSize={10}
                >
                  {label}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
      <figcaption className="mt-2 text-center text-xs text-muted-foreground">
        How a mark becomes an outcome-attainment percentage: two weighted roll-ups (question→CO,
        then CO→PO) stand between raw marks and the number shown on each tab below.
      </figcaption>
    </figure>
  )
}

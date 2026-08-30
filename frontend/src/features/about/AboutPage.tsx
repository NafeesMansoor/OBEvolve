import { Code2, ExternalLink, Globe } from 'lucide-react'

import { APP_VERSION } from '@/lib/version'
import { Logo } from '@/components/logo'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PageHeader } from '@/components/page-header'
import { Separator } from '@/components/ui/separator'

const CAPABILITIES = [
  {
    title: 'PEO → PO → CO outcome chain',
    body: 'Program Educational Objectives, Program Outcomes, and Course Outcomes are modeled as a real hierarchy with weighted mappings between every level, not flat text fields.',
  },
  {
    title: 'Accreditation framework catalogue',
    body: "A framework's Program Outcomes, Knowledge Profiles (WK), Problem Attributes (WP), and Engineering Activities (EA) are seeded verbatim from the accrediting body's own manual (e.g. BAETE v3.0) and referenced, not re-typed, by every program that adopts it.",
  },
  {
    title: 'Attainment calculation',
    body: 'Course-level CO attainment rolls up into program-level PO attainment automatically from entered marks, mapping weights, and configurable thresholds — recalculated on demand, not run as a batch job.',
  },
  {
    title: 'Multi-tenant, schema-isolated',
    body: 'Every institution gets its own PostgreSQL schema; every program within it gets a further isolated schema for curricula, offerings, and assessment data — physical separation, not row-level filtering.',
  },
  {
    title: 'Full academic operations',
    body: 'Course offerings, sections, faculty assignments, and student enrollments for every term, with import-from-previous-term shortcuts and CO-failure→improvement-plan workflows.',
  },
  {
    title: 'Scoped RBAC',
    body: 'Roles carry permissions that can be scoped to a specific program or left institution-wide, enforced server-side on every endpoint — the UI reflects exactly what a role can see and do.',
  },
]

const VERSION_HISTORY = [
  {
    version: `${APP_VERSION}`,
    tag: 'Current',
    notes:
      'Faculty Course Settings restored with real course-outline content (description, objectives, Course Outcomes with delivery methods/assessment tools, CO-PO mapping, TLA, materials, weights, grading policy) and a Coordinator approve/reject action on change requests; CEP guidance (Problem Attributes) surfaced in task authoring; a cross-course faculty Analytics view (grade distribution, CO/PO attainment, filterable); BR-01 previous-semester read-only now enforced server-side; the OBEvolve icon mark refined to "Ov".',
  },
  {
    version: '1.0.2',
    tag: 'Prior',
    notes:
      'Faculty Module: per-course-section workspace (Overview, Course Settings + change requests, Course Files, Students, Assessments with CEP/OEP task authoring, Marks Entry, Grades with submit-and-lock + CO attainment snapshot, Analytics); a Question Bank page; "my sections only" scoping for faculty across assessments/marks/enrollments; the OBEvolve brand logo and refreshed red theme.',
  },
  {
    version: '1.0.1',
    tag: 'Prior',
    notes:
      'Product versioning introduced. Program/Course Level Settings split out of the former combined Curriculum & Outcomes page; a dedicated Analytics section; the raw-data console; forgot/reset-password flow; scoped RBAC fixes across every program-scoped endpoint.',
  },
  {
    version: '0.x',
    tag: 'Foundation',
    notes:
      'Multi-tenant schema-per-institution/program architecture; the full OBE outcome hierarchy (PEOs/POs/COs) and mapping matrices; BAETE v3.0 + ULAB CSE seed data; academic operations, grading, and assessment modules; the platform-admin console.',
  },
]

function ExternalLinkRow({
  href,
  icon: Icon,
  label,
}: {
  href: string
  icon: typeof ExternalLink
  label: string
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
    >
      <Icon className="size-4" />
      {label}
      <ExternalLink className="size-3 opacity-60" />
    </a>
  )
}

export function AboutPage() {
  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-8">
      <div className="overflow-hidden rounded-xl border bg-card shadow-sm">
        <div className="h-1.5 bg-brand-gradient" />
        <div className="flex justify-center py-8">
          <Logo className="text-6xl" />
        </div>
      </div>

      <PageHeader
        title="About OBEvolve"
        description="A production-grade, multi-tenant Outcome-Based Education and accreditation platform."
      />

      <Card>
        <CardHeader>
          <CardTitle>What OBEvolve is</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm leading-relaxed text-muted-foreground">
          <p>
            OBEvolve is not a gradebook and not a generic LMS plugin. It is purpose-built
            infrastructure for running Outcome-Based Education end to end: defining an
            accreditation framework's outcomes, mapping a program's curriculum onto them,
            running academic operations and assessment against that curriculum, and
            calculating outcome attainment from the real marks entered along the way —
            for every institution and every program it serves, each fully isolated from the
            others.
          </p>
          <p>
            It answers the questions an accreditation self-study actually asks: which course
            outcomes map to which program outcomes, and with what weight; whether last
            term's cohort attained each program outcome above threshold; what corrective
            action was opened the last time a course outcome fell short; and who taught,
            enrolled in, or was assessed against a given offering — with a full audit trail
            behind every answer.
          </p>
        </CardContent>
      </Card>

      <div className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold tracking-tight">Core capabilities</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {CAPABILITIES.map((c) => (
            <Card key={c.title}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">{c.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-sm leading-relaxed">{c.body}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Version history</CardTitle>
          <CardDescription>OBEvolve follows semantic versioning once tagged releases begin.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {VERSION_HISTORY.map((v, i) => (
            <div key={v.version}>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-semibold">v{v.version}</span>
                <Badge variant={i === 0 ? 'secondary' : 'outline'} className="font-normal">
                  {v.tag}
                </Badge>
              </div>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{v.notes}</p>
              {i < VERSION_HISTORY.length - 1 && <Separator className="mt-4" />}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Author</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <div>
            <p className="text-sm font-medium">Prof. Nafees Mansoor</p>
            <p className="text-sm text-muted-foreground">
              University of Liberal Arts Bangladesh (ULAB), Department of Computer Science &
              Engineering
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <ExternalLinkRow href="https://www.nafees.info" icon={Globe} label="nafees.info" />
            <ExternalLinkRow
              href="https://github.com/NafeesMansoor"
              icon={Code2}
              label="github.com/NafeesMansoor"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

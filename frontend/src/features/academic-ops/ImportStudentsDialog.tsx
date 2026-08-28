import * as React from 'react'
import { Download, Upload } from 'lucide-react'

import { ApiError } from '@/lib/api-client'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'

interface SelectOption {
  label: string
  value: string
}

interface ParsedRow {
  full_name: string
  email: string
  student_code: string
  batch_year: number | null
  rowErrors: string[]
}

interface ImportResult {
  email: string
  ok: boolean
  detail: string
}

const EXPECTED_HEADERS = ['full_name', 'email', 'student_code', 'batch_year']
const SAMPLE_CSV =
  'full_name,email,student_code,batch_year\nJane Doe,jane.doe@example.edu,CSE-24-001,2024\nJohn Smith,john.smith@example.edu,CSE-24-002,2024'

/** Minimal CSV split — handles simple quoted fields ("a, b") but not
 * embedded newlines inside a quoted cell; the header/row shape this dialog
 * expects (four short scalar columns) never needs that. */
function parseCsvLine(line: string): string[] {
  const cells: string[] = []
  let current = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      cells.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  cells.push(current.trim())
  return cells
}

function parseCsv(text: string): { rows: ParsedRow[]; headerError: string | null } {
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0)
  if (lines.length === 0) return { rows: [], headerError: null }

  const header = parseCsvLine(lines[0]).map((h) => h.toLowerCase())
  const missing = EXPECTED_HEADERS.filter((h) => h !== 'batch_year' && !header.includes(h))
  if (missing.length > 0) {
    return { rows: [], headerError: `Missing required column(s): ${missing.join(', ')}` }
  }

  const idx = {
    full_name: header.indexOf('full_name'),
    email: header.indexOf('email'),
    student_code: header.indexOf('student_code'),
    batch_year: header.indexOf('batch_year'),
  }

  const rows: ParsedRow[] = lines.slice(1).map((line) => {
    const cells = parseCsvLine(line)
    const full_name = cells[idx.full_name]?.trim() ?? ''
    const email = cells[idx.email]?.trim() ?? ''
    const student_code = cells[idx.student_code]?.trim() ?? ''
    const rawBatchYear = idx.batch_year >= 0 ? cells[idx.batch_year]?.trim() : ''
    const batch_year = rawBatchYear ? Number.parseInt(rawBatchYear, 10) : null

    const rowErrors: string[] = []
    if (!full_name) rowErrors.push('missing name')
    if (!email || !email.includes('@')) rowErrors.push('invalid email')
    if (!student_code) rowErrors.push('missing student code')
    if (rawBatchYear && Number.isNaN(batch_year)) rowErrors.push('invalid batch year')

    return { full_name, email, student_code, batch_year, rowErrors }
  })

  return { rows, headerError: null }
}

function generatePassword(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789'
  const bytes = new Uint32Array(12)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, (b) => chars[b % chars.length]).join('')
}

/**
 * Bulk-create students from a pasted/uploaded CSV — the one-at-a-time "Add
 * student" dialog doesn't scale to onboarding a whole batch/cohort at
 * once. Program + program version are picked once here and applied to
 * every row (matches the product rule that students are only addable at
 * the program level, not per-course); each row gets its own randomly
 * generated temporary password, shown in the results table afterward since
 * the backend only ever stores its hash — this is the one and only time an
 * admin can see it, so the results table is copyable, not just a toast.
 */
export function ImportStudentsDialog({
  open,
  onOpenChange,
  programOptions,
  programVersionOptions,
  onImportRow,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  programOptions: SelectOption[]
  programVersionOptions: SelectOption[]
  onImportRow: (row: {
    full_name: string
    email: string
    password: string
    student_code: string
    program_id: string | null
    program_version_id: string | null
    batch_year: number | null
  }) => Promise<void>
}) {
  const [csvText, setCsvText] = useResetOnChange(open, '')
  const [programId, setProgramId] = React.useState('')
  const [programVersionId, setProgramVersionId] = React.useState('')
  const [isImporting, setIsImporting] = useResetOnChange(open, false)
  const [results, setResults] = useResetOnChange<ImportResult[] | null>(open, null)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const { rows, headerError } = React.useMemo(() => parseCsv(csvText), [csvText])
  const validRows = rows.filter((r) => r.rowErrors.length === 0)
  const invalidRows = rows.filter((r) => r.rowErrors.length > 0)

  function handleFile(file: File) {
    const reader = new FileReader()
    reader.onload = () => setCsvText(String(reader.result ?? ''))
    reader.readAsText(file)
  }

  async function handleImport() {
    setIsImporting(true)
    const outcomes: ImportResult[] = []
    for (const row of validRows) {
      const password = generatePassword()
      try {
        await onImportRow({
          full_name: row.full_name,
          email: row.email,
          password,
          student_code: row.student_code,
          program_id: programId || null,
          program_version_id: programVersionId || null,
          batch_year: row.batch_year,
        })
        outcomes.push({ email: row.email, ok: true, detail: password })
      } catch (err) {
        outcomes.push({
          email: row.email,
          ok: false,
          detail: err instanceof ApiError ? err.detail : 'Failed to create',
        })
      }
    }
    setResults(outcomes)
    setIsImporting(false)
  }

  const succeeded = results?.filter((r) => r.ok).length ?? 0
  const failed = results?.filter((r) => !r.ok).length ?? 0

  function copyResults() {
    if (!results) return
    const text = results
      .map((r) => (r.ok ? `${r.email}\t${r.detail}` : `${r.email}\tFAILED: ${r.detail}`))
      .join('\n')
    void navigator.clipboard.writeText(text)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Import students</DialogTitle>
          <DialogDescription>
            Paste or upload a CSV with columns: full_name, email, student_code, batch_year
            (optional). Every row is created under the same program/version chosen below.
          </DialogDescription>
        </DialogHeader>

        {results ? (
          <div className="space-y-3">
            <p className="text-sm">
              Created <span className="font-medium">{succeeded}</span> student
              {succeeded === 1 ? '' : 's'}
              {failed > 0 ? (
                <>
                  {' '}
                  · <span className="font-medium text-destructive">{failed} failed</span>
                </>
              ) : null}
              .
            </p>
            {succeeded > 0 ? (
              <p className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                Temporary passwords are shown once, below — they can't be retrieved again. Share
                them with each student, or have them use "Forgot password" to set their own.
              </p>
            ) : null}
            <div className="max-h-64 overflow-y-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Result</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.map((r) => (
                    <TableRow key={r.email}>
                      <TableCell className="font-mono text-xs">{r.email}</TableCell>
                      <TableCell
                        className={
                          r.ok ? 'font-mono text-xs' : 'text-xs text-destructive'
                        }
                      >
                        {r.ok ? r.detail : r.detail}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={copyResults}>
                Copy results
              </Button>
              <Button onClick={() => onOpenChange(false)}>Done</Button>
            </DialogFooter>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Program</Label>
                <Select value={programId} onValueChange={setProgramId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a program" />
                  </SelectTrigger>
                  <SelectContent>
                    {programOptions.map((o) => (
                      <SelectItem key={o.value} value={o.value}>
                        {o.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Program version</Label>
                <Select value={programVersionId} onValueChange={setProgramVersionId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a version" />
                  </SelectTrigger>
                  <SelectContent>
                    {programVersionOptions.map((o) => (
                      <SelectItem key={o.value} value={o.value}>
                        {o.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label>CSV data</Label>
                <div className="flex gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,text/csv"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) handleFile(file)
                      e.target.value = ''
                    }}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="size-3.5" /> Upload CSV
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setCsvText(SAMPLE_CSV)}
                  >
                    <Download className="size-3.5" /> Use sample
                  </Button>
                </div>
              </div>
              <Textarea
                value={csvText}
                onChange={(e) => setCsvText(e.target.value)}
                placeholder={SAMPLE_CSV}
                className="h-40 font-mono text-xs"
              />
            </div>

            {headerError ? (
              <p className="text-sm text-destructive">{headerError}</p>
            ) : rows.length > 0 ? (
              <p className="text-sm text-muted-foreground">
                {validRows.length} row{validRows.length === 1 ? '' : 's'} ready to import
                {invalidRows.length > 0
                  ? `, ${invalidRows.length} skipped (${invalidRows
                      .flatMap((r) => r.rowErrors)
                      .join(', ')})`
                  : ''}
                .
              </p>
            ) : null}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button
                disabled={
                  validRows.length === 0 || !programId || !programVersionId || isImporting
                }
                onClick={handleImport}
              >
                {isImporting
                  ? 'Importing…'
                  : `Import ${validRows.length || ''} student${validRows.length === 1 ? '' : 's'}`}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

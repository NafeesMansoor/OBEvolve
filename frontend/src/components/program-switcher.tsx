import { Check, GraduationCap } from 'lucide-react'

import { useActiveProgram } from '@/lib/active-program-context'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

/**
 * Picks which program's schema program-scoped requests target (see
 * lib/active-program-context.tsx and docs/adr/0003-schema-per-program.md) —
 * NOT presentational like RoleSwitcher: Program Versions, PEOs/POs, CO-PO
 * mappings, course offerings/sections/faculty/enrollments, and assessments
 * all 400 without one selected. Hidden when there's 0 or 1 program, since
 * there's nothing to choose (1 program auto-selects itself).
 */
export function ProgramSwitcher() {
  const { programs, activeProgramCode, setActiveProgram } = useActiveProgram()

  if (programs.length < 2) return null

  const current = programs.find((p) => p.code === activeProgramCode)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5">
          <GraduationCap className="size-4" />
          {current?.code ?? 'Select program'}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel>Active program</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {programs.map((program) => (
          <DropdownMenuItem
            key={program.id}
            onClick={() => setActiveProgram(program.code)}
            className="flex items-center justify-between"
          >
            <span className="truncate">
              {program.name} ({program.code})
            </span>
            {activeProgramCode === program.code && <Check className="size-4 shrink-0" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

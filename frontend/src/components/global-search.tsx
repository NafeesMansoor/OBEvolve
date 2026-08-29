import * as React from 'react'
import {
  BookOpen,
  ClipboardCheck,
  GraduationCap,
  Search,
  Target,
  UserCircle,
  Users,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { useGlobalSearch } from '@/features/search/api'
import { SEARCH_TYPE_LABELS, type SearchResult, type SearchResultType } from '@/features/search/types'
import { Button } from '@/components/ui/button'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'

const TYPE_ICONS: Record<SearchResultType, React.ComponentType<{ className?: string }>> = {
  course: BookOpen,
  student: GraduationCap,
  faculty: UserCircle,
  assessment: ClipboardCheck,
  program_outcome: Target,
  course_outcome: Target,
  program: Users,
}

const DEBOUNCE_MS = 250

function useDebouncedValue(value: string, delayMs: number): string {
  const [debounced, setDebounced] = React.useState(value)
  React.useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(timer)
  }, [value, delayMs])
  return debounced
}

function groupResults(results: SearchResult[]): [SearchResultType, SearchResult[]][] {
  const groups = new Map<SearchResultType, SearchResult[]>()
  for (const result of results) {
    const bucket = groups.get(result.type) ?? []
    bucket.push(result)
    groups.set(result.type, bucket)
  }
  return Array.from(groups.entries())
}

export function GlobalSearch() {
  const [open, setOpen] = React.useState(false)
  const [query, setQuery] = React.useState('')
  const debouncedQuery = useDebouncedValue(query, DEBOUNCE_MS)
  const navigate = useNavigate()

  const search = useGlobalSearch(debouncedQuery, open)

  function handleOpenChange(next: boolean) {
    setOpen(next)
    if (!next) setQuery('')
  }

  React.useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'k' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault()
        handleOpenChange(!open)
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open])

  function goTo(result: SearchResult) {
    setOpen(false)
    navigate(result.url_hint)
  }

  const results = search.data?.results ?? []
  const showEmpty = debouncedQuery.trim().length >= 2 && !search.isFetching && results.length === 0

  return (
    <>
      <Button
        variant="outline"
        size="icon"
        className="shrink-0 text-muted-foreground sm:hidden"
        aria-label="Search"
        onClick={() => setOpen(true)}
      >
        <Search className="size-4" />
      </Button>
      <Button
        variant="outline"
        className="hidden w-64 justify-start gap-2 text-muted-foreground sm:flex"
        onClick={() => setOpen(true)}
      >
        <Search className="size-4" />
        <span className="flex-1 text-left">Search…</span>
        <kbd className="rounded border bg-muted px-1.5 py-0.5 text-[10px] font-medium">⌘K</kbd>
      </Button>

      <CommandDialog open={open} onOpenChange={handleOpenChange}>
        <CommandInput
          placeholder="Search courses, students, faculty, assessments, outcomes…"
          value={query}
          onValueChange={setQuery}
        />
        <CommandList>
          {query.trim().length > 0 && query.trim().length < 2 && (
            <p className="px-4 py-6 text-center text-sm text-muted-foreground">
              Keep typing — at least 2 characters.
            </p>
          )}
          {showEmpty && <CommandEmpty>No results for "{debouncedQuery.trim()}".</CommandEmpty>}
          {groupResults(results).map(([type, items]) => (
            <CommandGroup key={type} heading={SEARCH_TYPE_LABELS[type]}>
              {items.map((item) => {
                const Icon = TYPE_ICONS[item.type]
                return (
                  <CommandItem
                    key={`${item.type}-${item.id}`}
                    value={`${item.type}-${item.id}-${item.title}`}
                    onSelect={() => goTo(item)}
                  >
                    <Icon className="size-4 text-muted-foreground" />
                    <div className="flex min-w-0 flex-1 flex-col">
                      <span className="truncate">{item.title}</span>
                      {item.subtitle && (
                        <span className="truncate text-xs text-muted-foreground">
                          {item.subtitle}
                        </span>
                      )}
                    </div>
                  </CommandItem>
                )
              })}
            </CommandGroup>
          ))}
        </CommandList>
      </CommandDialog>
    </>
  )
}

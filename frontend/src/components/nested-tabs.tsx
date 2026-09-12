import * as React from 'react'

import { cn } from '@/lib/utils'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export interface NestedTabItem {
  value: string
  label: string
  content: React.ReactNode
  show?: boolean
}

/** A second tier of tabs living inside an already-tabbed page (e.g. the
 * Programs tab hosting a Sessions panel, or a program's own
 * curriculum/outcomes/course-settings pages nested under it). Deliberately
 * styled as an underline strip rather than the outer level's boxed/pill
 * `TabsList` — one visual step quieter, so depth reads at a glance instead
 * of two equal-weight tab bars competing for attention. Every "tabbed page"
 * in this codebase hand-rolls its own {value,label,show,content}[] array;
 * this is that same shape, reused for the nested tier so it doesn't have to
 * be hand-rolled again at each nesting site. */
export function NestedTabs({
  items,
  defaultValue,
  className,
}: {
  items: NestedTabItem[]
  defaultValue?: string
  className?: string
}) {
  const visible = items.filter((t) => t.show !== false)
  if (visible.length === 0) return null

  return (
    <Tabs defaultValue={defaultValue ?? visible[0]?.value} className={className}>
      <TabsList className="h-auto w-full justify-start gap-4 rounded-none border-b bg-transparent p-0">
        {visible.map((t) => (
          <TabsTrigger
            key={t.value}
            value={t.value}
            className={cn(
              'rounded-none border-b-2 border-transparent px-0.5 pb-2 pt-0 text-sm font-medium text-muted-foreground shadow-none',
              'data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-foreground data-[state=active]:shadow-none',
            )}
          >
            {t.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {visible.map((t) => (
        <TabsContent key={t.value} value={t.value} className="mt-4">
          {t.content}
        </TabsContent>
      ))}
    </Tabs>
  )
}

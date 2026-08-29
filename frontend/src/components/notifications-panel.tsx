import * as React from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Bell, CheckCheck, ClipboardList, FileStack, Lightbulb } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useNotifications,
  usePendingApprovals,
  useUnreadCount,
} from '@/features/notifications/api'
import { PENDING_APPROVAL_ROUTES, type PendingApprovalType } from '@/features/notifications/types'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Separator } from '@/components/ui/separator'

const PENDING_ICONS: Record<PendingApprovalType, React.ComponentType<{ className?: string }>> = {
  assessment_document: FileStack,
  raw_data_change: ClipboardList,
  improvement_plan: Lightbulb,
}

export function NotificationsPanel() {
  const [open, setOpen] = React.useState(false)
  const navigate = useNavigate()

  const notifications = useNotifications(open)
  const pendingApprovals = usePendingApprovals(true)
  const unreadCountQuery = useUnreadCount(true)
  const markRead = useMarkNotificationRead()
  const markAllRead = useMarkAllNotificationsRead()

  const unreadCount = open
    ? (notifications.data ?? []).filter((n) => !n.is_read).length
    : (unreadCountQuery.data ?? 0)
  const pendingTotal = pendingApprovals.data?.total ?? 0
  const badgeCount = unreadCount + pendingTotal

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
          <Bell className="size-5" />
          {badgeCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex size-4 items-center justify-center rounded-full bg-destructive text-[10px] font-semibold text-destructive-foreground">
              {badgeCount > 9 ? '9+' : badgeCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-96 p-0">
        {pendingTotal > 0 && (
          <>
            <div className="flex items-center justify-between px-4 pt-3">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Pending your review
              </p>
              <Badge variant="secondary">{pendingTotal}</Badge>
            </div>
            <div className="flex flex-col gap-0.5 p-2">
              {(pendingApprovals.data?.items ?? []).map((item) => {
                const Icon = PENDING_ICONS[item.type]
                return (
                  <button
                    key={item.type}
                    type="button"
                    onClick={() => {
                      setOpen(false)
                      navigate(PENDING_APPROVAL_ROUTES[item.type])
                    }}
                    className="flex items-center gap-3 rounded-md px-2 py-2 text-left text-sm hover:bg-accent"
                  >
                    <Icon className="size-4 shrink-0 text-muted-foreground" />
                    <span className="flex-1">{item.label}</span>
                    <Badge variant="outline">{item.count}</Badge>
                  </button>
                )
              })}
            </div>
            <Separator />
          </>
        )}

        <div className="flex items-center justify-between px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Notifications
          </p>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto gap-1 px-2 py-1 text-xs"
              onClick={() => markAllRead.mutate()}
              disabled={markAllRead.isPending}
            >
              <CheckCheck className="size-3.5" />
              Mark all read
            </Button>
          )}
        </div>

        <div className="max-h-80 overflow-y-auto">
          {(notifications.data ?? []).length === 0 && pendingTotal === 0 ? (
            <p className="px-4 pb-4 text-sm text-muted-foreground">
              You're all caught up — nothing needs your attention.
            </p>
          ) : (notifications.data ?? []).length === 0 ? (
            <p className="px-4 pb-4 text-sm text-muted-foreground">No notifications yet.</p>
          ) : (
            <ul className="flex flex-col">
              {(notifications.data ?? []).map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    onClick={() => !n.is_read && markRead.mutate(n.id)}
                    className={cn(
                      'flex w-full flex-col gap-0.5 border-t px-4 py-2.5 text-left text-sm hover:bg-accent',
                      !n.is_read && 'bg-primary/5',
                    )}
                  >
                    <span className="flex items-center gap-2 font-medium">
                      {!n.is_read && <span className="size-1.5 shrink-0 rounded-full bg-primary" />}
                      {n.title}
                    </span>
                    {n.body && <span className="text-muted-foreground">{n.body}</span>}
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}

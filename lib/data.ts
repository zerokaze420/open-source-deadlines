import { TZDate } from "@date-fns/tz"

export interface TimelineEvent {
  deadline: string
  comment: string
}

export interface EventData {
  year: number
  id: string
  link: string
  timeline: TimelineEvent[]
  timezone: string
  date: string
  place: string
}

export interface DeadlineItem {
  title: string
  description: string
  category: 'conference' | 'competition'
  tags: string[]
  events: EventData[]
}

export function getTimelineStatus(deadline: TZDate): 'past' | 'current' | 'upcoming' {
  const now = new TZDate(new Date(), "Asia/Shanghai")
  const timeDiff = deadline.getTime() - now.getTime()
  const daysDiff = timeDiff / (1000 * 3600 * 24)
  
  if (daysDiff < -1) return 'past'
  if (daysDiff >= -1 && daysDiff <= 1) return 'current'
  return 'upcoming'
}

export function isEventEnded(event: EventData): boolean {
  const now = new TZDate(new Date(), "Asia/Shanghai")
  const lastDeadline = new TZDate(event.timeline[event.timeline.length - 1].deadline, event.timezone)
  return lastDeadline.withTimeZone("Asia/Shanghai") < now
}
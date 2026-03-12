import { format, formatDistanceToNow, isToday, isTomorrow, isYesterday } from 'date-fns'
import { fr } from 'date-fns/locale'

export function fmtDate(str) {
  if (!str) return '—'
  const d = new Date(str)
  return format(d, 'EEE dd MMM · HH:mm', { locale: fr })
}

export function fmtDateFull(str) {
  if (!str) return '—'
  const d = new Date(str)
  return format(d, 'EEEE dd MMMM yyyy · HH:mm', { locale: fr })
}

export function fmtDateShort(str) {
  if (!str) return '—'
  const d = new Date(str)
  if (isToday(d))     return `Aujourd'hui · ${format(d, 'HH:mm')}`
  if (isTomorrow(d))  return `Demain · ${format(d, 'HH:mm')}`
  if (isYesterday(d)) return `Hier · ${format(d, 'HH:mm')}`
  return format(d, 'EEE dd MMM · HH:mm', { locale: fr })
}

export function fmtRelative(str) {
  if (!str) return '—'
  return formatDistanceToNow(new Date(str), { addSuffix: true, locale: fr })
}

export const STATUS_META = {
  SCHEDULED: { label: 'PROG.',   color: '#ffcc00', bg: 'rgba(255,204,0,0.1)'   },
  TIMED:     { label: 'PROG.',   color: '#ffcc00', bg: 'rgba(255,204,0,0.1)'   },
  IN_PLAY:   { label: 'LIVE',    color: '#00ff88', bg: 'rgba(0,255,136,0.1)'   },
  FINISHED:  { label: 'TERM.',   color: '#44456a', bg: 'rgba(68,69,106,0.1)'   },
  POSTPONED: { label: 'REPOR.',  color: '#ff4455', bg: 'rgba(255,68,85,0.1)'   },
  CANCELLED: { label: 'ANNUL.',  color: '#ff4455', bg: 'rgba(255,68,85,0.1)'   },
  HALFTIME:  { label: 'MI-TEMPS',color: '#00ccff', bg: 'rgba(0,204,255,0.1)'   },
}

export const RESULT_COLOR = { W: '#00ff88', D: '#ffcc00', L: '#ff4455' }

export function probaColor(value) {
  if (value >= 0.65) return '#00ff88'
  if (value >= 0.45) return '#00ccff'
  if (value >= 0.30) return '#ffcc00'
  return '#ff5566'
}

export function probaColorHot(value) {
  if (value >= 0.52) return '#ffcc00'
  if (value >= 0.42) return '#ff6b35'
  return '#ff4455'
}

export const TOP_COMPETITIONS = ['PL', 'PD', 'BL1', 'SA', 'FL1', 'CL', 'EL', 'UCL']

export function getDateRange(days = 7) {
  const now  = new Date()
  const from = now.toISOString().split('T')[0]
  const to   = new Date(now.setDate(now.getDate() + days)).toISOString().split('T')[0]
  return { date_from: from, date_to: to }
}

import { ApiError } from '../../api/client'

export type ClassType = {
  id: string
  tenant_id: string
  name: string
  description: string | null
  category: string
  duration_minutes: number
  default_capacity: number
  color_hex: string
  cancellation_cutoff_minutes: number
  is_active: boolean
}

export type ClassSchedule = {
  id: string
  tenant_id: string
  location_id: string
  class_type_id: string
  class_type_name?: string
  trainer_user_id: string
  trainer_name?: string
  day_of_week: number
  start_time: string
  end_time: string
  room_name: string | null
  capacity: number
  is_active: boolean
}

export type ClassSession = {
  id: string
  tenant_id: string
  location_id: string
  location_name?: string
  class_type_id: string
  class_type_name?: string
  class_category?: string
  color_hex?: string
  trainer_user_id: string
  trainer_name?: string
  start_time_utc: string
  end_time_utc: string
  room_name: string | null
  capacity: number
  confirmed_count: number
  waitlist_count: number
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
  user_booking_status?: 'CONFIRMED' | 'WAITLISTED' | 'ATTENDED' | 'NO_SHOW' | 'CANCELLED' | null
  user_waitlist_position?: number | null
}

export type ClassBooking = {
  id: string
  tenant_id: string
  session_id: string
  member_id: string
  status: 'CONFIRMED' | 'WAITLISTED' | 'ATTENDED' | 'NO_SHOW' | 'CANCELLED'
  waitlist_position: number | null
  booked_at: string
  attended_at: string | null
  cancelled_at: string | null
  is_late_cancellation: boolean
}

export type ClassAttendee = {
  booking_id: string
  member_id: string
  member_name: string
  member_email: string | null
  member_phone: string | null
  status: 'CONFIRMED' | 'WAITLISTED' | 'ATTENDED' | 'NO_SHOW' | 'CANCELLED'
  waitlist_position: number | null
}

export type ClassSessionRoster = {
  session: ClassSession
  attendees: ClassAttendee[]
  total_confirmed: number
  total_waitlisted: number
}

export type PtAppointment = {
  id: string
  tenant_id: string
  location_id: string
  trainer_user_id: string
  trainer_name?: string
  member_id: string
  member_name?: string
  start_time_utc: string
  end_time_utc: string
  status: 'CONFIRMED' | 'ATTENDED' | 'NO_SHOW' | 'CANCELLED'
  notes: string | null
  is_late_cancellation: boolean
}

export type LocationItem = {
  id: string
  name: string
}

export type StaffItem = {
  id: string
  user_id: string
  email?: string | null
  role: string
}

export type TrainerOption = {
  user_id: string
  email: string
  role: string
}

export function staffLabel(person: { email?: string | null; user_id: string; role: string }): string {
  const who = person.email?.trim() || person.user_id
  return `${who} (${person.role})`
}

export const DAYS_TR = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']

export function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'Bu işlem için yetkiniz yok.'
    if (e.body && typeof e.body === 'object' && 'detail' in (e.body as Record<string, unknown>)) {
      const detail = (e.body as Record<string, unknown>).detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail)) {
        return detail.map((d: Record<string, unknown>) => `${(d.loc as string[])?.join('.')}: ${d.msg}`).join(', ')
      }
    }
    return e.status === 400 || e.status === 404 || e.status === 409
      ? e.message
      : `${e.status}: ${e.message}`
  }
  if (e instanceof Error) return e.message
  return fallback
}

export function formatDateTr(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleDateString('tr-TR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatTime(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
}

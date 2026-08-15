import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, EmptyState, LoadingSkeleton, PageHeader, StatusBadge } from '../components/ui'

// ---------------------------------------------------------
// TypeScript Domain Interfaces
// ---------------------------------------------------------

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
  booked_at: string
  attended_at: string | null
  cancelled_at: string | null
  is_late_cancellation: boolean
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
  first_name: string
  last_name: string
  role: string
}

const DAYS_TR = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']

function formatApiError(e: unknown, fallback: string): string {
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

function formatDateTr(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleDateString('tr-TR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatTime(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
}

export default function Classes() {
  const { session } = useAuth()
  const [activeTab, setActiveTab] = useState<'sessions' | 'schedules' | 'types' | 'pt'>('sessions')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  // Data states
  const [sessions, setSessions] = useState<ClassSession[]>([])
  const [schedules, setSchedules] = useState<ClassSchedule[]>([])
  const [classTypes, setClassTypes] = useState<ClassType[]>([])
  const [ptAppointments, setPtAppointments] = useState<PtAppointment[]>([])
  const [locations, setLocations] = useState<LocationItem[]>([])
  const [staffList, setStaffList] = useState<StaffItem[]>([])

  // Roster Drawer State
  const [selectedSessionRoster, setSelectedSessionRoster] = useState<ClassSessionRoster | null>(null)
  const [rosterLoading, setRosterLoading] = useState(false)

  // Modals
  const [showTypeModal, setShowTypeModal] = useState(false)
  const [showSessionModal, setShowSessionModal] = useState(false)
  const [showGenerateModal, setShowGenerateModal] = useState(false)

  // Form states - Type
  const [typeName, setTypeName] = useState('')
  const [typeCategory, setTypeCategory] = useState('CARDIO')
  const [typeDuration, setTypeDuration] = useState(45)
  const [typeCapacity, setTypeCapacity] = useState(10)
  const [typeColor, setTypeColor] = useState('#10B981')
  const [typeCutoff, setTypeCutoff] = useState(120)

  // Form states - Session
  const [sessLocationId, setSessLocationId] = useState('')
  const [sessClassTypeId, setSessClassTypeId] = useState('')
  const [sessTrainerUserId, setSessTrainerUserId] = useState('')
  const [sessStart, setSessStart] = useState('')
  const [sessEnd, setSessEnd] = useState('')
  const [sessCapacity, setSessCapacity] = useState(10)
  const [sessRoom, setSessRoom] = useState('')

  // Form states - Generate
  const [genScheduleId, setGenScheduleId] = useState('')
  const [genStartDate, setGenStartDate] = useState('')
  const [genEndDate, setGenEndDate] = useState('')

  // Fetch all initial data
  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [typesRes, schedsRes, sessRes, ptRes, locsRes, staffRes] = await Promise.all([
        api<ClassType[]>('/api/v1/classes/types'),
        api<ClassSchedule[]>('/api/v1/classes/schedules'),
        api<ClassSession[]>('/api/v1/classes/sessions'),
        api<PtAppointment[]>('/api/v1/classes/pt/appointments'),
        api<LocationItem[]>('/api/v1/locations'),
        api<StaffItem[]>('/api/v1/staff').catch(() => [] as StaffItem[]),
      ])

      setClassTypes(typesRes)
      setSchedules(schedsRes)
      setSessions(sessRes)
      setPtAppointments(ptRes)
      setLocations(locsRes)
      setStaffList(staffRes)

      if (locsRes.length > 0) setSessLocationId(locsRes[0].id)
      if (typesRes.length > 0) setSessClassTypeId(typesRes[0].id)
      if (staffRes.length > 0) setSessTrainerUserId(staffRes[0].user_id)
      if (schedsRes.length > 0) setGenScheduleId(schedsRes[0].id)
    } catch (e) {
      setError(formatApiError(e, 'Ders verileri yüklenirken bir hata oluştu.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Open Roster Drawer
  async function openRoster(sessionId: string) {
    setRosterLoading(true)
    try {
      const res = await api<ClassSessionRoster>(`/api/v1/classes/sessions/${sessionId}/roster`)
      setSelectedSessionRoster(res)
    } catch (e) {
      setError(formatApiError(e, 'Yoklama listesi yüklenemedi.'))
    } finally {
      setRosterLoading(false)
    }
  }

  // Mark Attendance
  async function handleMarkAttendance(bookingId: string, statusVal: 'ATTENDED' | 'NO_SHOW') {
    try {
      await api(`/api/v1/classes/bookings/${bookingId}/attend`, {
        method: 'POST',
        body: { status: statusVal },
      })
      setMessage(`Yoklama kaydedildi: ${statusVal === 'ATTENDED' ? 'Katıldı (Geldi)' : 'Gelmedi (No-Show)'}`)
      if (selectedSessionRoster) {
        await openRoster(selectedSessionRoster.session.id)
      }
      loadData()
    } catch (e) {
      setError(formatApiError(e, 'Yoklama kaydedilemedi.'))
    }
  }

  // Admin Cancel Booking
  async function handleAdminCancelBooking(bookingId: string) {
    if (!confirm('Bu rezervasyonu iptal etmek istediğinize emin misiniz? Yedekte üye varsa otomatik asil listeye terfi ettirilecektir.')) return
    try {
      await api(`/api/v1/classes/bookings/${bookingId}/cancel`, {
        method: 'POST',
        body: { cancellation_reason: 'Yönetici tarafından iptal edildi' },
      })
      setMessage('Rezervasyon iptal edildi. Varsa sıradaki yedek üye asil listeye geçirildi.')
      if (selectedSessionRoster) {
        await openRoster(selectedSessionRoster.session.id)
      }
      loadData()
    } catch (e) {
      setError(formatApiError(e, 'Rezervasyon iptal edilemedi.'))
    }
  }

  // Submit Create Class Type
  async function handleCreateType(e: FormEvent) {
    e.preventDefault()
    try {
      await api<ClassType>('/api/v1/classes/types', {
        method: 'POST',
        body: {
          name: typeName,
          category: typeCategory,
          duration_minutes: typeDuration,
          default_capacity: typeCapacity,
          color_hex: typeColor,
          cancellation_cutoff_minutes: typeCutoff,
        },
      })
      setMessage('Yeni ders tipi başarıyla oluşturuldu.')
      setShowTypeModal(false)
      setTypeName('')
      loadData()
    } catch (err) {
      setError(formatApiError(err, 'Ders tipi oluşturulamadı.'))
    }
  }

  // Submit Create Session
  async function handleCreateSession(e: FormEvent) {
    e.preventDefault()
    const finalLocationId = sessLocationId || locations[0]?.id
    const finalClassTypeId = sessClassTypeId || classTypes[0]?.id
    const finalTrainerId = sessTrainerUserId || staffList[0]?.user_id || session?.user_id

    if (!finalLocationId || !finalClassTypeId || !finalTrainerId) {
      setError('Lütfen şube, ders tipi ve eğitmen seçimlerini tamamlayın.')
      return
    }

    try {
      await api<ClassSession>('/api/v1/classes/sessions', {
        method: 'POST',
        body: {
          location_id: finalLocationId,
          class_type_id: finalClassTypeId,
          trainer_user_id: finalTrainerId,
          start_time_utc: new Date(sessStart).toISOString(),
          end_time_utc: new Date(sessEnd).toISOString(),
          capacity: sessCapacity,
          room_name: sessRoom || null,
        },
      })
      setMessage('Ders seansı başarıyla takvime eklendi.')
      setShowSessionModal(false)
      loadData()
    } catch (err) {
      setError(formatApiError(err, 'Seans oluşturulamadı.'))
    }
  }

  // Submit Generate Recurring Sessions
  async function handleGenerateSessions(e: FormEvent) {
    e.preventDefault()
    try {
      await api(`/api/v1/classes/schedules/${genScheduleId}/generate-sessions`, {
        method: 'POST',
        body: {
          schedule_id: genScheduleId,
          start_date: new Date(genStartDate).toISOString(),
          end_date: new Date(genEndDate).toISOString(),
        },
      })
      setMessage('Haftalık programa ait seanslar başarıyla üretildi.')
      setShowGenerateModal(false)
      loadData()
    } catch (err) {
      setError(formatApiError(err, 'Seanslar üretilemedi.'))
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Grup Dersi & PT Takvimi"
        subtitle="Grup ders seansları, kapasite yönetimi, dinamik yedek sırası ve 1-on-1 PT randevuları."
        actions={
          <div className="flex gap-2">
            <button
              onClick={() => setShowSessionModal(true)}
              className="btn btn-primary text-sm px-4 py-2"
            >
              + Yeni Seans Ekle
            </button>
            <button
              onClick={() => setShowGenerateModal(true)}
              className="btn btn-secondary text-sm px-4 py-2"
            >
              ⚡ Toplu Seans Üret
            </button>
            <button
              onClick={() => setShowTypeModal(true)}
              className="btn btn-secondary text-sm px-4 py-2"
            >
              + Ders Tipi
            </button>
          </div>
        }
      />

      {error && <Alert variant="error">{error}</Alert>}
      {message && <Alert variant="success">{message}</Alert>}

      {/* Tabs */}
      <div className="flex border-b border-border/40 gap-4 text-sm font-medium">
        <button
          onClick={() => setActiveTab('sessions')}
          className={`pb-3 px-2 border-b-2 transition-colors ${
            activeTab === 'sessions'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          📅 Takvim & Seanslar ({sessions.length})
        </button>
        <button
          onClick={() => setActiveTab('schedules')}
          className={`pb-3 px-2 border-b-2 transition-colors ${
            activeTab === 'schedules'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          📋 Haftalık Şablon Programı ({schedules.length})
        </button>
        <button
          onClick={() => setActiveTab('types')}
          className={`pb-3 px-2 border-b-2 transition-colors ${
            activeTab === 'types'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          🏷️ Ders Kataloğu ({classTypes.length})
        </button>
        <button
          onClick={() => setActiveTab('pt')}
          className={`pb-3 px-2 border-b-2 transition-colors ${
            activeTab === 'pt'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          🏋️ Kişisel Antrenman (PT) ({ptAppointments.length})
        </button>
      </div>

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <>
          {/* TAB 1: SESSIONS CALENDAR */}
          {activeTab === 'sessions' && (
            <div className="space-y-4">
              {sessions.length === 0 ? (
                <EmptyState
                  title="Henüz Planlanmış Ders Seansı Yok"
                  description="Yeni seans ekleyebilir veya haftalık şablondan toplu seans üretebilirsiniz."
                  actionLabel="+ İlk Seansı Ekle"
                  onAction={() => setShowSessionModal(true)}
                />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {sessions.map((sess) => {
                    const isFull = sess.confirmed_count >= sess.capacity
                    return (
                      <div
                        key={sess.id}
                        className="p-5 rounded-xl border border-border/40 bg-card hover:border-primary/40 transition-all flex flex-col justify-between shadow-sm relative overflow-hidden"
                      >
                        <div
                          className="absolute top-0 left-0 right-0 h-1.5"
                          style={{ backgroundColor: sess.color_hex || '#3B82F6' }}
                        />
                        <div>
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-muted/60 text-muted-foreground uppercase tracking-wider">
                              {sess.class_category || 'DERS'}
                            </span>
                            <StatusBadge
                              status={
                                sess.status === 'SCHEDULED'
                                  ? isFull
                                    ? 'PENDING'
                                    : 'ACTIVE'
                                  : sess.status
                              }
                            />
                          </div>

                          <h3 className="font-bold text-lg text-foreground mb-1">
                            {sess.class_type_name || 'Grup Dersi'}
                          </h3>

                          <div className="text-sm text-muted-foreground space-y-1 my-3">
                            <div className="flex items-center gap-2">
                              <span>⏰</span>
                              <span className="font-medium text-foreground">
                                {formatDateTr(sess.start_time_utc)} - {formatTime(sess.end_time_utc)}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span>🏋️</span>
                              <span>Eğitmen: {sess.trainer_name || 'Atanmamış'}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span>📍</span>
                              <span>{sess.location_name || 'Ana Şube'} {sess.room_name ? `(${sess.room_name})` : ''}</span>
                            </div>
                          </div>

                          {/* Capacity Bar */}
                          <div className="my-3">
                            <div className="flex justify-between text-xs font-medium mb-1">
                              <span>Doluluk: {sess.confirmed_count} / {sess.capacity}</span>
                              {sess.waitlist_count > 0 && (
                                <span className="text-amber-500 font-semibold">
                                  🟡 {sess.waitlist_count} Yedek
                                </span>
                              )}
                            </div>
                            <div className="w-full bg-muted/50 rounded-full h-2 overflow-hidden">
                              <div
                                className={`h-full transition-all ${
                                  isFull ? 'bg-amber-500' : 'bg-emerald-500'
                                }`}
                                style={{
                                  width: `${Math.min(100, (sess.confirmed_count / sess.capacity) * 100)}%`,
                                }}
                              />
                            </div>
                          </div>
                        </div>

                        <div className="pt-3 border-t border-border/30 flex justify-end">
                          <button
                            onClick={() => openRoster(sess.id)}
                            className="btn btn-outline text-xs px-3 py-1.5 w-full justify-center"
                          >
                            👥 Katılımcı Listesi & Yoklama ({sess.confirmed_count + sess.waitlist_count})
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: SCHEDULES */}
          {activeTab === 'schedules' && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl border border-border/40 bg-card">
                <h3 className="font-semibold text-foreground mb-2">Haftalık Sabit Program Şablonu</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Burada tanımlanan haftalık dersler &quot;Toplu Seans Üret&quot; butonuyla istenen tarih aralığına otomatik kopyalanır.
                </p>

                {schedules.length === 0 ? (
                  <EmptyState
                    title="Haftalık Program Tanımlanmamış"
                    description="Şablon ekleyerek her hafta tekrar eden seansları tek tıkla üretebilirsiniz."
                  />
                ) : (
                  <div className="divide-y divide-border/30">
                    {schedules.map((sch) => (
                      <div key={sch.id} className="py-3 flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-foreground">{sch.class_type_name}</span>
                            <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary font-medium">
                              {DAYS_TR[sch.day_of_week]}
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            Saat: {sch.start_time.slice(0, 5)} - {sch.end_time.slice(0, 5)} | Eğitmen: {sch.trainer_name || 'Eğitmen'} | Kapasite: {sch.capacity} kişi {sch.room_name ? `(${sch.room_name})` : ''}
                          </div>
                        </div>
                        <span className="text-xs text-emerald-500 font-medium">Aktif Şablon</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: CLASS TYPES */}
          {activeTab === 'types' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {classTypes.map((t) => (
                <div key={t.id} className="p-5 rounded-xl border border-border/40 bg-card flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground">
                        {t.category}
                      </span>
                      <span
                        className="w-3.5 h-3.5 rounded-full"
                        style={{ backgroundColor: t.color_hex }}
                        title={t.color_hex}
                      />
                    </div>
                    <h3 className="font-bold text-foreground text-lg">{t.name}</h3>
                    {t.description && (
                      <p className="text-sm text-muted-foreground my-2">{t.description}</p>
                    )}
                    <div className="text-xs text-muted-foreground space-y-1 mt-4">
                      <div>⏱️ Süre: {t.duration_minutes} dakika</div>
                      <div>👥 Varsayılan Kapasite: {t.default_capacity} kişi</div>
                      <div>⏳ İptal Eşiği: {t.cancellation_cutoff_minutes} dk öncesine kadar</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 4: PT APPOINTMENTS */}
          {activeTab === 'pt' && (
            <div className="p-5 rounded-xl border border-border/40 bg-card">
              <h3 className="font-semibold text-foreground mb-3">Kişisel Antrenman (PT) Randevuları</h3>
              {ptAppointments.length === 0 ? (
                <EmptyState
                  title="Henüz PT Randevusu Yok"
                  description="Üyeler mobil/web portal üzerinden müsait antrenörlere birebir randevu alabilir."
                />
              ) : (
                <div className="divide-y divide-border/30">
                  {ptAppointments.map((pt) => (
                    <div key={pt.id} className="py-3.5 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-foreground">
                          {pt.member_name || 'Üye'} ↔ {pt.trainer_name || 'Antrenör'}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          ⏰ {formatDateTr(pt.start_time_utc)} - {formatTime(pt.end_time_utc)}
                          {pt.notes && ` | Not: "${pt.notes}"`}
                        </div>
                      </div>
                      <StatusBadge
                        status={
                          pt.status === 'CONFIRMED'
                            ? 'ACTIVE'
                            : pt.status === 'ATTENDED'
                            ? 'COMPLETED'
                            : 'CANCELLED'
                        }
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ROSTER MODAL / DRAWER */}
      {selectedSessionRoster && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-xl bg-card border-l border-border/40 h-full p-6 overflow-y-auto flex flex-col justify-between shadow-2xl">
            <div>
              <div className="flex justify-between items-start pb-4 border-b border-border/30">
                <div>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-primary/10 text-primary">
                    YOKLAMA & KATILIMCI LİSTESİ
                  </span>
                  <h2 className="text-xl font-bold text-foreground mt-1">
                    {selectedSessionRoster.session.class_type_name}
                  </h2>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {formatDateTr(selectedSessionRoster.session.start_time_utc)} | Kapasite: {selectedSessionRoster.total_confirmed} / {selectedSessionRoster.session.capacity} (Yedek: {selectedSessionRoster.total_waitlisted})
                  </p>
                </div>
                <button
                  onClick={() => setSelectedSessionRoster(null)}
                  className="text-muted-foreground hover:text-foreground text-xl font-bold p-1"
                >
                  ✕
                </button>
              </div>

              {rosterLoading ? (
                <div className="py-8">
                  <LoadingSkeleton rows={3} />
                </div>
              ) : selectedSessionRoster.attendees.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground">
                  Bu seansa henüz kayıtlı katılımcı bulunmamaktadır.
                </div>
              ) : (
                <div className="divide-y divide-border/30 my-4">
                  {selectedSessionRoster.attendees.map((att) => (
                    <div key={att.booking_id} className="py-3.5 flex items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-foreground">{att.member_name}</span>
                          {att.status === 'WAITLISTED' && (
                            <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-500 font-bold">
                              Yedek #{att.waitlist_position}
                            </span>
                          )}
                          {att.status === 'ATTENDED' && (
                            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-medium">
                              Geldi
                            </span>
                          )}
                          {att.status === 'NO_SHOW' && (
                            <span className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-500 font-medium">
                              Gelmedi
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {att.member_email || att.member_phone || 'İletişim yok'}
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5">
                        {att.status === 'CONFIRMED' && (
                          <>
                            <button
                              onClick={() => handleMarkAttendance(att.booking_id, 'ATTENDED')}
                              className="btn btn-primary text-xs px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                              title="Geldi Olarak İşaretle"
                            >
                              ✓ Geldi
                            </button>
                            <button
                              onClick={() => handleMarkAttendance(att.booking_id, 'NO_SHOW')}
                              className="btn btn-secondary text-xs px-2.5 py-1 text-red-400 hover:text-red-300"
                              title="Gelmedi Olarak İşaretle"
                            >
                              ✕ Gelmedi
                            </button>
                          </>
                        )}
                        {att.status !== 'CANCELLED' && (
                          <button
                            onClick={() => handleAdminCancelBooking(att.booking_id)}
                            className="text-xs text-muted-foreground hover:text-red-400 p-1"
                            title="İptal Et & Yedekten Terfi Ettir"
                          >
                            İptal
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-border/30 flex justify-end">
              <button
                onClick={() => setSelectedSessionRoster(null)}
                className="btn btn-secondary text-sm px-4 py-2"
              >
                Kapat
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: CREATE CLASS TYPE */}
      {showTypeModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/40 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-foreground">Yeni Ders Tipi Ekle</h3>
            <form onSubmit={handleCreateType} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Ders Adı</label>
                <input
                  type="text"
                  required
                  value={typeName}
                  onChange={(e) => setTypeName(e.target.value)}
                  placeholder="Örn: Reformer Pilates, Spinning Blast"
                  className="input w-full text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Kategori</label>
                  <select
                    value={typeCategory}
                    onChange={(e) => setTypeCategory(e.target.value)}
                    className="input w-full text-sm"
                  >
                    <option value="CARDIO">Cardio</option>
                    <option value="PILATES">Pilates</option>
                    <option value="YOGA">Yoga</option>
                    <option value="HIIT">HIIT</option>
                    <option value="STRENGTH">Strength</option>
                    <option value="CROSSFIT">CrossFit</option>
                    <option value="BOXING">Boks</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Süre (Dk)</label>
                  <input
                    type="number"
                    min={15}
                    max={180}
                    value={typeDuration}
                    onChange={(e) => setTypeDuration(Number(e.target.value))}
                    className="input w-full text-sm"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Varsayılan Kapasite</label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={typeCapacity}
                    onChange={(e) => setTypeCapacity(Number(e.target.value))}
                    className="input w-full text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Renk</label>
                  <input
                    type="color"
                    value={typeColor}
                    onChange={(e) => setTypeColor(e.target.value)}
                    className="h-9 w-full rounded-md cursor-pointer bg-transparent"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">İptal Eşiği (Dakika)</label>
                <input
                  type="number"
                  min={0}
                  max={1440}
                  value={typeCutoff}
                  onChange={(e) => setTypeCutoff(Number(e.target.value))}
                  placeholder="120 (Seans başlamadan 2 saat öncesine kadar cezasız iptal)"
                  className="input w-full text-sm"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowTypeModal(false)}
                  className="btn btn-secondary text-sm px-4 py-2"
                >
                  Vazgeç
                </button>
                <button type="submit" className="btn btn-primary text-sm px-4 py-2">
                  Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE SESSION */}
      {showSessionModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/40 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-foreground">Yeni Ders Seansı Planla</h3>
            <form onSubmit={handleCreateSession} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Ders Tipi</label>
                <select
                  value={sessClassTypeId}
                  onChange={(e) => setSessClassTypeId(e.target.value)}
                  className="input w-full text-sm"
                >
                  {classTypes.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} ({t.duration_minutes} dk)
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Şube</label>
                <select
                  value={sessLocationId}
                  onChange={(e) => setSessLocationId(e.target.value)}
                  className="input w-full text-sm"
                >
                  {locations.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Eğitmen</label>
                <select
                  value={sessTrainerUserId}
                  onChange={(e) => setSessTrainerUserId(e.target.value)}
                  className="input w-full text-sm"
                >
                  {staffList.map((s) => (
                    <option key={s.id} value={s.user_id}>
                      {s.first_name} {s.last_name} ({s.role})
                    </option>
                  ))}
                  {session?.user_id && !staffList.some((s) => s.user_id === session.user_id) && (
                    <option value={session.user_id}>
                      {session.email || 'Kulüp Yöneticisi / Eğitmen'}
                    </option>
                  )}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Başlangıç Zamanı</label>
                  <input
                    type="datetime-local"
                    required
                    value={sessStart}
                    onChange={(e) => setSessStart(e.target.value)}
                    className="input w-full text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Bitiş Zamanı</label>
                  <input
                    type="datetime-local"
                    required
                    value={sessEnd}
                    onChange={(e) => setSessEnd(e.target.value)}
                    className="input w-full text-sm"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Kapasite</label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={sessCapacity}
                    onChange={(e) => setSessCapacity(Number(e.target.value))}
                    className="input w-full text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Oda / Stüdyo</label>
                  <input
                    type="text"
                    value={sessRoom}
                    onChange={(e) => setSessRoom(e.target.value)}
                    placeholder="Stüdyo A"
                    className="input w-full text-sm"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowSessionModal(false)}
                  className="btn btn-secondary text-sm px-4 py-2"
                >
                  Vazgeç
                </button>
                <button type="submit" className="btn btn-primary text-sm px-4 py-2">
                  Seansı Ekle
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: GENERATE SESSIONS */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border/40 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-foreground">Haftalık Şablondan Toplu Seans Üret</h3>
            <p className="text-xs text-muted-foreground">
              Seçilen haftalık program şablonuna göre belirtilen tarih aralığındaki seanslar otomatik oluşturulacaktır.
            </p>
            <form onSubmit={handleGenerateSessions} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">Şablon Programı</label>
                <select
                  value={genScheduleId}
                  onChange={(e) => setGenScheduleId(e.target.value)}
                  className="input w-full text-sm"
                >
                  {schedules.map((sch) => (
                    <option key={sch.id} value={sch.id}>
                      {sch.class_type_name} ({DAYS_TR[sch.day_of_week]} {sch.start_time.slice(0, 5)})
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Başlangıç Tarihi</label>
                  <input
                    type="date"
                    required
                    value={genStartDate}
                    onChange={(e) => setGenStartDate(e.target.value)}
                    className="input w-full text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Bitiş Tarihi</label>
                  <input
                    type="date"
                    required
                    value={genEndDate}
                    onChange={(e) => setGenEndDate(e.target.value)}
                    className="input w-full text-sm"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="btn btn-secondary text-sm px-4 py-2"
                >
                  Vazgeç
                </button>
                <button type="submit" className="btn btn-primary text-sm px-4 py-2">
                  ⚡ Seansları Üret
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

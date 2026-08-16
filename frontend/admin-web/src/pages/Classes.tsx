import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, LoadingSkeleton, PageHeader } from '../components/ui'
import { PtTab } from './classes/PtTab'
import { RosterDrawer } from './classes/RosterDrawer'
import { SchedulesTab } from './classes/SchedulesTab'
import { SessionsTab } from './classes/SessionsTab'
import { TypesTab } from './classes/TypesTab'
import {
  DAYS_TR,
  formatApiError,
  type ClassSchedule,
  type ClassSession,
  type ClassSessionRoster,
  type ClassType,
  staffLabel,
  type LocationItem,
  type PtAppointment,
  type TrainerOption,
} from './classes/types'

export type {
  ClassAttendee,
  ClassBooking,
  ClassSchedule,
  ClassSession,
  ClassSessionRoster,
  ClassType,
  LocationItem,
  PtAppointment,
  TrainerOption,
} from './classes/types'

export default function Classes() {
  const { session } = useAuth()
  const [activeTab, setActiveTab] = useState<'sessions' | 'schedules' | 'types' | 'pt'>('sessions')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [sessions, setSessions] = useState<ClassSession[]>([])
  const [schedules, setSchedules] = useState<ClassSchedule[]>([])
  const [classTypes, setClassTypes] = useState<ClassType[]>([])
  const [ptAppointments, setPtAppointments] = useState<PtAppointment[]>([])
  const [locations, setLocations] = useState<LocationItem[]>([])
  const [trainers, setTrainers] = useState<TrainerOption[]>([])

  const [selectedSessionRoster, setSelectedSessionRoster] = useState<ClassSessionRoster | null>(null)
  const [rosterLoading, setRosterLoading] = useState(false)

  const [showTypeModal, setShowTypeModal] = useState(false)
  const [showSessionModal, setShowSessionModal] = useState(false)
  const [showGenerateModal, setShowGenerateModal] = useState(false)

  const [typeName, setTypeName] = useState('')
  const [typeCategory, setTypeCategory] = useState('CARDIO')
  const [typeDuration, setTypeDuration] = useState(45)
  const [typeCapacity, setTypeCapacity] = useState(10)
  const [typeColor, setTypeColor] = useState('#10B981')
  const [typeCutoff, setTypeCutoff] = useState(120)

  const [sessLocationId, setSessLocationId] = useState('')
  const [sessClassTypeId, setSessClassTypeId] = useState('')
  const [sessTrainerUserId, setSessTrainerUserId] = useState('')
  const [sessStart, setSessStart] = useState('')
  const [sessEnd, setSessEnd] = useState('')
  const [sessCapacity, setSessCapacity] = useState(10)
  const [sessRoom, setSessRoom] = useState('')

  const [genScheduleId, setGenScheduleId] = useState('')
  const [genStartDate, setGenStartDate] = useState('')
  const [genEndDate, setGenEndDate] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [typesRes, schedsRes, sessRes, ptRes, locsRes, trainerRes] = await Promise.all([
        api<ClassType[]>('/api/v1/classes/types'),
        api<ClassSchedule[]>('/api/v1/classes/schedules'),
        api<ClassSession[]>('/api/v1/classes/sessions'),
        api<PtAppointment[]>('/api/v1/classes/pt/appointments'),
        api<LocationItem[]>('/api/v1/locations'),
        api<TrainerOption[]>('/api/v1/classes/trainers').catch(() => [] as TrainerOption[]),
      ])

      setClassTypes(typesRes)
      setSchedules(schedsRes)
      setSessions(sessRes)
      setPtAppointments(ptRes)
      setLocations(locsRes)
      setTrainers(trainerRes)

      if (locsRes.length > 0) setSessLocationId(locsRes[0].id)
      if (typesRes.length > 0) setSessClassTypeId(typesRes[0].id)
      if (trainerRes.length > 0) setSessTrainerUserId(trainerRes[0].user_id)
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

  async function handleAdminCancelBooking(bookingId: string) {
    if (
      !confirm(
        'Bu rezervasyonu iptal etmek istediğinize emin misiniz? Yedekte üye varsa otomatik asil listeye terfi ettirilecektir.',
      )
    )
      return
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

  async function handleCreateSession(e: FormEvent) {
    e.preventDefault()
    const finalLocationId = sessLocationId || locations[0]?.id
    const finalClassTypeId = sessClassTypeId || classTypes[0]?.id
    const finalTrainerId = sessTrainerUserId || trainers[0]?.user_id || session?.user_id

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
            <button onClick={() => setShowSessionModal(true)} className="btn btn-primary text-sm px-4 py-2">
              + Yeni Seans Ekle
            </button>
            <button onClick={() => setShowGenerateModal(true)} className="btn btn-secondary text-sm px-4 py-2">
              ⚡ Toplu Seans Üret
            </button>
            <button onClick={() => setShowTypeModal(true)} className="btn btn-secondary text-sm px-4 py-2">
              + Ders Tipi
            </button>
          </div>
        }
      />

      {error && <Alert variant="error">{error}</Alert>}
      {message && <Alert variant="success">{message}</Alert>}

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
          {activeTab === 'sessions' && (
            <SessionsTab
              sessions={sessions}
              onOpenSessionModal={() => setShowSessionModal(true)}
              onOpenRoster={(id) => void openRoster(id)}
            />
          )}
          {activeTab === 'schedules' && <SchedulesTab schedules={schedules} />}
          {activeTab === 'types' && <TypesTab classTypes={classTypes} />}
          {activeTab === 'pt' && <PtTab appointments={ptAppointments} />}
        </>
      )}

      {selectedSessionRoster && (
        <RosterDrawer
          roster={selectedSessionRoster}
          loading={rosterLoading}
          onClose={() => setSelectedSessionRoster(null)}
          onMarkAttendance={(id, status) => void handleMarkAttendance(id, status)}
          onCancelBooking={(id) => void handleAdminCancelBooking(id)}
        />
      )}

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
                  {trainers.length === 0 && (
                    <option value="">Henüz antrenör tanımlı değil</option>
                  )}
                  {trainers.map((t) => (
                    <option key={t.user_id} value={t.user_id}>
                      {staffLabel(t)}
                    </option>
                  ))}
                  {session?.user_id && !trainers.some((t) => t.user_id === session.user_id) && (
                    <option value={session.user_id}>{session.email || 'Kulüp Yöneticisi / Eğitmen'}</option>
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

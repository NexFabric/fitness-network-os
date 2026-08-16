import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import MemberAccessLogs from '../components/MemberAccessLogs'
import { Alert, EmptyState, LoadingSkeleton, StatusBadge } from '../components/ui'
import type { ClassSession, ClassSessionRoster, PtAppointment } from './Classes'

type Member = {
  id: string
  member_number: string
  first_name: string
  last_name: string
  status: string
}

type EntitlementCheck = {
  granted: boolean
  reason: string | null
  remaining: number | null
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

/**
 * Trainer console with Member management and Class/PT attendance ledger.
 */
export default function TrainerPortal() {
  const { session, hasPermission } = useAuth()

  const [activeTab, setActiveTab] = useState<'members' | 'classes' | 'pt'>('members')

  // Members state
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const [checking, setChecking] = useState(false)
  const [checkResult, setCheckResult] = useState<EntitlementCheck | null>(null)
  const [checkError, setCheckError] = useState<string | null>(null)

  // Classes & PT state
  const [sessions, setSessions] = useState<ClassSession[]>([])
  const [ptAppointments, setPtAppointments] = useState<PtAppointment[]>([])
  const [selectedSessionRoster, setSelectedSessionRoster] = useState<ClassSessionRoster | null>(null)
  const [rosterLoading, setRosterLoading] = useState(false)

  const isAssignmentScoped = !hasPermission('members:read:all')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [membersRes, sessionsRes, ptRes] = await Promise.all([
        api<Member[]>('/api/v1/members?limit=100').catch(() => [] as Member[]),
        api<ClassSession[]>('/api/v1/classes/sessions').catch(() => [] as ClassSession[]),
        api<PtAppointment[]>('/api/v1/classes/pt/appointments').catch(() => [] as PtAppointment[]),
      ])
      setMembers(membersRes)
      setSessions(sessionsRes)
      setPtAppointments(ptRes)
    } catch {
      setError('Veriler yüklenemedi. Birkaç saniye sonra tekrar deneyin.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  async function handleCheckEntitlement(memberId: string) {
    setChecking(true)
    setCheckError(null)
    setCheckResult(null)
    try {
      setCheckResult(
        await api<EntitlementCheck>(
          `/api/v1/members/${memberId}/entitlements/check`,
          { method: 'POST', body: { action: 'GYM_ENTRY', quantity: 1 } },
        ),
      )
    } catch (err) {
      setCheckError(
        err instanceof ApiError && err.status === 403
          ? 'Bu üye için yetkiniz yok.'
          : 'Hak kontrolü yapılamadı. Birkaç saniye sonra tekrar deneyin.',
      )
    } finally {
      setChecking(false)
    }
  }

  async function openRoster(sessionId: string) {
    setRosterLoading(true)
    try {
      const res = await api<ClassSessionRoster>(`/api/v1/classes/sessions/${sessionId}/roster`)
      setSelectedSessionRoster(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Yoklama listesi alınamadı.')
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
      setMessage(`Yoklama kaydedildi: ${statusVal === 'ATTENDED' ? 'Geldi' : 'Gelmedi'}`)
      if (selectedSessionRoster) {
        await openRoster(selectedSessionRoster.session.id)
      }
      loadData()
    } catch {
      setError('Yoklama kaydedilemedi.')
    }
  }

  const selected = members.find((m) => m.id === selectedId) ?? null

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 font-sans">
      <div className="mx-auto w-full max-w-5xl">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              Antrenör Portalı
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              {isAssignmentScoped
                ? 'Size atanmış üyeler & ders seansları'
                : 'Kulüpteki tüm üyeler & dersler'}
              {session?.email && ` · ${session.email}`}
            </p>
          </div>
          <Link
            to="/portal"
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800"
          >
            Portallara dön
          </Link>
        </header>

        {error && <Alert variant="error">{error}</Alert>}
        {message && <Alert variant="success">{message}</Alert>}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 gap-4 mb-6 text-sm font-medium">
          <button
            onClick={() => setActiveTab('members')}
            className={`pb-3 px-2 border-b-2 transition-colors ${
              activeTab === 'members'
                ? 'border-emerald-500 text-emerald-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            👥 Üyeler & Hak Kontrolü ({members.length})
          </button>
          <button
            onClick={() => setActiveTab('classes')}
            className={`pb-3 px-2 border-b-2 transition-colors ${
              activeTab === 'classes'
                ? 'border-emerald-500 text-emerald-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            📅 Grup Derslerim & Yoklama ({sessions.length})
          </button>
          <button
            onClick={() => setActiveTab('pt')}
            className={`pb-3 px-2 border-b-2 transition-colors ${
              activeTab === 'pt'
                ? 'border-emerald-500 text-emerald-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            🏋️ Birebir PT Seanslarım ({ptAppointments.length})
          </button>
        </div>

        {loading && <LoadingSkeleton rows={5} />}

        {/* TAB 1: MEMBERS */}
        {!loading && activeTab === 'members' && (
          <div>
            {members.length === 0 ? (
              <EmptyState
                title={
                  isAssignmentScoped
                    ? 'Size atanmış üye yok'
                    : 'Kayıtlı üye bulunmuyor'
                }
                description={
                  isAssignmentScoped
                    ? 'Kulüp yöneticiniz size üye atadığında burada görünecekler.'
                    : 'Üye kaydı yapıldığında burada listelenir.'
                }
              />
            ) : (
              <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
                <section
                  aria-label="Üye listesi"
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-3"
                >
                  <ul className="divide-y divide-slate-800/70">
                    {members.map((member) => (
                      <li key={member.id}>
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedId(member.id)
                            setCheckResult(null)
                            setCheckError(null)
                          }}
                          aria-current={member.id === selectedId}
                          className={`w-full rounded-xl px-3 py-3 text-left transition-colors ${
                            member.id === selectedId
                              ? 'bg-slate-800'
                              : 'hover:bg-slate-800/50'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-semibold text-white">
                              {member.first_name} {member.last_name}
                            </span>
                            <StatusBadge status={member.status} kind="member" />
                          </div>
                          <span className="text-xs text-slate-500">
                            {member.member_number}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>

                <section
                  aria-label="Üye detayı"
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                >
                  {!selected ? (
                    <EmptyState
                      title="Üye seçin"
                      description="Giriş geçmişini ve hak durumunu görmek için soldan bir üye seçin."
                    />
                  ) : (
                    <>
                      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <h2 className="text-lg font-bold text-white">
                            {selected.first_name} {selected.last_name}
                          </h2>
                          <p className="text-xs text-slate-500">
                            {selected.member_number}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => void handleCheckEntitlement(selected.id)}
                          disabled={checking}
                          className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-bold text-white hover:bg-emerald-500 disabled:opacity-50"
                        >
                          {checking ? 'Kontrol ediliyor…' : 'Giriş hakkını kontrol et'}
                        </button>
                      </div>

                      {checkError && <Alert variant="error">{checkError}</Alert>}

                      {checkResult && (
                        <Alert variant={checkResult.granted ? 'success' : 'error'}>
                          {checkResult.granted
                            ? `Giriş hakkı var${
                                checkResult.remaining !== null
                                  ? ` · kalan: ${checkResult.remaining}`
                                  : ''
                              }`
                            : `Giriş hakkı yok${
                                checkResult.reason ? ` · ${checkResult.reason}` : ''
                              }`}
                        </Alert>
                      )}

                      <h3 className="mb-1 mt-6 text-sm font-bold text-slate-300">
                        Turnike giriş geçmişi
                      </h3>
                      <MemberAccessLogs memberId={selected.id} />
                    </>
                  )}
                </section>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: CLASS SESSIONS */}
        {!loading && activeTab === 'classes' && (
          <div className="space-y-4">
            {sessions.length === 0 ? (
              <EmptyState
                title="Planlanmış Grup Dersi Bulunmuyor"
                description="Yöneticiniz ders atadığında burada listelenecektir."
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sessions.map((sess) => (
                  <div
                    key={sess.id}
                    className="p-5 rounded-2xl border border-slate-800 bg-slate-900 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {sess.class_type_category || 'GRUP DERSI'}
                        </span>
                        <span className="text-xs font-semibold text-emerald-400">
                          {sess.confirmed_count} / {sess.capacity} Kişi
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-white mb-1">
                        {sess.class_type_name}
                      </h3>
                      <div className="text-xs text-slate-400 space-y-1 my-3">
                        <div>⏰ {formatDateTr(sess.start_time_utc)} - {formatTime(sess.end_time_utc)}</div>
                        <div>📍 {sess.location_name || 'Ana Şube'} {sess.room_name ? `(${sess.room_name})` : ''}</div>
                        {sess.waitlist_count > 0 && (
                          <div className="text-amber-400 font-semibold">🟡 {sess.waitlist_count} Yedek Bekliyor</div>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => openRoster(sess.id)}
                      className="mt-3 w-full rounded-xl bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30 border border-emerald-500/30 py-2.5 text-xs font-bold transition-colors"
                    >
                      👥 Yoklama Listesini Aç ({sess.confirmed_count + sess.waitlist_count} Kayıtlı)
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: PT APPOINTMENTS */}
        {!loading && activeTab === 'pt' && (
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900">
            <h3 className="text-base font-bold text-white mb-3">Birebir PT Randevuları</h3>
            {ptAppointments.length === 0 ? (
              <EmptyState
                title="PT Randevusu Yok"
                description="Üyeler sizinle randevu aldığında burada listelenecektir."
              />
            ) : (
              <div className="divide-y divide-slate-800/70">
                {ptAppointments.map((pt) => (
                  <div key={pt.id} className="py-3.5 flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-white">
                        {pt.member_name || 'Üye'}
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        ⏰ {formatDateTr(pt.start_time_utc)} - {formatTime(pt.end_time_utc)}
                        {pt.notes && ` | Not: "${pt.notes}"`}
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-2 py-1 rounded bg-emerald-500/10 text-emerald-400">
                      {pt.status === 'CONFIRMED' ? 'Onaylandı' : pt.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ROSTER MODAL */}
        {selectedSessionRoster && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4 max-h-[85vh] overflow-y-auto">
              <div className="flex justify-between items-start border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-lg font-bold text-white">
                    {selectedSessionRoster.session.class_type_name} Yoklaması
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {formatDateTr(selectedSessionRoster.session.start_time_utc)}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedSessionRoster(null)}
                  className="text-slate-400 hover:text-white font-bold text-xl"
                >
                  ✕
                </button>
              </div>

              {rosterLoading ? (
                <LoadingSkeleton rows={3} />
              ) : selectedSessionRoster.attendees.length === 0 ? (
                <div className="py-8 text-center text-sm text-slate-400">
                  Bu seansa henüz kayıtlı katılımcı bulunmamaktadır.
                </div>
              ) : (
                <div className="divide-y divide-slate-800/70">
                  {selectedSessionRoster.attendees.map((att) => (
                    <div key={att.booking_id} className="py-3 flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white text-sm">{att.member_name}</span>
                          {att.status === 'WAITLISTED' && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                              Yedek #{att.waitlist_position}
                            </span>
                          )}
                          {att.status === 'ATTENDED' && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-medium">
                              Geldi
                            </span>
                          )}
                          {att.status === 'NO_SHOW' && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/20 text-red-300 font-medium">
                              Gelmedi
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">{att.member_email || att.member_phone}</div>
                      </div>

                      {att.status === 'CONFIRMED' && (
                        <div className="flex gap-1.5">
                          <button
                            onClick={() => handleMarkAttendance(att.booking_id, 'ATTENDED')}
                            className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-2.5 py-1 rounded-lg font-bold"
                          >
                            ✓ Geldi
                          </button>
                          <button
                            onClick={() => handleMarkAttendance(att.booking_id, 'NO_SHOW')}
                            className="bg-slate-800 hover:bg-slate-700 text-red-400 text-xs px-2.5 py-1 rounded-lg font-bold"
                          >
                            ✕ Gelmedi
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="pt-3 border-t border-slate-800 flex justify-end">
                <button
                  onClick={() => setSelectedSessionRoster(null)}
                  className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800"
                >
                  Kapat
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

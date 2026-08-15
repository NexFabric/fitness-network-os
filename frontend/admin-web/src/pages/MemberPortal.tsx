import { useCallback, useEffect, useState } from 'react'
import QRCode from 'qrcode'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, EmptyState, LoadingSkeleton } from '../components/ui'
import type { ClassBooking, ClassSession, PtAppointment, StaffItem } from './Classes'

type MeMember = {
  id: string
  member_number: string
  first_name: string
  last_name: string
  status: string
}

type Membership = {
  id: string
  status: string
  start_date: string
  end_date: string | null
}

type Wallet = {
  wallet_id: string
  entitlement_code: string | null
  entitlement_name: string | null
  allocated: number
  remaining: number
  expires_at: string | null
}

type EntitlementsSummary = {
  member_id: string
  wallets: Wallet[]
}

type MeCheckin = {
  id: string
  tenant_id: string
  member_id: string
  location_id: string
  device_id: string | null
  checkin_time: string
  checkout_time: string | null
}

type MeInvoice = {
  id: string
  invoice_number: string | null
  status: string
  total_amount_minor: number
  paid_amount_minor: number
  discount_amount_minor: number
  currency: string
  due_date: string | null
  issued_at: string | null
  created_at: string
}

type MePayment = {
  id: string
  amount_minor: number
  refunded_amount_minor: number
  currency: string
  status: string
  method: string
  paid_at: string | null
  created_at: string
}

type MeConsent = {
  id: string
  consent_type: string
  document_version: string
  status: string
  given_at: string | null
  withdrawn_at: string | null
}

type IssuedQr = {
  token: string
  jti: string
  exp: string
}

const TTL_SECONDS = 60

type ActiveTab = 'access' | 'classes' | 'memberships' | 'history' | 'finance' | 'preferences'

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

function formatMinor(minor: number, currency: string = 'TRY'): string {
  const abs = Math.abs(minor)
  return `${Math.floor(abs / 100)},${String(abs % 100).padStart(2, '0')} ${currency}`
}

export default function MemberPortal() {
  const { session, signOut } = useAuth()

  const [activeTab, setActiveTab] = useState<ActiveTab>('access')
  const [member, setMember] = useState<MeMember | null>(null)
  const [memberships, setMemberships] = useState<Membership[]>([])
  const [entitlements, setEntitlements] = useState<EntitlementsSummary | null>(null)
  const [checkins, setCheckins] = useState<MeCheckin[]>([])
  const [invoices, setInvoices] = useState<MeInvoice[]>([])
  const [payments, setPayments] = useState<MePayment[]>([])
  const [consents, setConsents] = useState<MeConsent[]>([])

  // Classes & PT state
  const [classSessions, setClassSessions] = useState<ClassSession[]>([])
  const [myBookings, setMyBookings] = useState<ClassBooking[]>([])
  const [myPtAppointments, setMyPtAppointments] = useState<PtAppointment[]>([])
  const [trainers, setTrainers] = useState<StaffItem[]>([])
  const [bookingLoading, setBookingLoading] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL')

  // PT Booking Modal
  const [showPtModal, setShowPtModal] = useState(false)
  const [ptTrainerId, setPtTrainerId] = useState('')
  const [ptStart, setPtStart] = useState('')
  const [ptEnd, setPtEnd] = useState('')
  const [ptNotes, setPtNotes] = useState('')

  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  // QR state
  const [qr, setQr] = useState<IssuedQr | null>(null)
  const [qrImage, setQrImage] = useState<string | null>(null)
  const [issuing, setIssuing] = useState(false)
  const [issueError, setIssueError] = useState<string | null>(null)
  const [secondsLeft, setSecondsLeft] = useState(0)

  const [consentUpdating, setConsentUpdating] = useState<string | null>(null)

  const loadProfile = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const [me, myMemberships, myEntitlements] = await Promise.all([
        api<MeMember>('/api/v1/me/member'),
        api<Membership[]>('/api/v1/me/memberships'),
        api<EntitlementsSummary>('/api/v1/me/entitlements'),
      ])
      setMember(me)
      setMemberships(myMemberships)
      setEntitlements(myEntitlements)
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setLoadError(
          'Hesabınız bir üye kaydına bağlı değil. Kulüp resepsiyonuyla iletişime geçin.',
        )
      } else {
        setLoadError(
          'Bilgileriniz yüklenemedi. Birkaç saniye sonra tekrar deneyin.',
        )
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const loadClassesData = useCallback(async () => {
    try {
      const [sessionsRes, bookingsRes, ptRes, staffRes] = await Promise.all([
        api<ClassSession[]>('/api/v1/me/classes/sessions'),
        api<ClassBooking[]>('/api/v1/me/classes/bookings').catch(() => [] as ClassBooking[]),
        api<PtAppointment[]>('/api/v1/me/pt/appointments').catch(() => [] as PtAppointment[]),
        api<StaffItem[]>('/api/v1/staff').catch(() => [] as StaffItem[]),
      ])
      setClassSessions(sessionsRes)
      setMyBookings(bookingsRes)
      setMyPtAppointments(ptRes)
      setTrainers(staffRes)
      if (staffRes.length > 0) setPtTrainerId(staffRes[0].user_id)
    } catch {
      // ignore
    }
  }, [])

  const loadTabData = useCallback(async (tab: ActiveTab) => {
    try {
      if (tab === 'classes') {
        await loadClassesData()
      } else if (tab === 'history') {
        const myCheckins = await api<MeCheckin[]>('/api/v1/me/checkins')
        setCheckins(myCheckins)
      } else if (tab === 'finance') {
        const [myInvoices, myPayments] = await Promise.all([
          api<MeInvoice[]>('/api/v1/me/invoices'),
          api<MePayment[]>('/api/v1/me/payments'),
        ])
        setInvoices(myInvoices)
        setPayments(myPayments)
      } else if (tab === 'preferences') {
        const myConsents = await api<MeConsent[]>('/api/v1/me/consents')
        setConsents(myConsents)
      }
    } catch {
      // ignore
    }
  }, [loadClassesData])

  useEffect(() => {
    void loadProfile()
  }, [loadProfile])

  useEffect(() => {
    void loadTabData(activeTab)
  }, [activeTab, loadTabData])

  // QR Countdown
  useEffect(() => {
    if (secondsLeft <= 0) return
    const timer = setInterval(() => {
      setSecondsLeft((prev) => (prev <= 1 ? 0 : prev - 1))
    }, 1000)
    return () => clearInterval(timer)
  }, [secondsLeft])

  async function handleIssueQr() {
    setIssuing(true)
    setIssueError(null)
    try {
      const res = await api<IssuedQr>('/api/v1/access/qr/issue-self', {
        method: 'POST',
        body: { ttl_seconds: TTL_SECONDS },
      })
      setQr(res)
      setSecondsLeft(TTL_SECONDS)
      const dataUrl = await QRCode.toDataURL(res.token, {
        width: 256,
        margin: 2,
        color: { dark: '#000000', light: '#ffffff' },
      })
      setQrImage(dataUrl)
    } catch (err) {
      setIssueError(
        err instanceof ApiError && err.status === 403
          ? 'Geçerli bir üyeliğiniz bulunmuyor.'
          : 'QR kod oluşturulamadı. Birkaç saniye sonra tekrar deneyin.',
      )
    } finally {
      setIssuing(false)
    }
  }

  // Book Class Session
  async function handleBookSession(sessionId: string) {
    setBookingLoading(true)
    setActionMessage(null)
    try {
      const res = await api<ClassBooking>(`/api/v1/me/classes/sessions/${sessionId}/book`, {
        method: 'POST',
      })
      if (res.status === 'CONFIRMED') {
        setActionMessage('🎉 Rezervasyonunuz başarıyla onaylandı!')
      } else {
        setActionMessage(`🟡 Kontenjan dolu olduğu için Yedek #${res.waitlist_position} sırasına eklendiniz. Asil listeden biri iptal ettiğinde otomatik onaylanacaksınız.`)
      }
      await loadClassesData()
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : 'Rezervasyon işlemi tamamlanamadı.')
    } finally {
      setBookingLoading(false)
    }
  }

  // Cancel Class Booking
  async function handleCancelBooking(bookingId: string) {
    if (!confirm('Rezervasyonunuzu iptal etmek istediğinize emin misiniz?')) return
    setBookingLoading(true)
    try {
      await api<ClassBooking>(`/api/v1/me/classes/bookings/${bookingId}/cancel`, {
        method: 'POST',
        body: { cancellation_reason: 'Üye tarafından iptal edildi' },
      })
      setActionMessage('Rezervasyonunuz iptal edildi.')
      await loadClassesData()
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : 'İptal işlemi gerçekleştirilemedi.')
    } finally {
      setBookingLoading(false)
    }
  }

  // Book PT Appointment
  async function handleBookPt(e: React.FormEvent) {
    e.preventDefault()
    setBookingLoading(true)
    try {
      await api<PtAppointment>('/api/v1/me/pt/appointments', {
        method: 'POST',
        body: {
          trainer_user_id: ptTrainerId,
          start_time_utc: new Date(ptStart).toISOString(),
          end_time_utc: new Date(ptEnd).toISOString(),
          notes: ptNotes || null,
        },
      })
      setActionMessage('🏋️ PT randevunuz başarıyla oluşturuldu!')
      setShowPtModal(false)
      await loadClassesData()
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : 'PT randevusu oluşturulamadı.')
    } finally {
      setBookingLoading(false)
    }
  }

  // Cancel PT Appointment
  async function handleCancelPt(appointmentId: string) {
    if (!confirm('PT randevunuzu iptal etmek istediğinize emin misiniz?')) return
    setBookingLoading(true)
    try {
      await api<PtAppointment>(`/api/v1/me/pt/appointments/${appointmentId}/cancel`, {
        method: 'POST',
        body: { cancellation_reason: 'Üye tarafından iptal edildi' },
      })
      setActionMessage('PT randevunuz iptal edildi.')
      await loadClassesData()
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : 'PT iptal edilemedi.')
    } finally {
      setBookingLoading(false)
    }
  }

  async function handleToggleConsent(consentType: string, currentStatus: string) {
    const newStatus = currentStatus === 'GIVEN' ? 'WITHDRAWN' : 'GIVEN'
    setConsentUpdating(consentType)
    try {
      await api('/api/v1/me/consents', {
        method: 'POST',
        body: { consent_type: consentType, status: newStatus },
      })
      const myConsents = await api<MeConsent[]>('/api/v1/me/consents')
      setConsents(myConsents)
    } catch {
      // ignore
    } finally {
      setConsentUpdating(null)
    }
  }

  const activeMembership = memberships.find((m) => m.status === 'ACTIVE')
  const expired = qr !== null && secondsLeft <= 0

  const filteredSessions = classSessions.filter((s) => {
    if (categoryFilter === 'ALL') return true
    return s.class_category === categoryFilter
  })

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 font-sans">
      <div className="mx-auto w-full max-w-lg">
        {/* Header */}
        <header className="mb-4 flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500 font-black text-slate-950 shadow-md shadow-emerald-500/20">
              N
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">
                GymClubNex
              </h1>
              <p className="text-xs text-slate-400">Sporcu Portalı</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {member && (
              <span className="rounded-full bg-emerald-950/80 border border-emerald-800/60 px-3 py-1 text-xs font-semibold text-emerald-400">
                {member.member_number}
              </span>
            )}
            <button
              type="button"
              onClick={() => void signOut()}
              className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
              title="Oturumu Kapat"
            >
              Çıkış
            </button>
          </div>
        </header>

        {actionMessage && (
          <div className="mb-3">
            <Alert variant="success">{actionMessage}</Alert>
          </div>
        )}

        {loading && <LoadingSkeleton rows={5} />}

        {!loading && loadError && (
          <div className="space-y-3">
            <Alert variant="error">{loadError}</Alert>
            <button
              type="button"
              onClick={() => void loadProfile()}
              className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm font-bold text-white hover:bg-slate-700"
            >
              Tekrar dene
            </button>
          </div>
        )}

        {!loading && !loadError && member && (
          <>
            {/* Athlete Profile Card */}
            <section className="mb-4 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <div className="text-base font-bold text-white">
                    {member.first_name} {member.last_name}
                  </div>
                  <div className="text-xs text-slate-400">
                    {session?.email || member.member_number}
                  </div>
                </div>
                <div
                  className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                    activeMembership
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}
                >
                  {activeMembership ? 'Aktif Üye' : 'Abonelik Yok'}
                </div>
              </div>
            </section>

            {/* Navigation Tabs (6 Tabs) */}
            <div className="mb-4 grid grid-cols-6 rounded-xl bg-slate-950/80 p-1 border border-slate-800 text-[11px] font-semibold text-center">
              <button
                type="button"
                onClick={() => setActiveTab('access')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'access' ? 'bg-slate-800 text-white font-bold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Giriş QR
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('classes')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'classes' ? 'bg-slate-800 text-emerald-400 font-bold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                📅 Dersler
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('memberships')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'memberships' ? 'bg-slate-800 text-white font-bold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Paketler
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('history')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'history' ? 'bg-slate-800 text-white font-bold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Geçmiş
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('finance')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'finance' ? 'bg-slate-800 text-white font-bold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Ödemeler
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('preferences')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'preferences' ? 'bg-slate-800 text-white font-bold shadow' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                İletişim
              </button>
            </div>

            {/* TAB 1: ACCESS QR */}
            {activeTab === 'access' && (
              <div>
                {!activeMembership && (
                  <div className="mb-3">
                    <Alert variant="info">
                      Aktif aboneliğiniz görünmüyor. Turnikeden geçiş reddedilebilir.
                    </Alert>
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => void handleIssueQr()}
                  disabled={issuing}
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-4 py-3.5 text-base font-extrabold text-white shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
                >
                  {issuing ? 'Oluşturuluyor…' : 'Giriş QR kodu oluştur'}
                </button>

                {issueError && (
                  <div className="mt-3">
                    <Alert variant="error">{issueError}</Alert>
                  </div>
                )}

                {qr && qrImage && (
                  <div className="mt-5 text-center">
                    <div className="mb-2 flex items-center justify-center gap-2 text-sm font-bold" role="status" aria-live="polite">
                      <span>Kalan süre:</span>
                      <span className={secondsLeft <= 10 ? 'font-extrabold text-red-400' : 'font-extrabold text-amber-400'}>
                        {expired ? 'Süre doldu — yeniden oluşturun' : `${secondsLeft} sn`}
                      </span>
                    </div>

                    <div className={`mb-2 inline-block rounded-2xl bg-white p-3.5 shadow-xl transition-opacity ${expired ? 'opacity-25' : 'opacity-100'}`}>
                      <img src={qrImage} alt="Giriş QR kodu" className="h-48 w-48" />
                    </div>

                    <p className="text-xs leading-relaxed text-slate-400">
                      QR kodunuzu turnikedeki okuyucuya gösterin. Kod 60 saniye geçerlidir.
                    </p>
                  </div>
                )}

                {!qr && (
                  <div className="mt-4">
                    <EmptyState
                      title="Henüz QR kodu oluşturmadınız"
                      description="Turnikeye geldiğinizde kodu oluşturun; güvenli ve dinamik üretilir."
                    />
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: CLASSES & PT BOOKING */}
            {activeTab === 'classes' && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <div className="flex gap-1.5 overflow-x-auto pb-1 text-xs">
                    {['ALL', 'PILATES', 'CARDIO', 'YOGA', 'HIIT', 'CROSSFIT'].map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setCategoryFilter(cat)}
                        className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                          categoryFilter === cat
                            ? 'bg-emerald-500 text-slate-950 font-bold'
                            : 'bg-slate-800 text-slate-400 hover:text-white'
                        }`}
                      >
                        {cat === 'ALL' ? 'Tümü' : cat}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={() => setShowPtModal(true)}
                    className="btn btn-secondary text-xs px-2.5 py-1 shrink-0 text-cyan-400 border-cyan-500/40"
                  >
                    + PT Randevusu
                  </button>
                </div>

                {/* My Active Bookings Banner */}
                {myBookings.filter((b) => b.status === 'CONFIRMED' || b.status === 'WAITLISTED').length > 0 && (
                  <div className="p-3 rounded-xl border border-emerald-500/30 bg-emerald-950/30 space-y-2">
                    <div className="text-xs font-bold text-emerald-400">Aktif Rezervasyonlarım</div>
                    <div className="space-y-1.5">
                      {myBookings
                        .filter((b) => b.status === 'CONFIRMED' || b.status === 'WAITLISTED')
                        .map((b) => (
                          <div key={b.id} className="flex items-center justify-between text-xs bg-slate-900/80 p-2 rounded-lg">
                            <div>
                              <span className="font-semibold text-white">Ders Rezervasyonu</span>
                              {b.status === 'WAITLISTED' ? (
                                <span className="ml-2 text-amber-400 font-bold">🟡 Yedek #{b.waitlist_position}</span>
                              ) : (
                                <span className="ml-2 text-emerald-400 font-bold">🟢 Onaylandı</span>
                              )}
                            </div>
                            <button
                              disabled={bookingLoading}
                              onClick={() => handleCancelBooking(b.id)}
                              className="text-red-400 hover:text-red-300 font-bold"
                            >
                              İptal Et
                            </button>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Class Sessions List */}
                {filteredSessions.length === 0 ? (
                  <EmptyState
                    title="Planlanmış Ders Seansı Yok"
                    description="Yakın zamanda planlanan grup dersi bulunmuyor."
                  />
                ) : (
                  <div className="space-y-3">
                    {filteredSessions.map((s) => {
                      const isFull = s.confirmed_count >= s.capacity
                      const userStatus = s.user_booking_status

                      return (
                        <div
                          key={s.id}
                          className="p-4 rounded-2xl border border-slate-800 bg-slate-900 flex flex-col justify-between relative overflow-hidden"
                        >
                          <div
                            className="absolute top-0 left-0 right-0 h-1"
                            style={{ backgroundColor: s.color_hex || '#10B981' }}
                          />
                          <div>
                            <div className="flex justify-between items-start mb-1">
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase tracking-wider">
                                {s.class_category || 'DERS'}
                              </span>
                              <span className="text-xs font-semibold text-slate-400">
                                {s.confirmed_count} / {s.capacity} Kişi
                              </span>
                            </div>
                            <h3 className="font-bold text-white text-base">{s.class_type_name}</h3>
                            <div className="text-xs text-slate-400 space-y-0.5 my-2">
                              <div>⏰ {formatDateTr(s.start_time_utc)} - {formatTime(s.end_time_utc)}</div>
                              <div>🏋️ Eğitmen: {s.trainer_name || 'Eğitmen'}</div>
                              <div>📍 {s.location_name || 'Ana Şube'} {s.room_name ? `(${s.room_name})` : ''}</div>
                            </div>
                          </div>

                          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                            <div>
                              {userStatus === 'CONFIRMED' && (
                                <span className="text-xs text-emerald-400 font-bold">✓ Rezervasyonunuz Var</span>
                              )}
                              {userStatus === 'WAITLISTED' && (
                                <span className="text-xs text-amber-400 font-bold">🟡 Yedektesiniz (#{s.user_waitlist_position})</span>
                              )}
                              {!userStatus && (
                                <span className={`text-xs font-medium ${isFull ? 'text-amber-400' : 'text-emerald-400'}`}>
                                  {isFull ? `Kontenjan Dolu (${s.waitlist_count} Yedek)` : `${s.capacity - s.confirmed_count} Boş Yer`}
                                </span>
                              )}
                            </div>

                            <div>
                              {!userStatus ? (
                                <button
                                  disabled={bookingLoading}
                                  onClick={() => handleBookSession(s.id)}
                                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                                    isFull
                                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30'
                                      : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-500/20'
                                  }`}
                                >
                                  {isFull ? `Yedek Sıraya Gir (#${s.waitlist_count + 1})` : 'Rezervasyon Yap'}
                                </button>
                              ) : (
                                <span className="text-xs text-slate-500">Kayıtlı</span>
                              )}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* My PT Appointments */}
                {myPtAppointments.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                      Birebir PT Randevularım
                    </h3>
                    <div className="space-y-2">
                      {myPtAppointments.map((pt) => (
                        <div key={pt.id} className="p-3 rounded-xl border border-slate-800 bg-slate-900 flex justify-between items-center text-xs">
                          <div>
                            <div className="font-semibold text-white">Antrenör: {pt.trainer_name || 'Atanmış Antrenör'}</div>
                            <div className="text-slate-400 mt-0.5">⏰ {formatDateTr(pt.start_time_utc)} - {formatTime(pt.end_time_utc)}</div>
                          </div>
                          {pt.status === 'CONFIRMED' && (
                            <button
                              disabled={bookingLoading}
                              onClick={() => handleCancelPt(pt.id)}
                              className="text-red-400 hover:text-red-300 font-bold"
                            >
                              İptal
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: MEMBERSHIPS */}
            {activeTab === 'memberships' && (
              <div className="space-y-4">
                <div>
                  <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                    Abonelik Kayıtları
                  </h3>
                  {memberships.length === 0 ? (
                    <EmptyState
                      title="Kayıtlı abonelik bulunamadı"
                      description="Aktif üyelik tanımlaması için kulüp yetkilisiyle görüşün."
                    />
                  ) : (
                    <div className="space-y-2">
                      {memberships.map((m) => (
                        <div
                          key={m.id}
                          className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
                        >
                          <div>
                            <div className="font-semibold text-slate-200">
                              Başlangıç: {new Date(m.start_date).toLocaleDateString('tr-TR')}
                            </div>
                            <div className="text-slate-400">
                              Bitiş: {m.end_date ? new Date(m.end_date).toLocaleDateString('tr-TR') : 'Süresiz'}
                            </div>
                          </div>
                          <span
                            className={`rounded px-2 py-0.5 font-bold ${
                              m.status === 'ACTIVE'
                                ? 'bg-emerald-500/10 text-emerald-400'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {m.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                    Kullanım Hakları & Cüzdanlar
                  </h3>
                  {(!entitlements || entitlements.wallets.length === 0) ? (
                    <p className="text-xs text-slate-500">Tanımlı özel hak cüzdanı bulunmuyor.</p>
                  ) : (
                    <div className="space-y-2">
                      {entitlements.wallets.map((w) => (
                        <div
                          key={w.wallet_id}
                          className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
                        >
                          <div className="mb-1 flex justify-between font-semibold">
                            <span className="text-slate-200">{w.entitlement_name || w.entitlement_code}</span>
                            <span className="text-cyan-400">{w.remaining} / {w.allocated} Kalan</span>
                          </div>
                          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                            <div
                              className="h-full bg-cyan-500 rounded-full"
                              style={{ width: `${Math.min(100, (w.remaining / Math.max(1, w.allocated)) * 100)}%` }}
                            />
                          </div>
                          {w.expires_at && (
                            <div className="mt-1 text-[10px] text-slate-500">
                              Son Kullanım: {new Date(w.expires_at).toLocaleDateString('tr-TR')}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 4: CHECKIN HISTORY */}
            {activeTab === 'history' && (
              <div>
                <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                  Son Giriş Kayıtları
                </h3>
                {checkins.length === 0 ? (
                  <EmptyState
                    title="Giriş kaydı bulunamadı"
                    description="Turnikeden gerçekleştirdiğiniz geçişler burada listelenir."
                  />
                ) : (
                  <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
                    {checkins.map((c) => (
                      <div
                        key={c.id}
                        className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="h-2 w-2 rounded-full bg-emerald-400" />
                          <div>
                            <div className="font-semibold text-slate-200">
                              {new Date(c.checkin_time).toLocaleString('tr-TR')}
                            </div>
                            <div className="text-[10px] text-slate-500">
                              {c.checkout_time ? `Çıkış: ${new Date(c.checkout_time).toLocaleTimeString('tr-TR')}` : 'Kulüp İçi'}
                            </div>
                          </div>
                        </div>
                        <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] text-slate-300">
                          Başarılı
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB 5: FINANCE */}
            {activeTab === 'finance' && (
              <div className="space-y-4">
                <div>
                  <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                    Faturalar & Belgeler
                  </h3>
                  {invoices.length === 0 ? (
                    <EmptyState
                      title="Fatura bulunamadı"
                      description="Kulüp abonelik faturalarınız burada listelenir."
                    />
                  ) : (
                    <div className="space-y-2">
                      {invoices.map((inv) => (
                        <div
                          key={inv.id}
                          className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
                        >
                          <div>
                            <div className="font-semibold text-slate-200">
                              {inv.invoice_number || 'Fatura Taslağı'}
                            </div>
                            <div className="text-slate-400">
                              {new Date(inv.created_at).toLocaleDateString('tr-TR')}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-white">{formatMinor(inv.total_amount_minor)}</div>
                            <span
                              className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                                inv.status === 'PAID'
                                  ? 'bg-emerald-500/10 text-emerald-400'
                                  : inv.status === 'OPEN'
                                  ? 'bg-amber-500/10 text-amber-400'
                                  : 'bg-slate-800 text-slate-400'
                              }`}
                            >
                              {inv.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                    Ödeme İşlemleri
                  </h3>
                  {payments.length === 0 ? (
                    <p className="text-xs text-slate-500">Kayıtlı ödeme hareketi bulunamadı.</p>
                  ) : (
                    <div className="space-y-2">
                      {payments.map((p) => (
                        <div
                          key={p.id}
                          className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
                        >
                          <div>
                            <div className="font-semibold text-slate-200">{p.method}</div>
                            <div className="text-slate-400">{new Date(p.created_at).toLocaleDateString('tr-TR')}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-emerald-400">{formatMinor(p.amount_minor)}</div>
                            <span className="text-[10px] text-slate-400">{p.status}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* TAB 6: CONSENTS & PREFERENCES */}
            {activeTab === 'preferences' && (
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  İletişim & Gizlilik Tercihleri
                </h3>
                <div className="space-y-3">
                  {[
                    { type: 'MARKETING_SMS', label: 'SMS Bilgilendirmeleri', desc: 'Kampanya ve duyuru SMS mesajları' },
                    { type: 'MARKETING_EMAIL', label: 'E-Posta Bültenleri', desc: 'Etkinlik ve fırsat e-postaları' },
                    { type: 'KVKK_CONSENT', label: 'KVKK Açık Rıza Onayı', desc: 'Kişisel veri işleme ve mevzuat onayı' },
                  ].map((item) => {
                    const found = consents.find((c) => c.consent_type === item.type)
                    const isGiven = found?.status === 'GIVEN'

                    return (
                      <div
                        key={item.type}
                        className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
                      >
                        <div className="max-w-[70%]">
                          <div className="font-semibold text-slate-200">{item.label}</div>
                          <div className="text-[11px] text-slate-400">{item.desc}</div>
                        </div>
                        <button
                          type="button"
                          disabled={consentUpdating === item.type}
                          onClick={() => void handleToggleConsent(item.type, isGiven ? 'GIVEN' : 'WITHDRAWN')}
                          className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                            isGiven
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30'
                              : 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700'
                          }`}
                        >
                          {consentUpdating === item.type ? '…' : isGiven ? 'Açık' : 'Kapalı'}
                        </button>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* PT BOOKING MODAL */}
            {showPtModal && (
              <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
                  <h3 className="text-base font-bold text-white">1-on-1 PT Randevusu Al</h3>
                  <form onSubmit={handleBookPt} className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Antrenör</label>
                      <select
                        value={ptTrainerId}
                        onChange={(e) => setPtTrainerId(e.target.value)}
                        className="input w-full text-xs"
                      >
                        {trainers.map((t) => (
                          <option key={t.id} value={t.user_id}>
                            {t.first_name} {t.last_name} ({t.role})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Başlangıç Zamanı</label>
                      <input
                        type="datetime-local"
                        required
                        value={ptStart}
                        onChange={(e) => setPtStart(e.target.value)}
                        className="input w-full text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Bitiş Zamanı</label>
                      <input
                        type="datetime-local"
                        required
                        value={ptEnd}
                        onChange={(e) => setPtEnd(e.target.value)}
                        className="input w-full text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Hedef & Notlar</label>
                      <input
                        type="text"
                        value={ptNotes}
                        onChange={(e) => setPtNotes(e.target.value)}
                        placeholder="Örn: Sırt & Kol antrenmanı"
                        className="input w-full text-xs"
                      />
                    </div>
                    <div className="flex justify-end gap-2 pt-2">
                      <button
                        type="button"
                        onClick={() => setShowPtModal(false)}
                        className="btn btn-secondary text-xs px-3 py-1.5"
                      >
                        Vazgeç
                      </button>
                      <button
                        type="submit"
                        disabled={bookingLoading}
                        className="btn btn-primary text-xs px-3 py-1.5"
                      >
                        Randevu Oluştur
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

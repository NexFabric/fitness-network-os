import { useCallback, useEffect, useState } from 'react'
import QRCode from 'qrcode'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, LoadingSkeleton } from '../components/ui'
import type { ClassBooking, ClassSession, PtAppointment, TrainerOption } from './classes/types'
import { AccessTab } from './portal/AccessTab'
import { ClassesTab } from './portal/ClassesTab'
import { FinanceTab } from './portal/FinanceTab'
import { HistoryTab } from './portal/HistoryTab'
import { MembershipsTab } from './portal/MembershipsTab'
import { PreferencesTab } from './portal/PreferencesTab'
import {
  TTL_SECONDS,
  type ActiveTab,
  type EntitlementsSummary,
  type IssuedQr,
  type MeCheckin,
  type MeConsent,
  type MeInvoice,
  type MeMember,
  type MePayment,
  type Membership,
} from './portal/types'

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
  const [dsarBusy, setDsarBusy] = useState(false)
  const [dsarMessage, setDsarMessage] = useState<string | null>(null)
  const [eraseBusy, setEraseBusy] = useState(false)
  const [eraseMessage, setEraseMessage] = useState<string | null>(null)

  const [classSessions, setClassSessions] = useState<ClassSession[]>([])
  const [myBookings, setMyBookings] = useState<ClassBooking[]>([])
  const [myPtAppointments, setMyPtAppointments] = useState<PtAppointment[]>([])
  const [trainers, setTrainers] = useState<TrainerOption[]>([])
  const [bookingLoading, setBookingLoading] = useState(false)
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL')

  const [showPtModal, setShowPtModal] = useState(false)
  const [ptTrainerId, setPtTrainerId] = useState('')
  const [ptLocationId, setPtLocationId] = useState('')
  const [ptStart, setPtStart] = useState('')
  const [ptEnd, setPtEnd] = useState('')
  const [ptNotes, setPtNotes] = useState('')

  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

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
        setLoadError('Hesabınız bir üye kaydına bağlı değil. Kulüp resepsiyonuyla iletişime geçin.')
      } else {
        setLoadError('Bilgileriniz yüklenemedi. Birkaç saniye sonra tekrar deneyin.')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const loadClassesData = useCallback(async () => {
    try {
      const [sessionsRes, bookingsRes, ptRes, trainerRes] = await Promise.all([
        api<ClassSession[]>('/api/v1/me/classes/sessions'),
        api<ClassBooking[]>('/api/v1/me/classes/bookings').catch(() => [] as ClassBooking[]),
        api<PtAppointment[]>('/api/v1/me/pt/appointments').catch(() => [] as PtAppointment[]),
        api<TrainerOption[]>('/api/v1/classes/trainers').catch(() => [] as TrainerOption[]),
      ])
      setClassSessions(sessionsRes)
      setMyBookings(bookingsRes)
      setMyPtAppointments(ptRes)
      setTrainers(trainerRes)
      if (trainerRes.length > 0) setPtTrainerId(trainerRes[0].user_id)
      const locId = sessionsRes.find((s) => s.location_id)?.location_id
      if (locId) setPtLocationId(locId)
    } catch {
      // ignore
    }
  }, [])

  const loadTabData = useCallback(
    async (tab: ActiveTab) => {
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
    },
    [loadClassesData],
  )

  useEffect(() => {
    void loadProfile()
  }, [loadProfile])

  useEffect(() => {
    void loadTabData(activeTab)
  }, [activeTab, loadTabData])

  useEffect(() => {
    if (!qr) return
    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [qr])

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
        setActionMessage(
          `🟡 Kontenjan dolu olduğu için Yedek #${res.waitlist_position} sırasına eklendiniz. Asil listeden biri iptal ettiğinde otomatik onaylanacaksınız.`,
        )
      }
      await loadClassesData()
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : 'Rezervasyon işlemi tamamlanamadı.')
    } finally {
      setBookingLoading(false)
    }
  }

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

  async function handleBookPt(e: React.FormEvent) {
    e.preventDefault()
    setBookingLoading(true)
    try {
      await api<PtAppointment>('/api/v1/me/pt/appointments', {
        method: 'POST',
        body: {
          trainer_user_id: ptTrainerId,
          location_id: ptLocationId,
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

  async function handleDsarErasure() {
    if (!confirm('Ad ve iletişim bilgileriniz anonimleştirilecek. Açık fatura varsa talep reddedilir. Devam?')) {
      return
    }
    setEraseBusy(true)
    setEraseMessage(null)
    try {
      await api('/api/v1/me/dsar/erasure', { method: 'POST' })
      setEraseMessage('Silme tamamlandı. Oturum kapatılacak.')
      await signOut()
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        setEraseMessage('Açık fatura nedeniyle silme bekletildi. Fatura kapandıktan sonra tekrar deneyin.')
      } else {
        setEraseMessage(e instanceof ApiError ? e.message : 'Silme başarısız.')
      }
    } finally {
      setEraseBusy(false)
    }
  }

  async function handleDsarExport() {
    setDsarBusy(true)
    setDsarMessage(null)
    try {
      const row = await api<{ download_url?: string | null; created: boolean }>('/api/v1/me/dsar/export', {
        method: 'POST',
      })
      if (row.download_url) {
        window.open(row.download_url, '_blank', 'noopener,noreferrer')
      }
      setDsarMessage(row.created ? 'Paket hazırlandı.' : 'Bugünkü paket yeniden açıldı.')
    } catch (e) {
      setDsarMessage(e instanceof ApiError ? e.message : 'Dışa aktarma başarısız.')
    } finally {
      setDsarBusy(false)
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
    return s.class_type_category === categoryFilter
  })
  const ptLocations = Array.from(
    new Map(
      classSessions
        .filter((s) => s.location_id)
        .map((s) => [s.location_id, s.location_name || s.location_id] as const),
    ).entries(),
  ).map(([id, name]) => ({ id, name }))

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 font-sans">
      <div className="mx-auto w-full max-w-lg">
        <header className="mb-4 flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500 font-black text-slate-950 shadow-md shadow-emerald-500/20">
              N
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">GymClubNex</h1>
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
            <section className="mb-4 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <div className="text-base font-bold text-white">
                    {member.first_name} {member.last_name}
                  </div>
                  <div className="text-xs text-slate-400">{session?.email || member.member_number}</div>
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
                  activeTab === 'classes'
                    ? 'bg-slate-800 text-emerald-400 font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                📅 Dersler
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('memberships')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'memberships'
                    ? 'bg-slate-800 text-white font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Paketler
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('history')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'history'
                    ? 'bg-slate-800 text-white font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Geçmiş
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('finance')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'finance'
                    ? 'bg-slate-800 text-white font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Ödemeler
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('preferences')}
                className={`rounded-lg py-2 transition-colors ${
                  activeTab === 'preferences'
                    ? 'bg-slate-800 text-white font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                İletişim
              </button>
            </div>

            {activeTab === 'access' && (
              <AccessTab
                hasActiveMembership={Boolean(activeMembership)}
                issuing={issuing}
                issueError={issueError}
                qr={qr}
                qrImage={qrImage}
                secondsLeft={secondsLeft}
                expired={expired}
                onIssueQr={handleIssueQr}
              />
            )}
            {activeTab === 'classes' && (
              <ClassesTab
                categoryFilter={categoryFilter}
                filteredSessions={filteredSessions}
                myBookings={myBookings}
                myPtAppointments={myPtAppointments}
                trainers={trainers}
                bookingLoading={bookingLoading}
                showPtModal={showPtModal}
                ptTrainerId={ptTrainerId}
                ptLocationId={ptLocationId}
                ptLocations={ptLocations}
                ptStart={ptStart}
                ptEnd={ptEnd}
                ptNotes={ptNotes}
                onCategoryChange={setCategoryFilter}
                onOpenPtModal={() => setShowPtModal(true)}
                onClosePtModal={() => setShowPtModal(false)}
                onBookSession={(id) => void handleBookSession(id)}
                onCancelBooking={(id) => void handleCancelBooking(id)}
                onCancelPt={(id) => void handleCancelPt(id)}
                onBookPt={(e) => void handleBookPt(e)}
                onPtTrainerChange={setPtTrainerId}
                onPtLocationChange={setPtLocationId}
                onPtStartChange={setPtStart}
                onPtEndChange={setPtEnd}
                onPtNotesChange={setPtNotes}
              />
            )}
            {activeTab === 'memberships' && (
              <MembershipsTab memberships={memberships} entitlements={entitlements} />
            )}
            {activeTab === 'history' && <HistoryTab checkins={checkins} />}
            {activeTab === 'finance' && <FinanceTab invoices={invoices} payments={payments} />}
            {activeTab === 'preferences' && (
              <PreferencesTab
                consents={consents}
                dsarBusy={dsarBusy}
                dsarMessage={dsarMessage}
                eraseBusy={eraseBusy}
                eraseMessage={eraseMessage}
                consentUpdating={consentUpdating}
                onDsarExport={handleDsarExport}
                onDsarErasure={handleDsarErasure}
                onToggleConsent={handleToggleConsent}
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}

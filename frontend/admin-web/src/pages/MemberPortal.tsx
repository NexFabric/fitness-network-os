import { useCallback, useEffect, useState } from 'react'
import QRCode from 'qrcode'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, EmptyState, LoadingSkeleton } from '../components/ui'

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

type ActiveTab = 'access' | 'memberships' | 'history' | 'finance' | 'preferences'

export default function MemberPortal() {
  const { session } = useAuth()

  const [activeTab, setActiveTab] = useState<ActiveTab>('access')
  const [member, setMember] = useState<MeMember | null>(null)
  const [memberships, setMemberships] = useState<Membership[]>([])
  const [entitlements, setEntitlements] = useState<EntitlementsSummary | null>(null)
  const [checkins, setCheckins] = useState<MeCheckin[]>([])
  const [invoices, setInvoices] = useState<MeInvoice[]>([])
  const [payments, setPayments] = useState<MePayment[]>([])
  const [consents, setConsents] = useState<MeConsent[]>([])

  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

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

  const loadTabData = useCallback(async (tab: ActiveTab) => {
    try {
      if (tab === 'history') {
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
      // Handled silently
    }
  }, [])

  useEffect(() => {
    void loadProfile()
  }, [loadProfile])

  useEffect(() => {
    if (activeTab !== 'access') {
      void loadTabData(activeTab)
    }
  }, [activeTab, loadTabData])

  useEffect(() => {
    if (!qr) return
    const tick = () => {
      setSecondsLeft(
        Math.max(
          0,
          Math.round((new Date(qr.exp).getTime() - Date.now()) / 1000),
        ),
      )
    }
    tick()
    const timer = setInterval(tick, 1000)
    return () => clearInterval(timer)
  }, [qr])

  async function handleIssueQr() {
    setIssuing(true)
    setIssueError(null)
    try {
      const issued = await api<IssuedQr>('/api/v1/access/qr/issue-self', {
        method: 'POST',
        body: { ttl_seconds: TTL_SECONDS },
      })
      const dataUrl = await QRCode.toDataURL(issued.token, {
        width: 240,
        margin: 1,
      })
      setQr(issued)
      setQrImage(dataUrl)
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setIssueError('Bu işlem için yetkiniz yok.')
      } else if (err instanceof ApiError && err.status === 404) {
        setIssueError('Üye kaydınız bulunamadı. Resepsiyonla iletişime geçin.')
      } else {
        setIssueError(
          'QR kodu oluşturulamadı. Birkaç saniye sonra tekrar deneyin.',
        )
      }
    } finally {
      setIssuing(false)
    }
  }

  async function handleToggleConsent(consentType: string, currentStatus: string) {
    const nextStatus = currentStatus === 'GIVEN' ? 'WITHDRAWN' : 'GIVEN'
    setConsentUpdating(consentType)
    try {
      await api<MeConsent>('/api/v1/me/consents', {
        method: 'POST',
        body: {
          consent_type: consentType,
          document_version: 'v1.0',
          status: nextStatus,
        },
      })
      await loadTabData('preferences')
    } catch {
      alert('Tercih güncellenemedi. Lütfen tekrar deneyin.')
    } finally {
      setConsentUpdating(null)
    }
  }

  const activeMembership = memberships.find((m) => m.status === 'ACTIVE')
  const totalRemaining =
    entitlements?.wallets.reduce((sum, w) => sum + w.remaining, 0) ?? 0
  const totalAllocated =
    entitlements?.wallets.reduce((sum, w) => sum + w.allocated, 0) ?? 0
  const expired = qr !== null && secondsLeft <= 0

  const formatMinor = (minor: number) =>
    (minor / 100).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ₺'

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-8 text-slate-100 font-sans">
      <div className="w-full max-w-lg rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        <header className="mb-4 flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 text-xl font-extrabold text-white">
              N
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">
                GymClubNex
              </h1>
              <p className="text-xs text-slate-400">Sporcu Portalı</p>
            </div>
          </div>
          {member && (
            <span className="rounded-full bg-emerald-950/80 border border-emerald-800/60 px-3 py-1 text-xs font-semibold text-emerald-400">
              {member.member_number}
            </span>
          )}
        </header>

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

              <div className="flex justify-between border-t border-slate-800/80 pt-2 text-xs">
                <div>
                  <span className="text-slate-400">Abonelik Durumu: </span>
                  <span className="font-semibold text-slate-200">
                    {activeMembership ? 'Geçerli' : 'Yenileme Gerekli'}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-slate-400">Kalan Hak: </span>
                  <span className="font-bold text-cyan-400">
                    {entitlements && entitlements.wallets.length > 0
                      ? `${totalRemaining} / ${totalAllocated}`
                      : 'Sınırsız / Tanımsız'}
                  </span>
                </div>
              </div>
            </section>

            {/* Navigation Tabs */}
            <div className="mb-4 flex rounded-xl bg-slate-950/80 p-1 border border-slate-800 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setActiveTab('access')}
                className={`flex-1 rounded-lg py-2 transition-colors ${
                  activeTab === 'access'
                    ? 'bg-slate-800 text-white font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Giriş QR
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('memberships')}
                className={`flex-1 rounded-lg py-2 transition-colors ${
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
                className={`flex-1 rounded-lg py-2 transition-colors ${
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
                className={`flex-1 rounded-lg py-2 transition-colors ${
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
                className={`flex-1 rounded-lg py-2 transition-colors ${
                  activeTab === 'preferences'
                    ? 'bg-slate-800 text-white font-bold shadow'
                    : 'text-slate-400 hover:text-slate-200'
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
                    <div
                      className="mb-2 flex items-center justify-center gap-2 text-sm font-bold"
                      role="status"
                      aria-live="polite"
                    >
                      <span>Kalan süre:</span>
                      <span
                        className={
                          secondsLeft <= 10
                            ? 'font-extrabold text-red-400'
                            : 'font-extrabold text-amber-400'
                        }
                      >
                        {expired
                          ? 'Süre doldu — yeniden oluşturun'
                          : `${secondsLeft} sn`}
                      </span>
                    </div>

                    <div
                      className={`mb-2 inline-block rounded-2xl bg-white p-3.5 shadow-xl transition-opacity ${
                        expired ? 'opacity-25' : 'opacity-100'
                      }`}
                    >
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

            {/* TAB 2: MEMBERSHIPS & WALLETS */}
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

            {/* TAB 3: CHECKIN HISTORY */}
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

            {/* TAB 4: FINANCE (INVOICES & PAYMENTS) */}
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

            {/* TAB 5: CONSENTS & PREFERENCES */}
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
          </>
        )}
      </div>
    </div>
  )
}

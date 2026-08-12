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

type IssuedQr = {
  token: string
  jti: string
  exp: string
}

const TTL_SECONDS = 60

/**
 * Athlete self-service.
 *
 * Everything is resolved from the caller's own session: the QR comes from
 * POST /access/qr/issue-self, whose request schema accepts no member_id at all,
 * and the membership/entitlement figures come from /me/*. The page cannot
 * address another member even if the request is edited.
 *
 * Uses the shared api client rather than raw fetch so the API base URL,
 * X-Tenant-ID, CSRF token and 401 handling all come from one place.
 */
export default function MemberPortal() {
  const { session } = useAuth()

  const [member, setMember] = useState<MeMember | null>(null)
  const [memberships, setMemberships] = useState<Membership[]>([])
  const [entitlements, setEntitlements] = useState<EntitlementsSummary | null>(
    null,
  )
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [qr, setQr] = useState<IssuedQr | null>(null)
  const [qrImage, setQrImage] = useState<string | null>(null)
  const [issuing, setIssuing] = useState(false)
  const [issueError, setIssueError] = useState<string | null>(null)
  const [secondsLeft, setSecondsLeft] = useState(0)

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

  useEffect(() => {
    void loadProfile()
  }, [loadProfile])

  // Countdown follows the token's real expiry rather than a fixed 60 counted
  // from the click, so clock skew or a slow response cannot show a valid-looking
  // code that the turnstile will reject.
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
      // Rendered locally — the access token must never reach a third party.
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

  const activeMembership = memberships.find((m) => m.status === 'ACTIVE')
  const totalRemaining =
    entitlements?.wallets.reduce((sum, w) => sum + w.remaining, 0) ?? 0
  const totalAllocated =
    entitlements?.wallets.reduce((sum, w) => sum + w.allocated, 0) ?? 0
  const expired = qr !== null && secondsLeft <= 0

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-8 text-slate-100 font-sans">
      <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        <header className="mb-6 flex items-center justify-between border-b border-slate-800 pb-4">
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
        </header>

        {loading && <LoadingSkeleton rows={4} />}

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
            <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="mb-3">
                <div className="text-base font-bold text-white">
                  {member.first_name} {member.last_name}
                </div>
                <div className="text-xs text-slate-400">
                  {member.member_number}
                  {session?.email && ` · ${session.email}`}
                </div>
              </div>

              <div className="flex justify-between text-xs">
                <div>
                  <div className="text-slate-400">Abonelik</div>
                  <div
                    className={
                      activeMembership
                        ? 'font-bold text-emerald-400'
                        : 'font-bold text-amber-400'
                    }
                  >
                    {activeMembership ? 'Aktif' : 'Aktif abonelik yok'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-slate-400">Kalan giriş hakkı</div>
                  <div className="font-bold text-sky-400">
                    {entitlements && entitlements.wallets.length > 0
                      ? `${totalRemaining} / ${totalAllocated}`
                      : '—'}
                  </div>
                </div>
              </div>
            </section>

            {!activeMembership && (
              <Alert variant="info">
                Aktif aboneliğiniz görünmüyor. Turnikeden geçiş reddedilebilir.
              </Alert>
            )}

            <button
              type="button"
              onClick={() => void handleIssueQr()}
              disabled={issuing}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-4 py-4 text-base font-extrabold text-white shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
            >
              {issuing ? 'Oluşturuluyor…' : 'Giriş QR kodu oluştur'}
            </button>

            {issueError && (
              <div className="mt-3">
                <Alert variant="error">{issueError}</Alert>
              </div>
            )}

            {qr && qrImage && (
              <div className="mt-6 text-center">
                <div
                  className="mb-3 flex items-center justify-center gap-2 text-sm font-bold"
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
                  className={`mb-2 inline-block rounded-2xl bg-white p-4 shadow-xl transition-opacity ${
                    expired ? 'opacity-30' : 'opacity-100'
                  }`}
                >
                  <img src={qrImage} alt="Giriş QR kodu" className="h-52 w-52" />
                </div>

                <p className="text-xs leading-relaxed text-slate-500">
                  QR kodunuzu turnikedeki okuyucuya gösterin. Kod tek
                  kullanımlıktır.
                </p>
              </div>
            )}

            {!qr && (
              <div className="mt-6">
                <EmptyState
                  title="Henüz QR kodu oluşturmadınız"
                  description="Turnikeye geldiğinizde kodu oluşturun; 60 saniye geçerlidir."
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

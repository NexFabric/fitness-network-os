import { useCallback, useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import { formatMinor } from '../pages/Plans'
import { Alert } from './ui'

export type Membership = {
  id: string
  member_id: string
  plan_version_id: string
  status: string
  start_date: string
  end_date: string | null
  current_period_end: string | null
  canceled_at: string | null
  frozen_until: string | null
}

type PlanVersionOption = {
  id: string
  plan_id: string
  version: number
  price_amount_minor: number
  currency: string
  billing_cycle_months: number
}

type PlanOption = {
  id: string
  name: string
}

type PendingAction = {
  membership: Membership
  kind: 'cancel' | 'expire' | 'past_due'
}

const STATUS_LABELS: Record<string, string> = {
  ACTIVE: 'Aktif',
  FROZEN: 'Dondurulmuş',
  CANCELED: 'İptal edildi',
  CANCELLED: 'İptal edildi',
  EXPIRED: 'Süresi doldu',
  PAST_DUE: 'Ödeme gecikti',
  PENDING: 'Beklemede',
}

function statusClass(status: string): string {
  if (status === 'ACTIVE') {
    return 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20'
  }
  if (status === 'FROZEN') {
    return 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/20'
  }
  if (status === 'PAST_DUE') {
    return 'bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20'
  }
  return 'bg-slate-700 text-slate-300'
}

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'Bu işlem için yetkiniz yok.'
    if (e.status === 400) return e.message
    return `${e.status}: ${e.message}`
  }
  if (e instanceof Error) return e.message
  return fallback
}

function today(): string {
  return new Date().toISOString().split('T')[0]
}

export default function MemberMemberships({ memberId }: { memberId: string }) {
  const [memberships, setMemberships] = useState<Membership[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  const [freezing, setFreezing] = useState<string | null>(null)
  const [freezeReason, setFreezeReason] = useState('')
  const [expectedEndDate, setExpectedEndDate] = useState('')

  const [canceling, setCanceling] = useState<string | null>(null)
  const [cancelReason, setCancelReason] = useState('')
  const [cancelDate, setCancelDate] = useState(today())

  // Irreversible transitions are confirmed before they run.
  const [pending, setPending] = useState<PendingAction | null>(null)

  // Only published versions can be sold, so the picker asks the API for those
  // rather than filtering a full catalogue client-side.
  const [planVersions, setPlanVersions] = useState<PlanVersionOption[]>([])
  const [plans, setPlans] = useState<PlanOption[]>([])
  const [starting, setStarting] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState('')

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true)
    try {
      const data = await api<Membership[]>(`/api/v1/members/${memberId}/memberships`)
      setMemberships(data)
      setError(null)
    } catch (e) {
      setError(formatApiError(e, 'Abonelikler yüklenemedi'))
    } finally {
      if (!opts?.silent) setLoading(false)
    }
  }, [memberId])

  const loadCatalogue = useCallback(async () => {
    try {
      const [versionRows, planRows] = await Promise.all([
        api<PlanVersionOption[]>('/api/v1/plans/versions?published_only=true'),
        api<PlanOption[]>('/api/v1/plans'),
      ])
      setPlanVersions(versionRows)
      setPlans(planRows)
    } catch {
      // A caller without memberships:read simply gets no picker; the list above
      // already surfaced the real error.
      setPlanVersions([])
    }
  }, [])

  useEffect(() => {
    void load()
    void loadCatalogue()
  }, [load, loadCatalogue])

  async function run(
    membershipId: string,
    path: string,
    successText: string,
    body?: Record<string, unknown>,
  ) {
    setBusy(membershipId)
    setMessage(null)
    setError(null)
    try {
      await api(`/api/v1/memberships/${membershipId}/${path}`, {
        method: 'POST',
        ...(body ? { body } : {}),
      })
      setMessage(successText)
      await load({ silent: true })
      return true
    } catch (e) {
      // Inline, never a browser dialog: an alert() blocks the page and loses
      // the server's reason for refusing.
      setError(formatApiError(e, 'İşlem tamamlanamadı'))
      return false
    } finally {
      setBusy(null)
    }
  }

  async function handleStart() {
    if (!selectedVersion) {
      setError('Önce yayımlanmış bir plan sürümü seçin.')
      return
    }
    setStarting(true)
    setError(null)
    setMessage(null)
    try {
      await api('/api/v1/memberships', {
        method: 'POST',
        body: { member_id: memberId, plan_version_id: selectedVersion },
      })
      setMessage('Abonelik başlatıldı.')
      setSelectedVersion('')
      await load({ silent: true })
    } catch (e) {
      setError(formatApiError(e, 'Abonelik başlatılamadı'))
    } finally {
      setStarting(false)
    }
  }

  async function handleFreeze(m: Membership) {
    if (!freezeReason.trim()) {
      setError('Dondurma sebebi gereklidir.')
      return
    }
    const ok = await run(m.id, 'freeze', 'Abonelik donduruldu.', {
      start_date: today(),
      reason: freezeReason.trim(),
      expected_end_date: expectedEndDate || undefined,
    })
    if (ok) {
      setFreezing(null)
      setFreezeReason('')
      setExpectedEndDate('')
    }
  }

  async function handleCancel(m: Membership) {
    if (!cancelReason.trim()) {
      setError('İptal sebebi gereklidir.')
      return
    }
    const ok = await run(m.id, 'cancel', 'Abonelik iptal edildi.', {
      effective_date: cancelDate || today(),
      reason: cancelReason.trim(),
    })
    if (ok) {
      setCanceling(null)
      setCancelReason('')
      setCancelDate(today())
    }
  }

  async function confirmPending() {
    if (!pending) return
    const { membership, kind } = pending
    setPending(null)
    if (kind === 'expire') {
      await run(membership.id, 'expire', 'Abonelik süresi dolmuş olarak işaretlendi.')
    } else if (kind === 'past_due') {
      await run(membership.id, 'past-due', 'Abonelik ödemesi gecikmiş olarak işaretlendi.')
    }
  }

  if (loading) {
    return <p className="mt-4 text-sm text-slate-400">Abonelikler yükleniyor…</p>
  }

  return (
    <div className="mt-4 space-y-4">
      {error && <Alert variant="error">{error}</Alert>}
      {message && <Alert variant="success">{message}</Alert>}

      <div className="rounded-lg border border-slate-700 bg-slate-800/40 p-4">
        <p className="text-sm font-semibold text-slate-200">Abonelik başlat</p>
        {planVersions.length === 0 ? (
          <p className="mt-2 text-xs text-slate-400">
            Yayımlanmış plan sürümü yok. Planlar sayfasından bir sürüm ekleyip
            yayımlayın.
          </p>
        ) : (
          <div className="mt-3 flex flex-wrap items-end gap-2">
            <div className="min-w-[220px] flex-1">
              <label htmlFor={`start_plan_${memberId}`} className="label-text">
                Plan sürümü
              </label>
              <select
                id={`start_plan_${memberId}`}
                value={selectedVersion}
                onChange={(e) => setSelectedVersion(e.target.value)}
                className="input-field py-1 text-sm"
                disabled={starting}
              >
                <option value="">Seçin…</option>
                {planVersions.map((v) => (
                  <option key={v.id} value={v.id}>
                    {plans.find((p) => p.id === v.plan_id)?.name ?? 'Plan'} v{v.version} —{' '}
                    {formatMinor(v.price_amount_minor, v.currency)} / {v.billing_cycle_months} ay
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              className="btn-primary"
              onClick={() => void handleStart()}
              disabled={starting}
            >
              {starting ? 'Başlatılıyor…' : 'Başlat'}
            </button>
          </div>
        )}
      </div>

      {memberships.length === 0 ? (
        <p className="text-sm text-slate-500">Bu üyeye ait abonelik bulunmuyor.</p>
      ) : (
        memberships.map((m) => {
          const working = busy === m.id
          return (
            <div key={m.id} className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
              <div className="mb-2 flex items-start justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    Plan:{' '}
                    <span className="font-mono text-xs">
                      {m.plan_version_id.substring(0, 8)}…
                    </span>
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Başlangıç: {m.start_date}
                    {m.end_date ? ` | Bitiş: ${m.end_date}` : ''}
                    {m.frozen_until ? ` | Dondurma bitişi: ${m.frozen_until}` : ''}
                  </p>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusClass(m.status)}`}
                >
                  {STATUS_LABELS[m.status] ?? m.status}
                </span>
              </div>

              <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-700 pt-4">
                {m.status === 'ACTIVE' && freezing !== m.id && canceling !== m.id && (
                  <>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => setFreezing(m.id)}
                      disabled={working}
                    >
                      Dondur
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() =>
                        void run(
                          m.id,
                          'renew',
                          'Abonelik aynı planla yenilendi.',
                          {
                            // No plan catalogue endpoint exists yet, so renewal
                            // stays on the current plan version rather than
                            // inventing a plan picker.
                            next_plan_version_id: m.plan_version_id,
                            renewal_date: today(),
                          },
                        )
                      }
                      disabled={working}
                    >
                      Aynı planla yenile
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => setPending({ membership: m, kind: 'past_due' })}
                      disabled={working}
                    >
                      Ödeme gecikti
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => setPending({ membership: m, kind: 'expire' })}
                      disabled={working}
                    >
                      Süresi doldu
                    </button>
                    <button
                      type="button"
                      className="btn-secondary text-rose-300"
                      onClick={() => setCanceling(m.id)}
                      disabled={working}
                    >
                      İptal et
                    </button>
                  </>
                )}

                {freezing === m.id && (
                  <div className="flex w-full flex-wrap items-end gap-2">
                    <div className="min-w-[180px] flex-1">
                      <label htmlFor={`freeze_reason_${m.id}`} className="label-text">
                        Dondurma sebebi <span className="text-teal-500">*</span>
                      </label>
                      <input
                        id={`freeze_reason_${m.id}`}
                        type="text"
                        value={freezeReason}
                        onChange={(e) => setFreezeReason(e.target.value)}
                        className="input-field py-1 text-sm"
                      />
                    </div>
                    <div>
                      <label htmlFor={`freeze_end_${m.id}`} className="label-text">
                        Beklenen bitiş
                      </label>
                      <input
                        id={`freeze_end_${m.id}`}
                        type="date"
                        value={expectedEndDate}
                        onChange={(e) => setExpectedEndDate(e.target.value)}
                        className="input-field py-1 text-sm"
                      />
                    </div>
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={() => void handleFreeze(m)}
                      disabled={working}
                    >
                      {working ? 'Donduruluyor…' : 'Onayla'}
                    </button>
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={() => {
                        setFreezing(null)
                        setFreezeReason('')
                        setExpectedEndDate('')
                      }}
                    >
                      Vazgeç
                    </button>
                  </div>
                )}

                {canceling === m.id && (
                  <div className="flex w-full flex-wrap items-end gap-2">
                    <div className="min-w-[180px] flex-1">
                      <label htmlFor={`cancel_reason_${m.id}`} className="label-text">
                        İptal sebebi <span className="text-teal-500">*</span>
                      </label>
                      <input
                        id={`cancel_reason_${m.id}`}
                        type="text"
                        value={cancelReason}
                        onChange={(e) => setCancelReason(e.target.value)}
                        className="input-field py-1 text-sm"
                      />
                    </div>
                    <div>
                      <label htmlFor={`cancel_date_${m.id}`} className="label-text">
                        Geçerlilik tarihi
                      </label>
                      <input
                        id={`cancel_date_${m.id}`}
                        type="date"
                        value={cancelDate}
                        onChange={(e) => setCancelDate(e.target.value)}
                        className="input-field py-1 text-sm"
                      />
                    </div>
                    <button
                      type="button"
                      className="btn-danger"
                      onClick={() => void handleCancel(m)}
                      disabled={working}
                    >
                      {working ? 'İptal ediliyor…' : 'İptali onayla'}
                    </button>
                    <button
                      type="button"
                      className="btn-ghost"
                      onClick={() => {
                        setCanceling(null)
                        setCancelReason('')
                      }}
                    >
                      Vazgeç
                    </button>
                  </div>
                )}

                {m.status === 'FROZEN' && (
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => void run(m.id, 'unfreeze', 'Dondurma kaldırıldı.')}
                    disabled={working}
                  >
                    {working ? 'İşleniyor…' : 'Dondurmayı kaldır'}
                  </button>
                )}

                {m.status === 'PAST_DUE' && (
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setPending({ membership: m, kind: 'expire' })}
                    disabled={working}
                  >
                    Süresi doldu
                  </button>
                )}
              </div>
            </div>
          )
        })
      )}

      {pending && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="membership-confirm-heading"
        >
          <div className="card w-full max-w-md">
            <h2
              id="membership-confirm-heading"
              className="text-base font-semibold text-slate-100"
            >
              {pending.kind === 'expire'
                ? 'Abonelik süresi dolmuş sayılsın mı?'
                : 'Ödeme gecikmiş olarak işaretlensin mi?'}
            </h2>
            <p className="mt-2 text-sm text-slate-400">
              {pending.kind === 'expire'
                ? 'Üye bu abonelikle giriş yapamaz hale gelir ve bu durum geri alınamaz — yeniden erişim için yeni bir abonelik gerekir.'
                : 'Abonelik ödeme bekleyen duruma geçer. Girişler tahsilat kurallarınıza göre kısıtlanabilir.'}
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setPending(null)}>
                Vazgeç
              </button>
              <button
                type="button"
                className={pending.kind === 'expire' ? 'btn-danger' : 'btn-primary'}
                onClick={() => void confirmPending()}
              >
                Onayla
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, formatApiError } from '../api/client'
import { Alert, EmptyState, LoadingSkeleton, PageHeader, StatusBadge } from '../components/ui'

type Plan = {
  id: string
  name: string
  description: string | null
  is_active: boolean
}

type PlanVersion = {
  id: string
  plan_id: string
  version: number
  price_amount_minor: number
  currency: string
  billing_cycle_months: number
  is_published: boolean
}

/**
 * "499,90" → 49990 kuruş. Parsed as digits, never via parseFloat: money that
 * round-trips through a float is money that eventually loses a kuruş.
 */
export function priceToMinor(input: string): number | null {
  const trimmed = input.trim().replace(/\s/g, '').replace(',', '.')
  if (!/^\d+(\.\d{1,2})?$/.test(trimmed)) return null
  const [whole, frac = ''] = trimmed.split('.')
  const padded = (frac + '00').slice(0, 2)
  return Number(whole) * 100 + Number(padded)
}

export function formatMinor(minor: number, currency: string): string {
  const sign = minor < 0 ? '-' : ''
  const abs = Math.abs(minor)
  return `${sign}${Math.floor(abs / 100)},${String(abs % 100).padStart(2, '0')} ${currency}`
}

export default function Plans() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [versions, setVersions] = useState<PlanVersion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const [planName, setPlanName] = useState('')
  const [planDescription, setPlanDescription] = useState('')
  const [creatingPlan, setCreatingPlan] = useState(false)
  const [planError, setPlanError] = useState<string | null>(null)

  const [versionPlanId, setVersionPlanId] = useState('')
  const [price, setPrice] = useState('')
  const [cycle, setCycle] = useState('1')
  const [creatingVersion, setCreatingVersion] = useState(false)
  const [versionError, setVersionError] = useState<string | null>(null)

  const [publishing, setPublishing] = useState<string | null>(null)
  const [confirmPublish, setConfirmPublish] = useState<PlanVersion | null>(null)

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) {
      setLoading(true)
      setError(null)
    }
    try {
      const [planRows, versionRows] = await Promise.all([
        api<Plan[]>('/api/v1/plans'),
        api<PlanVersion[]>('/api/v1/plans/versions'),
      ])
      setPlans(planRows)
      setVersions(versionRows)
      setError(null)
    } catch (e) {
      setError(formatApiError(e, 'Planlar yüklenemedi'))
    } finally {
      if (!opts?.silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleCreatePlan(e: FormEvent) {
    e.preventDefault()
    setPlanError(null)
    setMessage(null)
    if (!planName.trim()) {
      setPlanError('Plan adı gereklidir.')
      return
    }
    setCreatingPlan(true)
    try {
      await api<Plan>('/api/v1/plans', {
        method: 'POST',
        body: { name: planName.trim(), description: planDescription.trim() || null },
      })
      setPlanName('')
      setPlanDescription('')
      setMessage('Plan oluşturuldu. Satışa açmak için bir sürüm ekleyip yayımlayın.')
      await load({ silent: true })
    } catch (err) {
      setPlanError(formatApiError(err, 'Plan oluşturulamadı'))
    } finally {
      setCreatingPlan(false)
    }
  }

  async function handleCreateVersion(e: FormEvent) {
    e.preventDefault()
    setVersionError(null)
    setMessage(null)

    if (!versionPlanId) {
      setVersionError('Plan seçin.')
      return
    }
    const minor = priceToMinor(price)
    if (minor === null) {
      setVersionError('Fiyatı 499,90 biçiminde girin.')
      return
    }
    const months = Number(cycle)
    if (!Number.isInteger(months) || months < 1) {
      setVersionError('Fatura döngüsü en az 1 ay olmalıdır.')
      return
    }

    setCreatingVersion(true)
    try {
      const created = await api<PlanVersion>(`/api/v1/plans/${versionPlanId}/versions`, {
        method: 'POST',
        body: { price_amount_minor: minor, billing_cycle_months: months },
      })
      setPrice('')
      setMessage(`Sürüm ${created.version} taslak olarak oluşturuldu.`)
      await load({ silent: true })
    } catch (err) {
      setVersionError(formatApiError(err, 'Sürüm oluşturulamadı'))
    } finally {
      setCreatingVersion(false)
    }
  }

  async function handlePublish(pv: PlanVersion) {
    setConfirmPublish(null)
    setPublishing(pv.id)
    setMessage(null)
    setError(null)
    try {
      await api(`/api/v1/plans/versions/${pv.id}/publish`, { method: 'POST' })
      setMessage(`Sürüm ${pv.version} yayımlandı ve artık satılabilir.`)
      await load({ silent: true })
    } catch (err) {
      setError(formatApiError(err, 'Sürüm yayımlanamadı'))
    } finally {
      setPublishing(null)
    }
  }

  const planName_ = (id: string) => plans.find((p) => p.id === id)?.name ?? '—'

  return (
    <div>
      <PageHeader
        title="Planlar"
        subtitle="Üyelik ürünleri — abonelik yalnızca yayımlanmış bir sürümle başlatılabilir"
      />

      {error && (
        <div className="mt-6">
          <Alert onRetry={() => void load()}>{error}</Alert>
        </div>
      )}
      {message && (
        <div className="mt-6">
          <Alert variant="success">{message}</Alert>
        </div>
      )}

      <section className="card mt-6" aria-labelledby="create-plan-heading">
        <div className="card-header">
          <h2 id="create-plan-heading" className="text-base font-semibold text-slate-100">
            Plan oluştur
          </h2>
        </div>
        <form className="mt-4 grid gap-4 sm:grid-cols-3" onSubmit={handleCreatePlan} noValidate>
          <div>
            <label htmlFor="plan_name" className="label-text">
              İsim <span className="text-teal-500">*</span>
            </label>
            <input
              id="plan_name"
              type="text"
              required
              maxLength={255}
              value={planName}
              onChange={(e) => setPlanName(e.target.value)}
              className="input-field"
              disabled={creatingPlan}
              placeholder="Aylık Sınırsız"
            />
          </div>
          <div>
            <label htmlFor="plan_description" className="label-text">
              Açıklama
            </label>
            <input
              id="plan_description"
              type="text"
              maxLength={2000}
              value={planDescription}
              onChange={(e) => setPlanDescription(e.target.value)}
              className="input-field"
              disabled={creatingPlan}
            />
          </div>
          <div className="flex items-end">
            <button type="submit" className="btn-primary w-full" disabled={creatingPlan}>
              {creatingPlan ? 'Oluşturuluyor…' : 'Plan oluştur'}
            </button>
          </div>
          {planError && (
            <div className="sm:col-span-3">
              <Alert variant="error">{planError}</Alert>
            </div>
          )}
        </form>
      </section>

      <section className="card mt-6" aria-labelledby="create-version-heading">
        <div className="card-header">
          <h2 id="create-version-heading" className="text-base font-semibold text-slate-100">
            Sürüm ekle
          </h2>
        </div>
        <p className="mt-2 text-sm text-slate-400">
          Sürüm önce taslaktır. Yayımlandıktan sonra fiyatı değiştirilemez —
          satılmış abonelikler o fiyata bağlıdır; değişiklik için yeni sürüm açın.
        </p>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-4"
          onSubmit={handleCreateVersion}
          noValidate
        >
          <div>
            <label htmlFor="version_plan" className="label-text">
              Plan <span className="text-teal-500">*</span>
            </label>
            <select
              id="version_plan"
              value={versionPlanId}
              onChange={(e) => setVersionPlanId(e.target.value)}
              className="input-field"
              disabled={creatingVersion || plans.length === 0}
            >
              <option value="">Seçin…</option>
              {plans.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="version_price" className="label-text">
              Fiyat (TRY) <span className="text-teal-500">*</span>
            </label>
            <input
              id="version_price"
              type="text"
              inputMode="decimal"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="input-field"
              disabled={creatingVersion}
              placeholder="499,90"
            />
          </div>
          <div>
            <label htmlFor="version_cycle" className="label-text">
              Fatura döngüsü (ay)
            </label>
            <input
              id="version_cycle"
              type="number"
              min={1}
              max={60}
              value={cycle}
              onChange={(e) => setCycle(e.target.value)}
              className="input-field"
              disabled={creatingVersion}
            />
          </div>
          <div className="flex items-end">
            <button type="submit" className="btn-primary w-full" disabled={creatingVersion}>
              {creatingVersion ? 'Ekleniyor…' : 'Sürüm ekle'}
            </button>
          </div>
          {versionError && (
            <div className="sm:col-span-4">
              <Alert variant="error">{versionError}</Alert>
            </div>
          )}
        </form>
      </section>

      <section className="card mt-6" aria-labelledby="version-list-heading">
        <div className="card-header">
          <h2 id="version-list-heading" className="text-base font-semibold text-slate-100">
            Sürümler
          </h2>
        </div>
        {loading ? (
          <div className="mt-4">
            <LoadingSkeleton rows={3} />
          </div>
        ) : versions.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              title="Henüz sürüm yok"
              description="Bir plan oluşturup ilk fiyat sürümünü ekleyin."
            />
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2">Plan</th>
                  <th className="px-3 py-2">Sürüm</th>
                  <th className="px-3 py-2">Fiyat</th>
                  <th className="px-3 py-2">Döngü</th>
                  <th className="px-3 py-2">Durum</th>
                  <th className="px-3 py-2 text-right">İşlem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {versions.map((v) => (
                  <tr key={v.id}>
                    <td className="px-3 py-3 text-slate-200">{planName_(v.plan_id)}</td>
                    <td className="px-3 py-3 text-slate-400">v{v.version}</td>
                    <td className="px-3 py-3 font-medium text-slate-200">
                      {formatMinor(v.price_amount_minor, v.currency)}
                    </td>
                    <td className="px-3 py-3 text-slate-400">{v.billing_cycle_months} ay</td>
                    <td className="px-3 py-3">
                      <StatusBadge status={v.is_published ? 'Yayımlandı' : 'Taslak'} />
                    </td>
                    <td className="px-3 py-3 text-right">
                      {v.is_published ? (
                        <span className="text-xs text-slate-500">Satılabilir</span>
                      ) : (
                        <button
                          type="button"
                          className="btn-secondary"
                          onClick={() => setConfirmPublish(v)}
                          disabled={publishing === v.id}
                        >
                          {publishing === v.id ? 'Yayımlanıyor…' : 'Yayımla'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {confirmPublish && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="publish-heading"
        >
          <div className="card w-full max-w-md">
            <h2 id="publish-heading" className="text-base font-semibold text-slate-100">
              Sürüm yayımlansın mı?
            </h2>
            <p className="mt-2 text-sm text-slate-400">
              {planName_(confirmPublish.plan_id)} v{confirmPublish.version} —{' '}
              {formatMinor(confirmPublish.price_amount_minor, confirmPublish.currency)}.
              Yayımlandıktan sonra bu sürüm düzenlenemez ve yayından kaldırılamaz;
              fiyat değişikliği için yeni sürüm açmanız gerekir.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setConfirmPublish(null)}
              >
                Vazgeç
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={() => void handlePublish(confirmPublish)}
              >
                Yayımla
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

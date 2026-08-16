import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { Alert, LoadingSkeleton, PageHeader } from '../components/ui'

type Stage =
  | 'ORG_CREATED'
  | 'TENANT_CONFIGURED'
  | 'LOCATION_CREATED'
  | 'PLANS_DEFINED'
  | 'STAFF_INVITED'
  | 'COMPLETED'

type OnboardingStatus = {
  current_stage: Stage
  step_data: Record<string, unknown>
  is_completed: boolean
  completed_at: string | null
}

const STEPS: { stage: Stage; title: string; hint: string; href?: string }[] = [
  { stage: 'ORG_CREATED', title: 'Organizasyon', hint: 'Kulüp kaydı oluşturuldu.' },
  {
    stage: 'TENANT_CONFIGURED',
    title: 'Salon ayarı',
    hint: 'Temel işletme bilgisi hazır.',
  },
  {
    stage: 'LOCATION_CREATED',
    title: 'Şube',
    hint: 'En az bir şube tanımlayın.',
    href: '/locations',
  },
  {
    stage: 'PLANS_DEFINED',
    title: 'Paketler',
    hint: 'En az bir yayınlanmış üyelik paketi.',
    href: '/plans',
  },
  {
    stage: 'STAFF_INVITED',
    title: 'Personel',
    hint: 'En az bir personel veya yetkili.',
    href: '/staff',
  },
  { stage: 'COMPLETED', title: 'Tamamlandı', hint: 'Kurulum kapatıldı.' },
]

function nextStage(current: Stage): Stage | null {
  const i = STEPS.findIndex((s) => s.stage === current)
  if (i < 0 || i >= STEPS.length - 1) return null
  return STEPS[i + 1].stage
}

export default function Onboarding() {
  const [status, setStatus] = useState<OnboardingStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setError(null)
    try {
      const data = await api<OnboardingStatus>('/api/v1/onboarding/status')
      setStatus(data)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Kurulum durumu alınamadı')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function advance() {
    if (!status) return
    const next = nextStage(status.current_stage)
    if (!next) return
    setBusy(true)
    setError(null)
    try {
      const data = await api<OnboardingStatus>('/api/v1/onboarding/advance', {
        method: 'POST',
        body: { next_stage: next, stage_data: {} },
      })
      setStatus(data)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Aşama ilerletilemedi')
    } finally {
      setBusy(false)
    }
  }

  const currentIndex = status
    ? STEPS.findIndex((s) => s.stage === status.current_stage)
    : 0
  const next = status ? nextStage(status.current_stage) : null

  return (
    <div>
      <PageHeader
        title="Kurulum"
        subtitle="Salonun ilk kurulum aşamaları — şube, paket, personel"
      />
      {loading && <LoadingSkeleton rows={4} />}
      {error && (
        <div className="mt-6">
          <Alert onRetry={() => void load()}>{error}</Alert>
        </div>
      )}
      {status && (
        <ol className="mt-6 space-y-3">
          {STEPS.map((step, i) => {
            const done = i <= currentIndex
            return (
              <li
                key={step.stage}
                className={`rounded-xl border px-4 py-3 ${
                  done
                    ? 'border-emerald-800/60 bg-emerald-950/20'
                    : 'border-slate-800 bg-slate-900/40'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-slate-100">
                      {i + 1}. {step.title}
                    </p>
                    <p className="text-xs text-slate-400">{step.hint}</p>
                  </div>
                  {step.href && (
                    <Link to={step.href} className="text-xs text-brand underline">
                      Aç
                    </Link>
                  )}
                </div>
              </li>
            )
          })}
        </ol>
      )}
      {status && !status.is_completed && next && (
        <button
          type="button"
          className="btn-primary mt-6"
          disabled={busy}
          onClick={() => void advance()}
        >
          {busy ? 'İlerletiliyor…' : `Sonraki: ${next}`}
        </button>
      )}
      {status?.is_completed && (
        <p className="mt-6 text-sm text-emerald-300">Kurulum tamamlandı.</p>
      )}
    </div>
  )
}

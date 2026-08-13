import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import { Alert, EmptyState, LoadingSkeleton, PageHeader, StatusBadge } from '../components/ui'

type Definition = {
  id: string
  code: string
  name: string
  description: string | null
  report_type: string
  is_active: boolean
}

type Run = {
  id: string
  definition_id: string
  status: string
  result_url: string | null
  export_format: string | null
  row_count: number | null
  error_message: string | null
  finished_at: string | null
  created: boolean | null
}

const FORMATS = ['JSON', 'CSV'] as const

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'Bu işlem için yetkiniz yok.'
    return e.status === 400 ? e.message : `${e.status}: ${e.message}`
  }
  if (e instanceof Error) return e.message
  return fallback
}

export default function Reports() {
  const [definitions, setDefinitions] = useState<Definition[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createMessage, setCreateMessage] = useState<string | null>(null)

  const [runFormat, setRunFormat] = useState<string>('CSV')
  const [running, setRunning] = useState<string | null>(null)
  const [runError, setRunError] = useState<string | null>(null)
  // Keyed by definition so each card can show its own latest run.
  const [runs, setRuns] = useState<Record<string, Run>>({})
  const [history, setHistory] = useState<Run[]>([])

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) {
      setLoading(true)
      setError(null)
    }
    try {
      const [definitionRows, runRows] = await Promise.all([
        api<Definition[]>('/api/v1/reports/definitions'),
        api<Run[]>('/api/v1/reports/runs?limit=50'),
      ])
      setDefinitions(definitionRows)
      setHistory(runRows)
      setError(null)
    } catch (e) {
      setError(formatApiError(e, 'Rapor tanımları yüklenemedi'))
    } finally {
      if (!opts?.silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setCreateError(null)
    setCreateMessage(null)

    if (!code.trim() || !name.trim()) {
      setCreateError('Kod ve isim gereklidir.')
      return
    }

    setCreating(true)
    try {
      await api<Definition>('/api/v1/reports/definitions', {
        method: 'POST',
        body: {
          code: code.trim(),
          name: name.trim(),
          description: description.trim() || null,
        },
      })
      setCode('')
      setName('')
      setDescription('')
      setCreateMessage('Rapor tanımı oluşturuldu.')
      await load({ silent: true })
    } catch (err) {
      setCreateError(formatApiError(err, 'Rapor tanımı oluşturulamadı'))
    } finally {
      setCreating(false)
    }
  }

  async function handleRun(def: Definition) {
    setRunError(null)
    setRunning(def.id)
    try {
      const run = await api<Run>('/api/v1/reports/runs', {
        method: 'POST',
        body: { definition_code: def.code, export_format: runFormat },
      })
      setRuns((r) => ({ ...r, [def.id]: run }))
      await load({ silent: true })
    } catch (err) {
      setRunError(formatApiError(err, 'Rapor çalıştırılamadı'))
    } finally {
      setRunning(null)
    }
  }

  async function refreshRun(defId: string, runId: string) {
    try {
      const run = await api<Run>(`/api/v1/reports/runs/${runId}`)
      setRuns((r) => ({ ...r, [defId]: run }))
    } catch (err) {
      setRunError(formatApiError(err, 'Çalıştırma durumu alınamadı'))
    }
  }

  return (
    <div>
      <PageHeader title="Raporlar" subtitle="Rapor tanımları ve çalıştırmalar" />

      {error && (
        <div className="mt-6">
          <Alert onRetry={() => void load()}>{error}</Alert>
        </div>
      )}
      {runError && (
        <div className="mt-6">
          <Alert variant="error">{runError}</Alert>
        </div>
      )}

      <section className="card mt-6" aria-labelledby="create-definition-heading">
        <div className="card-header">
          <h2 id="create-definition-heading" className="text-base font-semibold text-slate-100">
            Rapor tanımı oluştur
          </h2>
        </div>
        <form className="mt-4 grid gap-4 sm:grid-cols-3" onSubmit={handleCreate} noValidate>
          <div>
            <label htmlFor="def_code" className="label-text">
              Kod <span className="text-teal-500">*</span>
            </label>
            <input
              id="def_code"
              type="text"
              required
              maxLength={100}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="input-field"
              disabled={creating}
              placeholder="aylik_giris_ozeti"
            />
          </div>
          <div>
            <label htmlFor="def_name" className="label-text">
              İsim <span className="text-teal-500">*</span>
            </label>
            <input
              id="def_name"
              type="text"
              required
              maxLength={255}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-field"
              disabled={creating}
            />
          </div>
          <div>
            <label htmlFor="def_desc" className="label-text">
              Açıklama
            </label>
            <input
              id="def_desc"
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-field"
              disabled={creating}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-3">
            <button type="submit" className="btn-primary" disabled={creating}>
              {creating ? 'Oluşturuluyor…' : 'Tanım oluştur'}
            </button>
            {createError && <Alert variant="error">{createError}</Alert>}
            {createMessage && <Alert variant="success">{createMessage}</Alert>}
          </div>
        </form>
      </section>

      <section className="card mt-6" aria-labelledby="definition-list-heading">
        <div className="card-header flex flex-wrap items-center justify-between gap-3">
          <h2 id="definition-list-heading" className="text-base font-semibold text-slate-100">
            Tanımlar
          </h2>
          <div className="flex items-center gap-2">
            <label htmlFor="run_format" className="label-text mb-0">
              Çıktı biçimi
            </label>
            <select
              id="run_format"
              value={runFormat}
              onChange={(e) => setRunFormat(e.target.value)}
              className="input-field py-1 text-sm"
            >
              {FORMATS.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="mt-4">
            <LoadingSkeleton rows={3} />
          </div>
        ) : definitions.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              title="Henüz rapor tanımı yok"
              description="Yukarıdaki formla ilk tanımı oluşturun."
            />
          </div>
        ) : (
          <ul className="mt-4 space-y-3">
            {definitions.map((d) => {
              const run = runs[d.id]
              return (
                <li
                  key={d.id}
                  className="rounded-lg border border-slate-700 bg-slate-800/50 p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-200">{d.name}</p>
                      <p className="mt-1 font-mono text-xs text-slate-400">{d.code}</p>
                      {d.description && (
                        <p className="mt-1 text-xs text-slate-400">{d.description}</p>
                      )}
                    </div>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => void handleRun(d)}
                      disabled={running === d.id}
                    >
                      {running === d.id ? 'Çalıştırılıyor…' : 'Çalıştır'}
                    </button>
                  </div>

                  {run && (
                    <div className="mt-3 border-t border-slate-700 pt-3">
                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                        <StatusBadge status={run.status} />
                        {run.row_count !== null && <span>{run.row_count} satır</span>}
                        {run.export_format && <span>{run.export_format}</span>}
                        {run.created === false && <span>(mevcut çalıştırma)</span>}
                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={() => void refreshRun(d.id, run.id)}
                        >
                          Durumu yenile
                        </button>
                        {run.result_url && (
                          <a
                            className="text-teal-400 underline"
                            href={run.result_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Çıktıyı aç
                          </a>
                        )}
                      </div>
                      {run.error_message && (
                        <p className="mt-2 text-xs text-rose-400">{run.error_message}</p>
                      )}
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </section>

      <section className="card mt-6" aria-labelledby="run-history-heading">
        <div className="card-header">
          <h2 id="run-history-heading" className="text-base font-semibold text-slate-100">
            Son çalıştırmalar
          </h2>
        </div>
        {loading ? (
          <div className="mt-4">
            <LoadingSkeleton rows={3} />
          </div>
        ) : history.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              title="Henüz çalıştırma yok"
              description="Bir tanımı çalıştırdığınızda burada listelenir."
            />
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2">Tanım</th>
                  <th className="px-3 py-2">Durum</th>
                  <th className="px-3 py-2">Satır</th>
                  <th className="px-3 py-2">Biçim</th>
                  <th className="px-3 py-2 text-right">Çıktı</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {history.map((r) => (
                  <tr key={r.id}>
                    <td className="px-3 py-3 text-slate-300">
                      {definitions.find((d) => d.id === r.definition_id)?.name ?? '—'}
                    </td>
                    <td className="px-3 py-3">
                      <StatusBadge status={r.status} />
                      {r.error_message && (
                        <p className="mt-1 text-xs text-rose-400">{r.error_message}</p>
                      )}
                    </td>
                    <td className="px-3 py-3 text-slate-400">{r.row_count ?? '—'}</td>
                    <td className="px-3 py-3 text-slate-400">{r.export_format ?? '—'}</td>
                    <td className="px-3 py-3 text-right">
                      {r.result_url ? (
                        <a
                          className="text-teal-400 underline"
                          href={r.result_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Aç
                        </a>
                      ) : (
                        <span className="text-xs text-slate-500">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

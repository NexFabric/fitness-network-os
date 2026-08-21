import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, formatApiError } from '../api/client'
import { Alert, EmptyState, LoadingSkeleton, PageHeader, StatusBadge } from '../components/ui'

type Device = {
  id: string
  name: string
  location_id: string
  status: string
  is_active: boolean
  last_heartbeat_at: string | null
}

type Location = {
  id: string
  name: string
}

type ProvisionResult = {
  id: string
  name: string
  location_id: string
  api_key: string
}

function formatHeartbeat(value: string | null): string {
  if (!value) return 'Hiç bağlanmadı'
  const at = new Date(value)
  if (Number.isNaN(at.getTime())) return 'Bilinmiyor'
  const minutes = Math.floor((Date.now() - at.getTime()) / 60000)
  if (minutes < 1) return 'Az önce'
  if (minutes < 60) return `${minutes} dk önce`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} sa önce`
  return at.toLocaleDateString('tr-TR')
}

export default function Devices() {
  const [devices, setDevices] = useState<Device[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [locationId, setLocationId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  // Shown once, right after provisioning: the API never returns this key again.
  const [issued, setIssued] = useState<ProvisionResult | null>(null)
  const [copied, setCopied] = useState(false)

  const [revoking, setRevoking] = useState<string | null>(null)
  const [confirmRevoke, setConfirmRevoke] = useState<Device | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    const silent = opts?.silent ?? false
    if (!silent) {
      setLoading(true)
      setError(null)
    }
    try {
      const [deviceRows, locationRows] = await Promise.all([
        api<Device[]>('/api/v1/devices/'),
        api<Location[]>('/api/v1/locations'),
      ])
      setDevices(deviceRows)
      setLocations(locationRows)
      if (silent) setError(null)
    } catch (e) {
      setError(formatApiError(e, 'Cihazlar yüklenemedi'))
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (!confirmRevoke) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setConfirmRevoke(null)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [confirmRevoke])

  async function handleProvision(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    setActionMessage(null)

    const trimmed = name.trim()
    if (!trimmed) {
      setFormError('Cihaz adı gereklidir.')
      return
    }
    if (!locationId) {
      setFormError('Şube seçilmelidir.')
      return
    }

    setSubmitting(true)
    try {
      const result = await api<ProvisionResult>('/api/v1/devices/provision', {
        method: 'POST',
        body: { name: trimmed, location_id: locationId },
      })
      setIssued(result)
      setCopied(false)
      setName('')
      setLocationId('')
      await load({ silent: true })
    } catch (err) {
      setFormError(formatApiError(err, 'Cihaz oluşturulamadı'))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRevoke(device: Device) {
    setConfirmRevoke(null)
    setRevoking(device.id)
    setActionMessage(null)
    try {
      await api('/api/v1/devices/revoke', {
        method: 'POST',
        body: { device_id: device.id },
      })
      setActionMessage(`"${device.name}" iptal edildi. Açık oturumları da kapatıldı.`)
      await load({ silent: true })
    } catch (err) {
      setError(formatApiError(err, 'Cihaz iptal edilemedi'))
    } finally {
      setRevoking(null)
    }
  }

  async function copyKey(key: string) {
    try {
      await navigator.clipboard.writeText(key)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  const locationName = (id: string) =>
    locations.find((l) => l.id === id)?.name ?? '—'

  return (
    <div>
      <PageHeader
        title="Cihazlar"
        subtitle="Turnike tarayıcıları — eşleştirme anahtarı yalnızca bir kez gösterilir"
      />

      {error && (
        <div className="mt-6">
          <Alert variant="error">{error}</Alert>
        </div>
      )}
      {actionMessage && (
        <div className="mt-6">
          <Alert variant="success">{actionMessage}</Alert>
        </div>
      )}

      {issued && (
        <section className="card mt-6 border-teal-700/60" aria-labelledby="issued-key-heading">
          <div className="card-header">
            <h2 id="issued-key-heading" className="text-base font-semibold text-slate-100">
              "{issued.name}" için eşleştirme anahtarı
            </h2>
          </div>
          <p className="mt-2 text-sm text-slate-400">
            Bu anahtar bir daha gösterilmez. Tarayıcı cihazına girin; cihaz bununla
            oturum açıp kendi imza sırrını alacak.
          </p>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <div>
              <dt className="label-text">Cihaz ID</dt>
              <dd className="mt-1 break-all font-mono text-xs text-slate-300">{issued.id}</dd>
            </div>
            <div>
              <dt className="label-text">API anahtarı</dt>
              <dd className="mt-1 break-all font-mono text-xs text-teal-300">{issued.api_key}</dd>
            </div>
          </dl>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" className="btn-secondary" onClick={() => void copyKey(issued.api_key)}>
              {copied ? 'Kopyalandı' : 'Anahtarı kopyala'}
            </button>
            <button type="button" className="btn-secondary" onClick={() => setIssued(null)}>
              Kapat
            </button>
          </div>
        </section>
      )}

      <section className="card mt-6" aria-labelledby="create-device-heading">
        <div className="card-header">
          <h2 id="create-device-heading" className="text-base font-semibold text-slate-100">
            Cihaz ekle
          </h2>
        </div>
        <form className="mt-4 grid gap-4 sm:grid-cols-3" onSubmit={handleProvision} noValidate>
          <div>
            <label htmlFor="device_name" className="label-text">
              İsim <span className="text-teal-500">*</span>
            </label>
            <input
              id="device_name"
              type="text"
              required
              maxLength={100}
              value={name}
              onChange={(ev) => setName(ev.target.value)}
              className="input-field"
              disabled={submitting}
              placeholder="Turnike 1"
            />
          </div>
          <div>
            <label htmlFor="device_location" className="label-text">
              Şube <span className="text-teal-500">*</span>
            </label>
            <select
              id="device_location"
              required
              value={locationId}
              onChange={(ev) => setLocationId(ev.target.value)}
              className="input-field"
              disabled={submitting || locations.length === 0}
            >
              <option value="">Seçin…</option>
              {locations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
            {locations.length === 0 && !loading && (
              <p className="mt-1 text-xs text-slate-500">
                Önce Şubeler sayfasından bir şube oluşturun.
              </p>
            )}
          </div>
          <div className="flex items-end">
            <button type="submit" className="btn-primary w-full" disabled={submitting}>
              {submitting ? 'Oluşturuluyor…' : 'Cihaz oluştur'}
            </button>
          </div>
          {formError && (
            <div className="sm:col-span-3">
              <Alert variant="error">{formError}</Alert>
            </div>
          )}
        </form>
      </section>

      <section className="card mt-6" aria-labelledby="device-list-heading">
        <div className="card-header">
          <h2 id="device-list-heading" className="text-base font-semibold text-slate-100">
            Kayıtlı cihazlar
          </h2>
        </div>

        {loading ? (
          <div className="mt-4">
            <LoadingSkeleton rows={3} />
          </div>
        ) : devices.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              title="Henüz cihaz yok"
              description="Turnike tarayıcılarını buradan tanımlayın."
            />
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2">İsim</th>
                  <th className="px-3 py-2">Şube</th>
                  <th className="px-3 py-2">Durum</th>
                  <th className="px-3 py-2">Son bağlantı</th>
                  <th className="px-3 py-2 text-right">İşlem</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {devices.map((d) => (
                  <tr key={d.id}>
                    <td className="px-3 py-3 text-slate-200">{d.name}</td>
                    <td className="px-3 py-3 text-slate-400">{locationName(d.location_id)}</td>
                    <td className="px-3 py-3">
                      <StatusBadge status={d.is_active ? d.status : 'IPTAL'} />
                    </td>
                    <td className="px-3 py-3 text-slate-400">
                      {formatHeartbeat(d.last_heartbeat_at)}
                    </td>
                    <td className="px-3 py-3 text-right">
                      {d.is_active ? (
                        <button
                          type="button"
                          className="btn-secondary"
                          onClick={() => setConfirmRevoke(d)}
                          disabled={revoking === d.id}
                        >
                          {revoking === d.id ? 'İptal ediliyor…' : 'İptal et'}
                        </button>
                      ) : (
                        <span className="text-xs text-slate-500">İptal edildi</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {confirmRevoke && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="revoke-heading"
        >
          <div className="card w-full max-w-md">
            <h2 id="revoke-heading" className="text-base font-semibold text-slate-100">
              Cihaz iptal edilsin mi?
            </h2>
            <p className="mt-2 text-sm text-slate-400">
              "{confirmRevoke.name}" bir daha giriş doğrulayamaz. Açık oturumları
              anında kapanır ve API anahtarı geçersiz olur. Bu işlem geri alınamaz —
              cihazı tekrar kullanmak için yeniden oluşturmanız gerekir.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setConfirmRevoke(null)}>
                Vazgeç
              </button>
              <button
                type="button"
                className="btn-danger"
                onClick={() => void handleRevoke(confirmRevoke)}
              >
                İptal et
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

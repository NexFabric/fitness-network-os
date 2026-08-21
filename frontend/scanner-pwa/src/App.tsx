import { useCallback, useState, type FormEvent, useEffect } from 'react'
import {
  authenticateDevice,
  clearAuth,
  getDeviceKey,
  getTenantId,
  validateQr,
  type ValidateQrResponse,
} from './api/client'
import { CameraQrScanner } from './components/CameraQrScanner'
import { ReloadPrompt } from './components/ReloadPrompt'
import { ErrorBoundary } from './components/ErrorBoundary'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export default function App() {
  const [deviceId, setDeviceId] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [tenantId, setTenantId] = useState(getTenantId() ?? '')
  const [paired, setPaired] = useState(false)
  const [qrToken, setQrToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ValidateQrResponse | null>(null)
  const [scanning, setScanning] = useState(false)
  const [manualMode, setManualMode] = useState(false)
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [credsOpen, setCredsOpen] = useState(
    () => !getTenantId(),
  )

  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)

  useEffect(() => {
    function handleOnline() { setIsOnline(true) }
    function handleOffline() { setIsOnline(false) }
    
    function handleBeforeInstallPrompt(e: Event) {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

    void getDeviceKey().then((key) => {
      setPaired(Boolean(key) && Boolean(getTenantId()))
    })
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    }
  }, [])

  async function handleInstallClick() {
    if (!deferredPrompt) return
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') {
      setDeferredPrompt(null)
    }
  }

  async function saveCredentials(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const did = deviceId.trim()
    const tid = tenantId.trim()
    const key = apiKey.trim()
    if (!did || !tid || !key) {
      setError('Cihaz ID, Tenant ID ve API anahtarı gereklidir.')
      return
    }

    try {
      const auth = await authenticateDevice(did, tid, key)
      setTenantId(auth.tenant_id)
      setPaired(true)
      setApiKey('')
      setError(null)
      setCredsOpen(false)
    } catch {
      setPaired(false)
      setError('Cihaz eşlenemedi. Kimlik bilgilerini kontrol edin.')
    }
  }

  const runValidate = useCallback(
    async (tokenRaw: string) => {
      setError(null)
      setResult(null)
      const token = tokenRaw.trim()
      if (!token) {
        setError('QR kod gereklidir.')
        return
      }
      // Offline policy: deny-by-default — no offline GRANT path.
      if (!navigator.onLine) {
        setError(
          'Çevrimdışı: QR doğrulama sunucu gerektirir. Ağ yokken geçiş verilmez (deny-by-default).',
        )
        return
      }
      if (!getTenantId()) {
        setError('Önce cihazı eşleyin (cihaz ID + API anahtarı + tenant).')
        setCredsOpen(true)
        return
      }

      try {
        const res = await validateQr({
          token,
          location_id: null,
          consume: false,
        })
        setResult(res)
      } catch (err) {
        console.error('Doğrulama hatası:', err)
        setError('Sunucu bağlantı hatası veya doğrulama başarısız.')
      }
    },
    [],
  )

  async function onValidate(e: FormEvent) {
    e.preventDefault()
    await runValidate(qrToken)
  }

  const onCameraDecode = useCallback(
    (token: string) => {
      setScanning(false)
      setQrToken(token)
      setError(null)
      const hasCreds = Boolean(getTenantId())
      if (hasCreds) {
        void runValidate(token)
      }
    },
    [runValidate],
  )

  function logout() {
    clearAuth()
    setTenantId('')
    setDeviceId('')
    setApiKey('')
    setPaired(false)
    setResult(null)
    setCredsOpen(true)
  }

  const granted = result?.granted === true
  const hasSavedCreds = paired && Boolean(getTenantId())

  return (
    <div className="min-h-[100dvh] flex flex-col bg-surface font-sans text-ink selection:bg-brand/30 pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]">
      {!isOnline && (
        <div className="sticky top-0 z-50 bg-accent-danger px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-white">
          İnternet bağlantısı yok — çevrimdışı
        </div>
      )}
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-800/50 bg-surface/80 px-4 sm:px-6 py-4 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand to-accent shadow-lg shadow-brand/20">
            <span className="text-sm font-bold text-white" aria-hidden="true">
              G
            </span>
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-ink">Kapı okuyucu</h1>
            <p className="text-xs font-medium uppercase tracking-wider text-ink-muted">
              GymClubNex Access
            </p>
          </div>
        </div>
        {deferredPrompt && (
          <button
            onClick={handleInstallClick}
            onTouchEnd={(e) => {
              e.preventDefault()
              handleInstallClick()
            }}
            className="rounded-control bg-brand px-3 py-1.5 text-xs font-medium text-white shadow hover:bg-brand-deep"
          >
            Uygulamayı yükle
          </button>
        )}
      </header>

      <div className="mx-auto w-full max-w-lg flex-1 px-4 py-8">
        <section className="mb-6 rounded-xl border border-slate-800/80 bg-slate-900/50 p-3">
          <button
            type="button"
            onClick={() => setCredsOpen((o) => !o)}
            onTouchEnd={(e) => {
              e.preventDefault()
              setCredsOpen((o) => !o)
            }}
            className="flex w-full items-center justify-between gap-2 rounded-lg px-1 py-1 text-left focus:outline-none"
            aria-expanded={credsOpen}
          >
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Cihaz eşleme
              </h2>
              {hasSavedCreds ? (
                <div className="flex items-center gap-2 mt-1">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                  </span>
                  <span className="text-xs font-semibold text-emerald-400">Çevrimiçi</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 mt-1 rounded-full bg-amber-500/10 px-2 py-0.5 border border-amber-500/20 w-fit">
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500"></span>
                  <span className="text-[10px] font-semibold text-amber-400">Çevrimdışı</span>
                </div>
              )}
            </div>
            <span className="text-xs text-slate-500">{credsOpen ? 'Gizle' : 'Göster'}</span>
          </button>
          {credsOpen && (
            <form onSubmit={saveCredentials} className="mt-3 space-y-3 border-t border-slate-800/80 pt-3">
              <div>
                <label htmlFor="device-id" className="text-xs text-slate-500">Cihaz ID</label>
                <input id="device-id" type="text" autoComplete="off" value={deviceId} onChange={(e) => setDeviceId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm text-slate-200" />
              </div>
              <div>
                <label htmlFor="api-key" className="text-xs text-slate-500">API anahtarı</label>
                <input id="api-key" type="password" autoComplete="off" value={apiKey} onChange={(e) => setApiKey(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm text-slate-200" />
              </div>
              <div>
                <label htmlFor="tenant" className="text-xs text-slate-500">Tenant ID</label>
                <input id="tenant" type="text" autoComplete="off" value={tenantId} onChange={(e) => setTenantId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm text-slate-200" />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="rounded-control bg-brand px-4 py-1.5 text-sm font-medium text-white hover:bg-brand-deep"
                >
                  Eşle
                </button>
                <button
                  type="button"
                  onClick={logout}
                  className="rounded-control border border-slate-800 px-4 py-1.5 text-sm text-ink-muted hover:text-ink"
                >
                  Temizle
                </button>
              </div>
            </form>
          )}
        </section>

        <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          {!scanning && !manualMode ? (
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setScanning(true)}
                onTouchEnd={(e) => {
                  e.preventDefault()
                  setScanning(true)
                }}
                className="flex flex-col items-center gap-3 rounded-xl bg-slate-800 p-4 transition-colors hover:bg-slate-700"
              >
                <svg
                  className="h-8 w-8 text-brand-light"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                  />
                </svg>
                <span className="text-sm font-medium">Kamera ile tara</span>
              </button>
              <button
                onClick={() => setManualMode(true)}
                onTouchEnd={(e) => {
                  e.preventDefault()
                  setManualMode(true)
                }}
                className="flex flex-col items-center gap-3 rounded-xl bg-slate-800 p-4 transition-colors hover:bg-slate-700"
              >
                <svg
                  className="h-8 w-8 text-accent"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
                <span className="text-sm font-medium">Klavyeden gir</span>
              </button>
            </div>
          ) : scanning ? (
            <ErrorBoundary>
              <CameraQrScanner active={scanning} onDecode={onCameraDecode} onStop={() => setScanning(false)} />
            </ErrorBoundary>
          ) : (
            <div className="absolute inset-0 z-20 flex items-center justify-center bg-surface p-6">
              <form onSubmit={onValidate} className="w-full">
                <label className="mb-2 block text-sm font-medium text-ink-muted">
                  QR token
                </label>
                <input
                  autoFocus
                  value={qrToken}
                  onChange={(e) => setQrToken(e.target.value)}
                  className="mb-4 w-full rounded-control border border-slate-700 bg-slate-900 px-4 py-3 text-ink"
                />
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setManualMode(false)}
                    className="flex-1 rounded-xl border border-slate-700 py-3 text-ink-muted"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    className="flex-1 rounded-xl bg-brand py-3 font-medium text-white hover:bg-brand-deep"
                  >
                    Doğrula
                  </button>
                </div>
              </form>
            </div>
          )}
        </section>

        {error && <div className="mt-4 rounded-xl border border-red-800/80 bg-red-950/60 px-4 py-3 text-sm text-red-200">{error}</div>}

        {result && (
          <div className="mt-6 flex flex-col items-center animate-in zoom-in-95 duration-300">
            {granted ? (
              <div className="w-full max-w-sm rounded-3xl bg-white shadow-2xl overflow-hidden">
                <div className="flex flex-col items-center bg-accent py-8 text-surface">
                  <div className="mb-4 rounded-full bg-white/20 p-3">
                    <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <path d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold">Onaylandı</h2>
                </div>
                <div className="p-6 text-center text-slate-900">
                  <p className="text-lg font-semibold">Geçiş yetkisi tanımlandı</p>
                  <button
                    onClick={() => setResult(null)}
                    onTouchEnd={(e) => {
                      e.preventDefault()
                      setResult(null)
                    }}
                    className="mt-6 w-full rounded-xl bg-accent py-3 font-bold text-surface"
                  >
                    Tamam
                  </button>
                </div>
              </div>
            ) : (
              <div className="w-full max-w-sm rounded-3xl bg-white shadow-2xl overflow-hidden">
                <div className="flex flex-col items-center bg-rose-500 py-8 text-white">
                  <div className="mb-4 rounded-full bg-white/20 p-3"><svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M6 18L18 6M6 6l12 12" /></svg></div>
                  <h2 className="text-2xl font-bold">Reddedildi</h2>
                </div>
                <div className="p-6 text-slate-900 text-center">
                  <p className="text-sm font-medium text-rose-700">
                    {{
                      unknown_kid: 'Farklı kulüp anahtarı (Farklı Kulüp / Tenant QR Kodu)',
                      tenant_mismatch: 'Yetkisiz kulüp geçişi',
                      token_expired: 'QR kod süresi dolmuş — Sporcudan yeni QR almasını isteyin',
                      key_revoked: 'Geçersiz güvenlik anahtarı',
                      no_active_membership: 'Aktif üyelik veya geçerli paket bulunamadı',
                      past_due_block: 'Gecikmiş ödeme nedeniyle geçiş engellendi',
                      insufficient_wallet_balance: 'Kullanım hakkı tükendi',
                      device_unauthorized: 'Yetkisiz turnike cihazı',
                    }[result.reason ?? ''] ?? (result.reason || 'Geçiş yetkisi yok')}
                  </p>
                  <button onClick={() => setResult(null)} onTouchEnd={(e) => { e.preventDefault(); setResult(null) }} className="mt-6 w-full rounded-xl bg-slate-900 py-3 font-bold text-white">Geri Dön</button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      <ReloadPrompt />
    </div>
  )
}

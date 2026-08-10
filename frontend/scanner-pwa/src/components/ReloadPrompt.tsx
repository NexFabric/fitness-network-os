import { useRegisterSW } from 'virtual:pwa-register/react'

export function ReloadPrompt() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r: ServiceWorkerRegistration | undefined) {
      console.log('SW Registered:', r)
    },
    onRegisterError(error: unknown) {
      console.error('SW registration error', error)
    },
  })

  if (!needRefresh) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 rounded-xl border border-teal-500/30 bg-slate-900/90 p-4 shadow-xl backdrop-blur-md animate-in slide-in-from-bottom-4">
      <div className="mb-3 text-sm font-medium text-slate-200">
        Yeni bir güncelleme var. Uygulamayı yenileyin.
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => updateServiceWorker(true)}
          className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-500"
        >
          Yenile
        </button>
        <button
          onClick={() => setNeedRefresh(false)}
          className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700"
        >
          Kapat
        </button>
      </div>
    </div>
  )
}

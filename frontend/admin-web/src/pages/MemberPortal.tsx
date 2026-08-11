import { useState, useEffect } from 'react'
import QRCode from 'qrcode'

export default function MemberPortal() {
  const [token, setToken] = useState('')
  const [qrDataUrl, setQrDataUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(60)
  const [copied, setCopied] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    let timer: ReturnType<typeof setInterval>
    if (token && secondsLeft > 0) {
      timer = setInterval(() => {
        setSecondsLeft((prev) => prev - 1)
      }, 1000)
    }
    return () => clearInterval(timer)
  }, [token, secondsLeft])

  const handleGenerateQr = async () => {
    setLoading(true)
    setCopied(false)
    setErrorMsg('')
    try {
      // Authenticated member self-issue endpoint (/api/v1/access/qr/issue-self)
      const res = await fetch('/api/v1/access/qr/issue-self', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          ttl_seconds: 60,
        }),
      })

      const data = await res.json()
      if (res.ok && data.token) {
        setToken(data.token)
        // Render QR strictly client-side to prevent credential leakage
        const url = await QRCode.toDataURL(data.token, { width: 220, margin: 2 })
        setQrDataUrl(url)
        setSecondsLeft(60)
      } else {
        const msg = data.detail || 'Geçerli bir oturum bulunamadı. Lütfen giriş yapın.'
        setErrorMsg(msg)
      }
    } catch (err) {
      setErrorMsg('Bağlantı hatası: ' + (err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = () => {
    if (!token) return
    navigator.clipboard.writeText(token)
    setCopied(true)
    setTimeout(() => setCopied(false), 3000)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-8 text-slate-100 font-sans">
      <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-cyan-500 font-extrabold text-white text-xl">
              N
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">
                GymClubNex
              </h1>
              <p className="text-xs text-slate-400">Üye Portalı (Member Portal)</p>
            </div>
          </div>
          <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
            MEMBER ROUTE
          </span>
        </div>

        {/* Info Card */}
        <div className="mb-6 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
          <div className="flex justify-between text-xs">
            <div>
              <div className="text-slate-400">Giriş Modu</div>
              <div className="font-bold text-emerald-400">🔑 Self-Service QR (Oturum Bağlı)</div>
            </div>
            <div className="text-right">
              <div className="text-slate-400">Güvenlik Prototipi</div>
              <div className="font-bold text-sky-400">Client-Side Render (Zero Leak)</div>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs font-bold text-red-400">
            ⚠️ {errorMsg}
          </div>
        )}

        {/* Generate Button */}
        <button
          onClick={handleGenerateQr}
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-4 py-4 text-base font-extrabold text-white shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
        >
          {loading ? '⚡ Üretiliyor...' : '⚡ GİRİŞ QR KODU OLUŞTUR'}
        </button>

        {/* QR Display */}
        {token && qrDataUrl && (
          <div className="mt-6 text-center animate-fade-in">
            <div className="mb-3 flex items-center justify-center gap-2 text-sm font-bold">
              <span>⏰ Kalan Geçerlilik Süresi:</span>
              <span
                className={secondsLeft <= 10 ? 'text-red-400 font-extrabold' : 'text-amber-400 font-extrabold'}
              >
                {secondsLeft > 0 ? `${secondsLeft} Saniye` : 'Süre Doldu (Yeniden Üretin)'}
              </span>
            </div>

            <div className="mb-4 inline-block rounded-2xl bg-white p-4 shadow-xl shadow-emerald-500/10">
              <img
                src={qrDataUrl}
                alt="Üye Giriş QR Kodu"
                className="h-52 w-52"
              />
            </div>

            <div className="mb-3 max-h-14 overflow-y-auto rounded-lg border border-dashed border-slate-700 bg-slate-950 p-2 text-left font-mono text-[10px] text-slate-400 break-all">
              {token}
            </div>

            <button
              onClick={handleCopy}
              className="w-full rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-slate-700"
            >
              📋 KODU KOPYALA (TURNİKEYE YAPIŞTIR)
            </button>

            {copied && (
              <div className="mt-2 text-xs font-bold text-emerald-400">
                ✓ Token Panoya Kopyalandı! Turnikeden Geçebilirsiniz.
              </div>
            )}
          </div>
        )}

        <div className="mt-6 border-t border-slate-800/80 pt-4 text-center text-xs text-slate-500 leading-relaxed">
          💡 <b>Turnike Geçiş Adımı:</b> QR kodunuzu ürettikten sonra kopyalayıp kapı okuyucu sekmesinde (
          <code className="text-emerald-400">http://localhost:5174</code>) doğrulatın.
        </div>
      </div>
    </div>
  )
}

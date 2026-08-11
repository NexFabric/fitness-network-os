import { useState, useEffect } from 'react'

export default function MemberPortal() {
  const [memberId, setMemberId] = useState('56e4427d-950d-483a-ae1b-19e510725f61')
  const [token, setToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(60)
  const [copied, setCopied] = useState(false)

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
    try {
      // 1. Try authenticated member self-issue endpoint (/api/v1/access/qr/issue-self)
      let res = await fetch('http://localhost:8000/api/v1/access/qr/issue-self', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': '92c41231-2a7d-42a5-862d-fda966f1137e',
        },
        credentials: 'include',
        body: JSON.stringify({
          ttl_seconds: 60,
        }),
      })

      // 2. If unauthenticated demo mode (401/404), fall back to staff endpoint with demo member_id
      if (!res.ok && (res.status === 401 || res.status === 404)) {
        res = await fetch('http://localhost:8000/api/v1/access/qr/issue', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Tenant-ID': '92c41231-2a7d-42a5-862d-fda966f1137e',
          },
          credentials: 'include',
          body: JSON.stringify({
            member_id: memberId,
            ttl_seconds: 60,
          }),
        })
      }

      const data = await res.json()
      if (data.token) {
        setToken(data.token)
        setSecondsLeft(60)
      } else {
        alert('QR Kod üretilemedi: ' + JSON.stringify(data))
      }
    } catch (err) {
      alert('Hata oluştu: ' + (err as Error).message)
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
              <p className="text-xs text-slate-400">Üye Mobil Portal (Athlete App)</p>
            </div>
          </div>
          <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
            CANLI PWA
          </span>
        </div>

        {/* Member Account Selector */}
        <div className="mb-6 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
          <label className="mb-2 block text-[11px] font-extrabold uppercase tracking-wider text-slate-400">
            📱 SPORCU HESABI SEÇİN
          </label>
          <select
            value={memberId}
            onChange={(e) => {
              setMemberId(e.target.value)
              setToken('')
            }}
            className="mb-4 w-full rounded-xl border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm font-semibold text-white outline-none focus:border-emerald-500"
          >
            <option value="56e4427d-950d-483a-ae1b-19e510725f61">
              Mehmet Kaya (DEMO-101) - mehmet@demo.local
            </option>
            <option value="89023693-520e-40fa-af48-a014479d3f0e">
              Emrah Akçay (DEMO-001) - demo.admin@demo.local
            </option>
          </select>

          <div className="flex justify-between text-xs">
            <div>
              <div className="text-slate-400">Abonelik Statüsü</div>
              <div className="font-bold text-emerald-400">🟢 VIP ÜYELİK (AKTİF)</div>
            </div>
            <div className="text-right">
              <div className="text-slate-400">Hak Cüzdanı</div>
              <div className="font-bold text-sky-400">10 / 10 GİRİŞ HAKKI</div>
            </div>
          </div>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerateQr}
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-4 py-4 text-base font-extrabold text-white shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
        >
          {loading ? '⚡ Üretiliyor...' : '⚡ GİRİŞ QR KODU OLUŞTUR'}
        </button>

        {/* QR Display */}
        {token && (
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
                src={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(
                  token
                )}`}
                alt="Üye QR Kodu"
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

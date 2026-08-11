import { useState } from 'react'

export default function TrainerPortal() {
  const [sessions] = useState([
    { time: '10:00 - 11:00', member: 'Mehmet Kaya', plan: 'Özel PT (Personal Training)', status: 'GELDI', attendance: '🟢 Turnikeden Geçti (10:02)' },
    { time: '11:30 - 12:30', member: 'Ayşe Yılmaz', plan: 'Pilates Reformer', status: 'BEKLENIYOR', attendance: '⏳ Henüz Giriş Yapmadı' },
    { time: '14:00 - 15:00', member: 'Ali Demir', plan: 'Vücut Geliştirme Programı', status: 'BEKLENIYOR', attendance: '⏳ Henüz Giriş Yapmadı' },
  ])

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100 font-sans">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between border-b border-slate-800 pb-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 font-black text-white text-2xl shadow-xl shadow-amber-500/20">
              🏋️‍♂️
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Antrenör & PT Eğitmen Portalı
              </h1>
              <p className="text-sm text-slate-400">Canlı Ders Takvimi, Üye Yoklaması ve Antrenman Programları</p>
            </div>
          </div>
          <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-4 py-1.5 text-xs font-bold text-amber-400">
            ANTRENÖR MODU
          </span>
        </div>

        {/* Today's Schedule Card */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <h2 className="mb-4 text-lg font-bold text-white">📅 Bugünkü PT Ders Programınız</h2>

          <div className="space-y-4">
            {sessions.map((s, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/60 p-4 transition-colors hover:border-slate-700"
              >
                <div className="flex items-center gap-4">
                  <div className="rounded-xl bg-slate-800 px-3 py-2 text-center text-xs font-bold text-amber-400">
                    {s.time}
                  </div>
                  <div>
                    <h3 className="font-bold text-white">{s.member}</h3>
                    <p className="text-xs text-slate-400">{s.plan}</p>
                  </div>
                </div>

                <div className="text-right text-xs">
                  <div className="font-bold text-emerald-400">{s.attendance}</div>
                  <button className="mt-2 rounded-lg bg-amber-500/10 border border-amber-500/30 px-3 py-1 text-amber-300 font-bold hover:bg-amber-500/20">
                    Yoklama Al & Nota Ekle
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

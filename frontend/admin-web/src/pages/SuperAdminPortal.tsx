import { useState } from 'react'

export default function SuperAdminPortal() {
  const [tenants] = useState([
    { id: '92c41231-2a7d-42a5-862d-fda966f1137e', name: 'Demo Gym', org: 'NexFabric Network', members: 3, status: 'ACTIVE', quota: '1,000 Üye' },
    { id: 'a1b2c3d4-5678-90ab-cdef-1234567890ab', name: 'FitClub Levent', org: 'FitClub Franchise', members: 1420, status: 'ACTIVE', quota: '5,000 Üye' },
    { id: 'b2c3d4e5-6789-01ab-cdef-2345678901bc', name: 'Gold Gym Kadıköy', org: 'Gold Fitness Group', members: 890, status: 'ACTIVE', quota: '2,500 Üye' },
  ])

  return (
    <div className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100 font-sans">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between border-b border-slate-800 pb-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-purple-600 font-black text-white text-2xl shadow-xl shadow-purple-500/20">
              👑
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-white tracking-tight">
                Federasyon & Platform SuperAdmin Konsolu
              </h1>
              <p className="text-sm text-slate-400">Global Organizasyonlar, Kulüp Tenant Kotaları ve Sistem Denetimi</p>
            </div>
          </div>
          <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-4 py-1.5 text-xs font-bold text-purple-400">
            PLATFORM OPERATÖRÜ MODU
          </span>
        </div>

        {/* Global KPI Cards */}
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Toplam Kulüp (Tenant)</div>
            <div className="mt-2 text-3xl font-extrabold text-white">14 Kulüp</div>
            <div className="mt-1 text-xs text-emerald-400">+2 Yeni Kulüp (Bu Ay)</div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Toplam Aktif Sporcu</div>
            <div className="mt-2 text-3xl font-extrabold text-purple-400">24,850</div>
            <div className="mt-1 text-xs text-slate-400">Multi-Tenant RLS Korumalı</div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Donanım Kapı Okuyucuları</div>
            <div className="mt-2 text-3xl font-extrabold text-amber-400">48 Kiosk PWA</div>
            <div className="mt-1 text-xs text-emerald-400">● 48/48 Çevrimiçi</div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Sistem Lisans Geliri</div>
            <div className="mt-2 text-3xl font-extrabold text-emerald-400">₺184,500 / ay</div>
            <div className="mt-1 text-xs text-slate-400">Stripe/Iyzico Bağlantılı</div>
          </div>
        </div>

        {/* Tenants Table */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">🏛️ Bağlı Spor Salonu Tenant'ları</h2>
            <button className="rounded-xl bg-purple-600 px-4 py-2 text-xs font-bold text-white hover:bg-purple-500">
              + Yeni Tenant (Gym) Lisansla
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Tenant ID</th>
                  <th className="py-3 px-4">Kulüp Adı</th>
                  <th className="py-3 px-4">Organizasyon</th>
                  <th className="py-3 px-4">Aktif Üye</th>
                  <th className="py-3 px-4">Lisans Kotası</th>
                  <th className="py-3 px-4">Durum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {tenants.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">{t.id.substring(0, 13)}...</td>
                    <td className="py-3 px-4 font-bold text-white">{t.name}</td>
                    <td className="py-3 px-4 text-slate-300">{t.org}</td>
                    <td className="py-3 px-4 font-semibold text-purple-300">{t.members} Sporcu</td>
                    <td className="py-3 px-4 text-slate-400">{t.quota}</td>
                    <td className="py-3 px-4">
                      <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 text-xs font-bold text-emerald-400">
                        {t.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

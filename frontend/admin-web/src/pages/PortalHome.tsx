import { Link } from 'react-router-dom'

export default function PortalHome() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12 text-slate-100 font-sans">
      <div className="w-full max-w-5xl">
        {/* Brand Header */}
        <div className="mb-10 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 font-extrabold text-white text-2xl shadow-xl shadow-emerald-500/20">
            N
          </div>
          <h1 className="text-4xl font-extrabold text-white tracking-tight">
            GymClubNex
          </h1>
          <p className="mt-2 text-base text-slate-400">
            Fitness Network OS — Çok Katmanlı Rol & Portal Ekosistemi
          </p>
        </div>

        {/* Portal Gateway Cards - 5 Unique Personas */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* 1. SuperAdmin */}
          <Link
            to="/superadmin"
            className="group relative flex flex-col justify-between rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-xl transition-all duration-200 hover:-translate-y-1 hover:border-purple-500/50 hover:shadow-2xl hover:shadow-purple-500/10"
          >
            <div>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-500/10 text-purple-400 text-2xl font-bold">
                👑
              </div>
              <h2 className="text-xl font-bold text-white group-hover:text-purple-400 transition-colors">
                1. Federasyon SuperAdmin
              </h2>
              <p className="mt-2 text-xs leading-relaxed text-slate-400">
                Global organizasyonlar, tüm kulüp tenant kotaları, lisanslama ve sistem çapında audit denetimi.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-2 text-sm font-bold text-purple-400">
              <span>Federasyon Girişi</span>
              <span>→</span>
            </div>
          </Link>

          {/* 2. Tenant Gym Owner */}
          <Link
            to="/login"
            className="group relative flex flex-col justify-between rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-xl transition-all duration-200 hover:-translate-y-1 hover:border-cyan-500/50 hover:shadow-2xl hover:shadow-cyan-500/10"
          >
            <div>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400 text-2xl font-bold">
                👔
              </div>
              <h2 className="text-xl font-bold text-white group-hover:text-cyan-400 transition-colors">
                2. Kulüp Sahibi (Ops Console)
              </h2>
              <p className="mt-2 text-xs leading-relaxed text-slate-400">
                Gym sahipleri ve resepsiyon personeli için üye kaydı, üyelik paketleri, şubeler ve kasa yönetimi.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-2 text-sm font-bold text-cyan-400">
              <span>Yönetim Girişi</span>
              <span>→</span>
            </div>
          </Link>

          {/* 3. Trainer / Antrenör */}
          <Link
            to="/trainer"
            className="group relative flex flex-col justify-between rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-xl transition-all duration-200 hover:-translate-y-1 hover:border-amber-500/50 hover:shadow-2xl hover:shadow-amber-500/10"
          >
            <div>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-400 text-2xl font-bold">
                🏋️‍♂️
              </div>
              <h2 className="text-xl font-bold text-white group-hover:text-amber-400 transition-colors">
                3. Antrenör & PT Portalı
              </h2>
              <p className="mt-2 text-xs leading-relaxed text-slate-400">
                Spor hocaları ve özel ders eğitmenleri için canlı ders takvimi, yoklama ve ölçüm kayıtları.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-2 text-sm font-bold text-amber-400">
              <span>Eğitmen Girişi</span>
              <span>→</span>
            </div>
          </Link>

          {/* 4. Member / Sporcu */}
          <Link
            to="/member"
            className="group relative flex flex-col justify-between rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-xl transition-all duration-200 hover:-translate-y-1 hover:border-emerald-500/50 hover:shadow-2xl hover:shadow-emerald-500/10"
          >
            <div>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-400 text-2xl font-bold">
                📱
              </div>
              <h2 className="text-xl font-bold text-white group-hover:text-emerald-400 transition-colors">
                4. Sporcu (Üye) Portalı
              </h2>
              <p className="mt-2 text-xs leading-relaxed text-slate-400">
                Sporcuların cep telefonlarından tek tıkla canlı dinamik turnike QR kod ürettiği mobil PWA.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-2 text-sm font-bold text-emerald-400">
              <span>Üye Girişi</span>
              <span>→</span>
            </div>
          </Link>

          {/* 5. Scanner PWA */}
          <a
            href="http://localhost:5174"
            target="_blank"
            rel="noopener noreferrer"
            className="group relative flex flex-col justify-between rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-xl transition-all duration-200 hover:-translate-y-1 hover:border-rose-500/50 hover:shadow-2xl hover:shadow-rose-500/10"
          >
            <div>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-500/10 text-rose-400 text-2xl font-bold">
                📹
              </div>
              <h2 className="text-xl font-bold text-white group-hover:text-rose-400 transition-colors">
                5. Kapı Okuyucu Kiosk PWA
              </h2>
              <p className="mt-2 text-xs leading-relaxed text-slate-400">
                Turnikeye monte edilen donanım PWA cihazı. QR okur, sahteciliği engeller, kapı rölesini açar.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-2 text-sm font-bold text-rose-400">
              <span>Cihaz PWA Aç (:5174)</span>
              <span>↗</span>
            </div>
          </a>
        </div>

        {/* System Architecture Report Link */}
        <div className="mt-8 text-center">
          <a
            href="/architecture_report.html"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-xs font-bold text-slate-300 transition-colors hover:border-emerald-500 hover:text-emerald-400"
          >
            <span>📊 Canlı Sistem Mimari & RLS İnteraktif Raporunu Aç</span>
            <span>↗</span>
          </a>
        </div>

        {/* Footer info */}
        <div className="mt-8 text-center text-xs text-slate-500">
          GymClubNex Fitness Network OS — Multi-Tenant Architecture & RLS Entitlement Engine
        </div>
      </div>
    </div>
  )
}

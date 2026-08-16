"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, ShieldCheck, Terminal, Cpu, Activity, Lock } from "lucide-react";

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-background pt-24 pb-28 sm:pt-32 sm:pb-36">
      {/* Background Ambience */}
      <div
        className="pointer-events-none absolute left-1/2 top-0 h-[600px] w-[900px] -translate-x-1/2 -translate-y-1/4 rounded-full bg-brand/15 blur-[140px] opacity-70"
        aria-hidden="true"
      />
      <div className="pointer-events-none absolute inset-0 bg-grid-pattern opacity-30" aria-hidden="true" />

      <div className="relative z-10 mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          {/* Refined Technical Badge */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="mb-8 flex justify-center"
          >
            <div className="inline-flex items-center gap-2.5 rounded-full border border-brand/30 bg-surface-raised/80 px-4 py-1.5 text-xs font-mono font-medium text-brand-light shadow-inner backdrop-blur-md">
              <span className="h-2 w-2 rounded-full bg-accent" />
              <span>FITNESS NETWORK OS // RELEASE v2.4</span>
            </div>
          </motion.div>

          {/* High-Contrast Hero Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.08 }}
            className="text-4xl font-bold tracking-[-0.03em] text-foreground sm:text-6xl lg:text-7xl"
            style={{ textWrap: "balance" }}
          >
            Hız. Kontrol. <span className="text-white">Performans.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.16 }}
            className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-ink-muted"
            style={{ textWrap: "balance" }}
          >
            Spor kulüpleri, stüdyolar ve tesis zincirleri için yüksek güvenlikli
            işletim sistemi. Donanım entegrasyonu, dinamik QR turnike ve kuruş
            cinsinden faturalama.
          </motion.p>

          {/* Premium Button Actions */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.24 }}
            className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4"
          >
            <Link
              href="/#demo"
              className="btn-primary group inline-flex h-12 items-center gap-2 rounded-xl px-7 text-sm font-semibold text-white"
            >
              Demoyu başlat
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/#features"
              className="btn-secondary inline-flex h-12 items-center gap-2 rounded-xl px-6 text-sm font-medium text-foreground"
            >
              Özellikleri incele
              <span aria-hidden="true" className="ml-1">
                →
              </span>
            </Link>
          </motion.div>
        </div>

        {/* Athletic Ops Console Mock */}
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.35 }}
          className="mx-auto mt-16 max-w-5xl sm:mt-20"
        >
          <div className="enterprise-card overflow-hidden rounded-2xl">
            {/* Console Bar */}
            <div className="flex items-center justify-between border-b border-border/70 bg-surface-raised/90 px-4 py-3 text-xs font-mono text-ink-muted">
              <div className="flex items-center gap-2">
                <Terminal className="h-3.5 w-3.5 text-brand-light" />
                <span className="text-slate-300 font-semibold">ops.gymclubnex.internal</span>
              </div>
              <div className="flex items-center gap-3 text-slate-400">
                <span className="flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5 text-accent" /> RLS ISOLATED
                </span>
                <span className="hidden sm:inline text-slate-600">|</span>
                <span className="hidden sm:inline font-mono">LATENCY: 12ms</span>
              </div>
            </div>

            {/* Dashboard Telemetry Canvas */}
            <div className="grid min-h-[300px] grid-cols-1 sm:grid-cols-[220px_1fr]">
              <aside className="hidden border-r border-border/70 bg-surface-raised/40 p-4 sm:block font-mono text-xs">
                <div className="text-[11px] font-semibold tracking-wider text-ink-subtle uppercase mb-3">
                  TENANT KAPSAMI
                </div>
                <div className="rounded-lg border border-brand/30 bg-brand/10 p-2.5 text-brand-light font-medium mb-4">
                  GymClub Central [HQ]
                </div>
                <ul className="space-y-1.5 text-ink-muted">
                  <li className="px-2.5 py-1.5 rounded bg-white/5 text-slate-200">▶ Telemetri</li>
                  <li className="px-2.5 py-1.5 hover:text-slate-200">▶ Turnike Ağları</li>
                  <li className="px-2.5 py-1.5 hover:text-slate-200">▶ Üye İzinleri</li>
                  <li className="px-2.5 py-1.5 hover:text-slate-200">▶ Finans Motoru</li>
                </ul>
              </aside>

              <div className="p-6">
                <div className="flex items-center justify-between border-b border-border/50 pb-4 mb-6">
                  <div>
                    <h3 className="text-sm font-semibold text-white">Canlı Ağ Durumu</h3>
                    <p className="text-xs text-ink-muted">Tüm lokasyonlar senkronize ve güvenli</p>
                  </div>
                  <span className="rounded-md border border-accent/30 bg-accent/10 px-2.5 py-1 font-mono text-xs text-accent">
                    ● %100 OPERASYONEL
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  {[
                    { label: "Aktif Üye", val: "1.248", change: "+4.2% bu hafta", icon: Activity },
                    { label: "Doğrulanan QR Geçiş", val: "3.180 / gün", change: "0 mutabakat hatası", icon: Cpu },
                    { label: "Şube İzolasyonu", val: "6 / 6 Şube", change: "Strict RLS", icon: Lock },
                  ].map((stat) => (
                    <div key={stat.label} className="rounded-xl border border-border/60 bg-background/60 p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-mono uppercase text-ink-muted">{stat.label}</span>
                        <stat.icon className="h-4 w-4 text-brand-light" />
                      </div>
                      <div className="mt-2 text-2xl font-bold font-mono tracking-tight text-white">{stat.val}</div>
                      <div className="mt-1 text-[11px] text-accent font-mono">{stat.change}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

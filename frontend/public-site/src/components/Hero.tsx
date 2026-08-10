"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-background pt-20 pb-24 sm:pt-28 sm:pb-32">
      <div
        className="pointer-events-none absolute left-1/2 top-0 h-[640px] w-[640px] -translate-x-1/2 -translate-y-1/3 rounded-full bg-brand/20 blur-[120px] opacity-60"
        aria-hidden="true"
      />

      <div className="relative z-10 mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
            className="mb-8 flex justify-center"
          >
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3.5 py-1.5 text-sm font-medium text-accent">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
              </span>
              Sistem aktif · Fitness Network OS
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.08 }}
            className="text-4xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl"
          >
            Hız. Kontrol.{" "}
            <span className="bg-gradient-to-r from-brand to-accent bg-clip-text text-transparent">
              Performans.
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.16 }}
            className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-ink-muted"
          >
            Yeni nesil spor kulüpleri için tasarlanmış, kesintisiz işletim
            sistemi. Operasyonu bize bırakın, performansa odaklanın.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.24 }}
            className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4"
          >
            <a
              href="#demo"
              className="btn-glow group inline-flex h-12 items-center gap-2 rounded-lg bg-brand px-6 text-sm font-semibold text-white transition-colors hover:bg-brand-deep"
            >
              Demoyu başlat
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </a>
            <a
              href="#features"
              className="inline-flex h-12 items-center rounded-lg px-5 text-sm font-semibold text-foreground transition-colors hover:text-brand"
            >
              Özellikleri incele
              <span aria-hidden="true" className="ml-1">
                →
              </span>
            </a>
          </motion.div>
        </div>

        {/* Product mock — Ops Console frame */}
        <motion.div
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.35 }}
          className="mx-auto mt-16 max-w-5xl sm:mt-20"
        >
          <div className="overflow-hidden rounded-xl border border-border bg-card shadow-2xl shadow-brand/10 ring-1 ring-white/5">
            <div className="flex items-center gap-2 border-b border-border bg-surface-raised/80 px-4 py-3">
              <div className="flex gap-1.5" aria-hidden="true">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
              </div>
              <div className="mx-auto font-mono text-xs text-ink-muted">
                ops.gymclubnex.com
              </div>
            </div>

            <div className="grid min-h-[280px] grid-cols-1 sm:grid-cols-[200px_1fr]">
              {/* Mini sidebar */}
              <aside className="hidden border-r border-border bg-surface-raised/60 p-4 sm:block">
                <div className="mb-6 flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand text-xs font-bold text-white">
                    G
                  </span>
                  <span className="text-sm font-semibold">GymClubNex</span>
                </div>
                <ul className="space-y-1 text-sm">
                  {[
                    { label: "Panel", active: true },
                    { label: "Üyeler", active: false },
                    { label: "Şubeler", active: false },
                    { label: "Finans", active: false },
                  ].map((item) => (
                    <li key={item.label}>
                      <span
                        className={`block rounded-lg px-3 py-2 ${
                          item.active
                            ? "bg-brand/20 font-medium text-brand-light"
                            : "text-ink-muted"
                        }`}
                      >
                        {item.label}
                      </span>
                    </li>
                  ))}
                </ul>
              </aside>

              {/* Mini dashboard */}
              <div className="bg-background/80 p-5 sm:p-6">
                <p className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Operasyonlar
                </p>
                <p className="mt-1 text-lg font-semibold text-foreground">
                  Günlük özet
                </p>
                <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
                  {[
                    { label: "Aktif üye", value: "1.248", hint: "Bu ay +4%" },
                    { label: "Şube", value: "6", hint: "Tek panel" },
                    { label: "Günlük geçiş", value: "3.1K", hint: "QR doğrulama" },
                  ].map((kpi) => (
                    <div
                      key={kpi.label}
                      className="rounded-xl border border-border bg-card p-4 transition-colors hover:border-brand/40"
                    >
                      <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
                        {kpi.label}
                      </p>
                      <p className="mt-2 text-2xl font-bold tracking-tight tabular-nums">
                        {kpi.value}
                      </p>
                      <p className="mt-1 text-xs text-brand-light">{kpi.hint}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {["Dinamik QR", "Merkezi yönetim", "Tam izolasyon"].map(
                    (tag) => (
                      <span
                        key={tag}
                        className="rounded-full border border-border bg-surface-raised px-3 py-1 text-xs font-medium text-ink-muted"
                      >
                        {tag}
                      </span>
                    ),
                  )}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

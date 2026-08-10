"use client";

import { motion } from "framer-motion";
import { ArrowRight, Activity, Shield, Zap } from "lucide-react";

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-background pt-24 pb-32 sm:pt-32 sm:pb-40">
      {/* Background glow effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-brand/20 rounded-full blur-[120px] opacity-50 pointer-events-none" />
      
      <div className="mx-auto max-w-7xl px-6 lg:px-8 relative z-10">
        <div className="mx-auto max-w-3xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="flex items-center justify-center gap-2 mb-8"
          >
            <span className="flex items-center gap-1.5 rounded-full bg-card border border-border px-3 py-1 text-sm font-medium text-accent shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
              </span>
              Sistem Aktif
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut", delay: 0.1 }}
            className="text-5xl font-bold tracking-tight text-foreground sm:text-7xl"
          >
            Hız. Kontrol. <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-accent">Performans.</span>
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut", delay: 0.2 }}
            className="mt-6 text-lg leading-8 text-foreground/70"
          >
            Yeni nesil spor kulüpleri için tasarlanmış, kesintisiz işletim sistemi.
            Operasyonu bize bırakın, performansa odaklanın.
          </motion.p>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut", delay: 0.3 }}
            className="mt-10 flex items-center justify-center gap-x-6"
          >
            <a
              href="#demo"
              className="group flex items-center gap-2 rounded-lg bg-brand px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-deep focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand transition-all"
            >
              Sistemi Başlat
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </a>
            <a href="#features" className="text-sm font-semibold leading-6 text-foreground hover:text-brand transition-colors">
              Özellikleri İncele <span aria-hidden="true">→</span>
            </a>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut", delay: 0.5 }}
          className="mt-16 sm:mt-24 lg:mt-32"
        >
          <div className="rounded-xl bg-card border border-border p-2 shadow-2xl shadow-brand/10 ring-1 ring-white/10 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-background/50">
              <div className="flex gap-1.5">
                <div className="h-3 w-3 rounded-full bg-rose-500/80" />
                <div className="h-3 w-3 rounded-full bg-amber-500/80" />
                <div className="h-3 w-3 rounded-full bg-emerald-500/80" />
              </div>
              <div className="mx-auto text-xs font-mono text-foreground/40">ops.gymclubnex.com</div>
            </div>
            <div className="bg-background p-6 sm:p-10 min-h-[300px] flex items-center justify-center">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
                <div className="bg-card border border-border rounded-lg p-6 flex flex-col items-center justify-center gap-4 hover:border-brand/50 transition-colors">
                  <Zap className="h-8 w-8 text-amber-400" />
                  <p className="font-mono text-sm text-foreground/80">Dinamik QR Geçiş</p>
                </div>
                <div className="bg-card border border-border rounded-lg p-6 flex flex-col items-center justify-center gap-4 hover:border-brand/50 transition-colors">
                  <Activity className="h-8 w-8 text-brand" />
                  <p className="font-mono text-sm text-foreground/80">Merkezi Yönetim</p>
                </div>
                <div className="bg-card border border-border rounded-lg p-6 flex flex-col items-center justify-center gap-4 hover:border-brand/50 transition-colors">
                  <Shield className="h-8 w-8 text-accent" />
                  <p className="font-mono text-sm text-foreground/80">Tam İzolasyon</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

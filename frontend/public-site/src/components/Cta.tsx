"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const ADMIN_URL =
  process.env.NEXT_PUBLIC_ADMIN_URL?.replace(/\/$/, "") ||
  "http://localhost:5173";

export function Cta() {
  return (
    <section
      id="demo"
      className="relative isolate scroll-mt-20 overflow-hidden border-t border-border bg-background py-24 sm:py-32"
    >
      <div
        className="absolute inset-0 -z-10 bg-[radial-gradient(50rem_40rem_at_top,rgba(13,148,136,0.2)_0%,transparent_70%)]"
        aria-hidden="true"
      />

      <div className="mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl font-bold tracking-tight sm:text-4xl text-white"
          >
            Kulübünüzü yeni sürüme yükseltin
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.08 }}
            className="mt-5 text-lg leading-relaxed text-ink-muted"
          >
            Klasik yazılımların hantallığından kurtulun. GymClubNex ile tanışın
            ve kulüp operasyonunuzu modern güvenlik standartlarına yükseltin.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.14 }}
            className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4"
          >
            <a
              href="mailto:hello@gymclubnex.com?subject=GymClubNex%20Demo"
              className="btn-primary group inline-flex h-12 items-center gap-2 rounded-xl px-8 text-base font-semibold text-white"
            >
              Demoyu başlat
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </a>
            <a
              href={`${ADMIN_URL}/login`}
              className="btn-secondary inline-flex h-12 items-center rounded-xl px-6 text-sm font-medium text-foreground"
            >
              Konsola giriş
            </a>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

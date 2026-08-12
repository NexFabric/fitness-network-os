"use client";

import { motion } from "framer-motion";
import { Database, Server, Lock, Layers } from "lucide-react";

const points = [
  {
    icon: Database,
    title: "Multi-tenant izolasyon",
    body: "Her kulüp (tenant) kendi veri alanında. Paylaşılan veritabanı, ayrı erişim politikaları.",
  },
  {
    icon: Lock,
    title: "Satır düzeyinde güvenlik (RLS)",
    body: "PostgreSQL Row Level Security ile sızıntıya kapalı sorgular. Yetkisiz satır okunmaz.",
  },
  {
    icon: Server,
    title: "Transactional outbox",
    body: "Kritik olaylar kaybolmaz. Bildirim ve yan etkiler güvenilir iş kuyruğuna yazılır.",
  },
  {
    icon: Layers,
    title: "RBAC + kapsam",
    body: "Rol, yetki ve şube kapsamı birlikte. Personel yalnızca görmesi gerekeni görür.",
  },
];

export function Architecture() {
  return (
    <section
      id="architecture"
      className="relative scroll-mt-20 overflow-hidden border-t border-border bg-surface-raised/40 py-20 sm:py-28"
    >
      <div
        className="pointer-events-none absolute right-0 top-0 h-[480px] w-[480px] translate-x-1/3 -translate-y-1/4 rounded-full bg-accent/10 blur-[100px]"
        aria-hidden="true"
      />

      <div className="relative z-10 mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 items-center gap-14 lg:grid-cols-2 lg:gap-16">
          <div>
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-sm font-semibold uppercase tracking-wider text-accent"
            >
              Mimari ve güvenlik
            </motion.p>
            <motion.h2
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.05 }}
              className="mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
            >
              Büyük ölçekler için tasarlandı
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="mt-5 text-lg leading-relaxed text-ink-muted"
            >
              Verileriniz izole ve güvende. Karmaşık altyapı yükünü taşımayın —
              enterprise-grade multi-tenant mimari operasyonunuzu korur.
            </motion.p>

            <ul className="mt-10 space-y-5">
              {points.map((p, i) => (
                <motion.li
                  key={p.title}
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.08 * i }}
                  className="flex gap-3"
                >
                  <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-brand/30 bg-brand/15">
                    <p.icon className="h-4 w-4 text-brand-light" aria-hidden="true" />
                  </span>
                  <div>
                    <p className="font-semibold text-foreground">{p.title}</p>
                    <p className="mt-0.5 text-sm leading-relaxed text-ink-muted">
                      {p.body}
                    </p>
                  </div>
                </motion.li>
              ))}
            </ul>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="relative"
          >
            <div
              className="absolute -inset-3 rounded-3xl bg-gradient-to-br from-brand/20 to-accent/10 blur-xl opacity-40"
              aria-hidden="true"
            />
            <div className="relative rounded-2xl border border-border bg-background p-6 font-mono text-sm shadow-2xl sm:p-8">
              <div className="mb-5 flex gap-1.5" aria-hidden="true">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
              </div>
              <div className="space-y-2 text-ink-muted">
                <p>
                  <span className="text-brand">SELECT</span> *{" "}
                  <span className="text-brand">FROM</span> members
                </p>
                <p>
                  <span className="text-brand">WHERE</span> tenant_id ={" "}
                  <span className="text-accent">current_tenant()</span>
                </p>
                <p className="text-ink-muted/50">-- Row Level Security aktif</p>
                <p className="text-ink-muted/50">-- Yetkisiz satır: 0 sonuç</p>
                <p className="pt-3 text-accent">DURUM: İzole ve güvenli</p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

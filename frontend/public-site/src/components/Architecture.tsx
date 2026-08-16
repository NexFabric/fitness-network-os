"use client";

import { motion } from "framer-motion";
import { Database, Server, Lock, Layers, ShieldCheck } from "lucide-react";

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
      className="relative scroll-mt-20 overflow-hidden border-t border-border bg-surface-raised/40 py-24 sm:py-32"
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
              className="text-xs font-mono uppercase tracking-[0.1em] text-accent"
            >
              MİMARİ VE GÜVENLİK
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

            <ul className="mt-10 space-y-6">
              {points.map((p, i) => (
                <motion.li
                  key={p.title}
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.08 * i }}
                  className="flex gap-4"
                >
                  <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-brand/30 bg-brand/15">
                    <p.icon className="h-5 w-5 text-brand-light" aria-hidden="true" />
                  </span>
                  <div>
                    <h3 className="text-base font-semibold text-foreground">{p.title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-ink-muted">
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
            <div className="enterprise-card relative rounded-2xl p-6 sm:p-8 font-mono text-sm">
              <div className="flex items-center justify-between border-b border-border/70 pb-4 mb-5 text-xs text-ink-muted">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-accent" />
                  <span className="text-slate-200 font-semibold">PostgreSQL RLS Motoru</span>
                </div>
                <span className="text-accent">STRICT ENFORCEMENT</span>
              </div>
              <div className="space-y-2.5 text-slate-300">
                <p>
                  <span className="text-brand-light font-semibold">SET LOCAL</span>{" "}
                  app.current_tenant_id = <span className="text-amber-400">&apos;central-hq&apos;</span>;
                </p>
                <p>
                  <span className="text-brand-light font-semibold">SELECT</span> *{" "}
                  <span className="text-brand-light font-semibold">FROM</span> members;
                </p>
                <div className="pt-2 text-slate-400 text-xs space-y-1">
                  <p>-- Row Level Security otomatik filtrelendi</p>
                  <p>-- Yabancı tenant verisi: 0 kayıt / sızıntı imkansız</p>
                </div>
                <div className="mt-4 rounded-lg border border-accent/30 bg-accent/10 p-3 text-xs text-accent font-semibold flex items-center justify-between">
                  <span>DURUM: İZOLE VE GÜVENLİ</span>
                  <span className="font-mono">PASS (357/357)</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

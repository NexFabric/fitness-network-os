"use client";

import { motion } from "framer-motion";

/** Honest design targets — not live production measurements. */
const stats = [
  { name: "Uptime hedefi", value: "99.9%" },
  { name: "Veri kaybı hedefi", value: "Sıfır" },
  { name: "Ölçek hedefi", value: "Yüksek hacim" },
];

export function Metrics() {
  return (
    <section className="relative overflow-hidden border-t border-border bg-background py-20 sm:py-28">
      <div
        className="pointer-events-none absolute left-1/2 top-1/2 h-[300px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand/10 blur-[100px]"
        aria-hidden="true"
      />

      <div className="relative z-10 mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand/25 bg-brand/10 px-3 py-1 text-sm font-medium text-brand-light"
          >
            Tasarım hedefleri
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.05 }}
            className="text-3xl font-bold tracking-tight sm:text-4xl"
          >
            Operasyon için tasarlandı
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="mt-4 text-lg text-ink-muted"
          >
            Aşağıdaki rakamlar canlı ölçüm değil; platformun hedeflediği
            mühendislik çıtalarıdır. Canlı telemetri ayrı bir gözlemlenebilirlik
            hattı ile gelir.
          </motion.p>
        </div>

        <dl className="mx-auto mt-14 grid max-w-4xl grid-cols-1 gap-5 sm:grid-cols-3">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.name}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.06 }}
              className="group relative overflow-hidden rounded-xl border border-brand/20 bg-background/60 p-8 text-center backdrop-blur-sm transition-all hover:border-brand/45"
            >
              <dt className="text-xs font-medium uppercase tracking-wider text-ink-muted">
                {stat.name}
              </dt>
              <dd className="mt-3 text-3xl font-bold tracking-tight text-foreground transition-colors group-hover:text-brand sm:text-4xl">
                {stat.value}
              </dd>
            </motion.div>
          ))}
        </dl>
      </div>
    </section>
  );
}

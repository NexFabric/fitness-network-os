"use client";

import { motion } from "framer-motion";

/** Honest design targets — not live production measurements. */
const stats = [
  { name: "Uptime Hedefi", value: "99.9%" },
  { name: "Veri Kaybı Toleransı", value: "Sıfır" },
  { name: "Yatay Ölçeklenme", value: "Yüksek Hacim" },
];

export function Metrics() {
  return (
    <section className="relative overflow-hidden border-t border-border bg-background py-24 sm:py-32">
      <div
        className="pointer-events-none absolute left-1/2 top-1/2 h-[300px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand/10 blur-[100px]"
        aria-hidden="true"
      />

      <div className="relative z-10 mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-xs font-mono uppercase tracking-[0.1em] text-brand-light"
          >
            MÜHENDİSLİK ÇITALARI
          </motion.p>

          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.05 }}
            className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl text-white"
          >
            Operasyonel Güvenilirlik
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="mt-4 text-lg text-ink-muted"
          >
            Aşağıdaki değerler platformun mimari tasarım hedefleridir.
            Canlı operasyonel telemetri izole Prometheus ve denetim hatlarıyla takip edilir.
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
              className="enterprise-card rounded-2xl p-8 text-center transition-all hover:border-brand/50"
            >
              <dt className="text-xs font-mono uppercase tracking-wider text-ink-muted">
                {stat.name}
              </dt>
              <dd className="mt-3 text-3xl font-bold font-mono tracking-tight text-white sm:text-4xl">
                {stat.value}
              </dd>
            </motion.div>
          ))}
        </dl>
      </div>
    </section>
  );
}

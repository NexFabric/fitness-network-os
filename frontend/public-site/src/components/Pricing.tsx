"use client";

import { motion } from "framer-motion";
import { Check, ArrowRight } from "lucide-react";

const tiers = [
  {
    name: "Demo",
    price: "Ücretsiz",
    period: "keşif oturumu",
    description: "Operasyon konsolunu ve QR erişimi canlı görün.",
    features: [
      "Demo tenant erişimi",
      "Üye ve şube ekranları",
      "Kapı okuyucu (scanner) denemesi",
      "Teknik mimari walkthrough",
    ],
    cta: "Demoyu talep et",
    href: "mailto:hello@gymclubnex.com?subject=GymClubNex%20Demo",
    highlighted: false,
  },
  {
    name: "Operasyon",
    price: "Kurumsal",
    period: "kulüp ölçeğine göre",
    description: "Tek veya çok şubeli kulüpler için tam Athletic Ops Console.",
    features: [
      "Sınırsız personel (rol bazlı)",
      "Dinamik QR + scanner PWA",
      "Finans ve faturalama görünümü",
      "Tenant izolasyonu ve denetim izi",
      "Öncelikli destek",
    ],
    cta: "Teklif al",
    href: "mailto:hello@gymclubnex.com?subject=GymClubNex%20Teklif",
    highlighted: true,
  },
  {
    name: "Ağ",
    price: "Özel",
    period: "çok kulüp / federasyon",
    description: "Zincir ve federasyon yapıları için özel planlama.",
    features: [
      "Çok tenant operasyon",
      "Özel entegrasyonlar",
      "SLA ve güvenlik incelemesi",
      "Özel onboarding",
    ],
    cta: "İletişime geç",
    href: "mailto:hello@gymclubnex.com?subject=GymClubNex%20A%C4%9F%20Plan%C4%B1",
    highlighted: false,
  },
];

export function Pricing() {
  return (
    <section
      id="pricing"
      className="scroll-mt-20 border-t border-border bg-background py-20 sm:py-28"
    >
      <div className="mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-sm font-semibold uppercase tracking-wider text-brand"
          >
            Fiyatlandırma
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.05 }}
            className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl"
          >
            Kulübünüze uygun paket
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="mt-4 text-lg text-ink-muted"
          >
            Şeffaf başlangıç. Ölçek ve şube sayısına göre net teklif.
          </motion.p>
        </div>

        <div className="mx-auto mt-14 grid max-w-5xl grid-cols-1 gap-6 lg:grid-cols-3">
          {tiers.map((tier, i) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06 }}
              className={`flex flex-col rounded-xl border p-6 sm:p-7 ${
                tier.highlighted
                  ? "border-brand/50 bg-brand/5 shadow-lg shadow-brand/10 ring-1 ring-brand/30"
                  : "border-border bg-card"
              }`}
            >
              {tier.highlighted && (
                <span className="mb-3 w-fit rounded-full bg-brand/20 px-2.5 py-0.5 text-xs font-semibold text-brand-light">
                  Önerilen
                </span>
              )}
              <h3 className="text-lg font-semibold text-foreground">
                {tier.name}
              </h3>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-bold tracking-tight">
                  {tier.price}
                </span>
                <span className="text-sm text-ink-muted">{tier.period}</span>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                {tier.description}
              </p>
              <ul className="mt-6 flex-1 space-y-2.5">
                {tier.features.map((f) => (
                  <li key={f} className="flex gap-2 text-sm text-foreground/90">
                    <Check
                      className="mt-0.5 h-4 w-4 shrink-0 text-accent"
                      aria-hidden="true"
                    />
                    {f}
                  </li>
                ))}
              </ul>
              <a
                href={tier.href}
                className={`mt-8 inline-flex h-11 items-center justify-center gap-2 rounded-lg text-sm font-semibold transition-colors ${
                  tier.highlighted
                    ? "btn-glow bg-brand text-white hover:bg-brand-deep"
                    : "border border-border bg-surface-raised text-foreground hover:border-brand/40 hover:bg-white/5"
                }`}
              >
                {tier.cta}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </a>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

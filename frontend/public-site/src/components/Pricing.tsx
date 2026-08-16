"use client";

import { motion } from "framer-motion";
import { Check, ArrowRight } from "lucide-react";

const tiers = [
  {
    name: "Demo",
    price: "Ücretsiz",
    period: "keşif oturumu",
    description: "Operasyon konsolunu ve dinamik QR erişimini canlı görün.",
    features: [
      "Demo tenant ve yönetici paneli",
      "Üye, şube ve personel ekranları",
      "Kapı / turnike okuyucu (scanner) denemesi",
      "Teknik mimari & RLS walkthrough",
    ],
    cta: "Demoyu talep et",
    ariaLabel: "Ücretsiz keşif oturumu için demo talep edin",
    href: "mailto:hello@gymclubnex.com?subject=GymClubNex%20Demo",
    highlighted: false,
  },
  {
    name: "Operasyon",
    price: "Kurumsal",
    period: "kulüp ölçeğine göre",
    description: "Tek veya çok şubeli kulüpler için uçtan uca GymClubNex işletim paketi.",
    features: [
      "Sınırsız personel hesabı (rol bazlı)",
      "Dinamik QR + Turnike Tarayıcı PWA",
      "Kuruş hassasiyetinde faturalama & dunning",
      "Tenant veri izolasyonu ve denetim izi",
      "İş günü teknik destek",
    ],
    cta: "Teklif al",
    ariaLabel: "Kulüp ölçeğinize özel Operasyon paketi için teklif alın",
    href: "mailto:hello@gymclubnex.com?subject=GymClubNex%20Teklif",
    highlighted: true,
  },
  {
    name: "Ağ",
    price: "Özel",
    period: "çok kulüp / federasyon",
    description: "Zincir kulüpler ve federasyon yapıları için özel ölçeklendirme.",
    features: [
      "Çok tenantlı merkezi federasyon paneli",
      "Özel donanım & API entegrasyonları",
      "Sözleşmeli SLA (pentest kanıtı ayrıca planlanır)",
      "Özel yerinde veri göçü ve onboarding",
    ],
    cta: "İletişime geç",
    ariaLabel: "Zincir ve federasyonlar için özel Ağ paketi hakkında iletişime geçin",
    href: "mailto:hello@gymclubnex.com?subject=GymClubNex%20A%C4%9F%20Plan%C4%B1",
    highlighted: false,
  },
];

export function Pricing() {
  return (
    <section
      id="pricing"
      className="scroll-mt-20 border-t border-border bg-background py-24 sm:py-32"
    >
      <div className="mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-xs font-mono uppercase tracking-[0.1em] text-brand-light"
          >
            FİYATLANDIRMA
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.05 }}
            className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl text-white"
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
            Şeffaf başlangıç. Ölçek ve şube sayısına göre net kurumsal teklif.
          </motion.p>
        </div>

        <div className="mx-auto mt-14 grid max-w-5xl grid-cols-1 gap-6 lg:grid-cols-3">
          {tiers.map((tier, i) => (
            <motion.article
              key={tier.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06 }}
              className={`enterprise-card flex flex-col rounded-2xl p-7 ${
                tier.highlighted
                  ? "border-brand/60 ring-1 ring-brand/50 shadow-xl shadow-brand/10"
                  : ""
              }`}
            >
              {tier.highlighted && (
                <span className="mb-3 w-fit rounded-full border border-brand/40 bg-brand/20 px-3 py-0.5 text-xs font-mono font-semibold text-brand-light">
                  EN ÇOK TERCİH EDİLEN
                </span>
              )}
              <h3 className="text-xl font-bold text-white">
                {tier.name}
              </h3>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-3xl font-bold font-mono tracking-tight text-white">
                  {tier.price}
                </span>
                <span className="text-sm text-ink-muted">{tier.period}</span>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                {tier.description}
              </p>
              <ul className="mt-6 flex-1 space-y-3">
                {tier.features.map((f) => (
                  <li key={f} className="flex gap-2.5 text-sm text-slate-200">
                    <Check
                      className="mt-0.5 h-4 w-4 shrink-0 text-accent"
                      aria-hidden="true"
                    />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <a
                href={tier.href}
                aria-label={tier.ariaLabel}
                className={`mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-xl text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand ${
                  tier.highlighted
                    ? "btn-primary text-white"
                    : "btn-secondary text-white"
                }`}
              >
                {tier.cta}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </a>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}

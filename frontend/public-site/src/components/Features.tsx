"use client";

import { motion } from "framer-motion";
import {
  QrCode,
  MonitorSmartphone,
  CreditCard,
  Shield,
  Bell,
  BarChart3,
} from "lucide-react";

const features = [
  {
    name: "Dinamik QR geçiş",
    description:
      "Kısa ömürlü imzalı kodlar. Kopyalanamaz, paylaşılamaz — saniyeler içinde güvenli kapı erişimi.",
    icon: QrCode,
  },
  {
    name: "Merkezi yönetim",
    description:
      "Tüm şubeler tek ekranda. Üye, personel ve yetki yönetimi operasyon panelinizde.",
    icon: MonitorSmartphone,
  },
  {
    name: "Kesintisiz ödemeler",
    description:
      "Kuruluş para birimi ve minor unit ile faturalama. Mutabakat hatalarını azaltın.",
    icon: CreditCard,
  },
  {
    name: "Tam izolasyon",
    description:
      "Her kulüp kendi tenant alanında. PostgreSQL RLS ile satır düzeyinde veri ayrımı.",
    icon: Shield,
  },
  {
    name: "Bildirimler",
    description:
      "Olay tabanlı bildirim hattı. Üyelik ve operasyon sinyallerini doğru kanala iletin.",
    icon: Bell,
  },
  {
    name: "Raporlar",
    description:
      "Günlük operasyon özetleri ve finans görünürlüğü. Karar için net sayılar.",
    icon: BarChart3,
  },
];

export function Features() {
  return (
    <section
      id="features"
      className="relative scroll-mt-20 border-t border-border bg-background py-20 sm:py-28"
    >
      <div className="mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="text-sm font-semibold uppercase tracking-wider text-brand"
          >
            Çekirdek yetenekler
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
          >
            Telemetri ve donanım bir arada
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="mt-4 text-lg leading-relaxed text-ink-muted"
          >
            Klasik yazılımları unutun. Kulübünüzün her verisi ve erişim noktası
            aynı çekirdek sistemde birleşir.
          </motion.p>
        </div>

        <div className="mx-auto mt-14 grid max-w-2xl grid-cols-1 gap-5 sm:mt-16 sm:grid-cols-2 lg:max-w-none lg:grid-cols-3">
          {features.map((feature, index) => (
            <motion.div
              key={feature.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              className="flex flex-col rounded-xl border border-border bg-card p-6 transition-colors hover:border-brand/40"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-brand/20 bg-brand/10">
                <feature.icon
                  className="h-5 w-5 text-brand-light"
                  aria-hidden="true"
                />
              </div>
              <h3 className="mt-4 text-base font-semibold text-foreground">
                {feature.name}
              </h3>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-ink-muted">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

"use client";

import { motion } from "framer-motion";
import { QrCode, MonitorSmartphone, CreditCard } from "lucide-react";

const features = [
  {
    name: "Dinamik QR Geçiş",
    description: "Saniyeden kısa sürede doğrulama. Kopyalanamaz, paylaşılamaz, tamamen güvenli erişim.",
    icon: QrCode,
    color: "text-amber-400",
    bg: "bg-amber-400/10",
    border: "border-amber-400/20"
  },
  {
    name: "Merkezi Yönetim",
    description: "Tüm şubeler, tek ekran. Tam izolasyon. Üye, personel ve yetki yönetimi avucunuzun içinde.",
    icon: MonitorSmartphone,
    color: "text-brand",
    bg: "bg-brand/10",
    border: "border-brand/20"
  },
  {
    name: "Kesintisiz Ödemeler",
    description: "Sıfır hata, anında mutabakat. Karmaşık finansal operasyonları otomatiğe bağlayın.",
    icon: CreditCard,
    color: "text-accent",
    bg: "bg-accent/10",
    border: "border-accent/20"
  },
];

export function Features() {
  return (
    <section id="features" className="relative py-24 sm:py-32 bg-background border-t border-border">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-base font-semibold leading-7 text-brand"
          >
            Core Specs
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-2 text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
          >
            Telemetri ve Donanım
          </motion.p>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-6 text-lg leading-8 text-foreground/70"
          >
            Klasik yazılımları unutun. Kulübünüzün her donanımı ve verisi, kusursuz bir uyumla çalışan bu çekirdek sistemde birleşiyor.
          </motion.p>
        </div>
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
            {features.map((feature, index) => (
              <motion.div 
                key={feature.name} 
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="flex flex-col rounded-2xl bg-card p-8 border border-border hover:border-brand/50 transition-colors shadow-sm"
              >
                <dt className="flex items-center gap-x-3 text-lg font-semibold leading-7 text-foreground">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${feature.bg} ${feature.border} border`}>
                    <feature.icon className={`h-6 w-6 ${feature.color}`} aria-hidden="true" />
                  </div>
                  {feature.name}
                </dt>
                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-foreground/70">
                  <p className="flex-auto">{feature.description}</p>
                </dd>
              </motion.div>
            ))}
          </dl>
        </div>
      </div>
    </section>
  );
}

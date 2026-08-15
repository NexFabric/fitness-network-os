"use client";

import { motion } from "framer-motion";
import {
  QrCode,
  MonitorSmartphone,
  CreditCard,
  ShieldCheck,
  Bell,
  BarChart3,
  Sparkles,
} from "lucide-react";

export function Features() {
  return (
    <section
      id="features"
      className="relative scroll-mt-20 border-t border-border bg-background py-24 sm:py-32"
    >
      <div className="mx-auto max-w-7xl px-5 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="text-xs font-mono uppercase tracking-[0.1em] text-brand-light"
          >
            ÇEKİRDEK YETENEKLER
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl"
          >
            Donanım, erişim ve finans tek çekirdekte
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="mt-4 text-lg leading-relaxed text-ink-muted"
          >
            Klasik yazılımları unutun. Kulübünüzün her verisi, turnike donanımı ve mali akışı
            aynı çekirdek sistemde birleşir.
          </motion.p>
        </div>

        {/* Asymmetrical Bento Grid */}
        <div className="mx-auto mt-14 grid max-w-6xl grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {/* Bento Card 1 (Span 2 cols on Desktop): Dynamic QR */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="enterprise-card sm:col-span-2 rounded-2xl p-7 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-brand/30 bg-brand/10">
                  <QrCode className="h-5 w-5 text-brand-light" aria-hidden="true" />
                </div>
                <span className="rounded-full border border-brand/30 bg-brand/10 px-3 py-1 font-mono text-xs text-brand-light">
                  KMS Envelope Encryption
                </span>
              </div>
              <h3 className="mt-5 text-xl font-bold text-white">
                Dinamik İmzalı QR & Turnike Entegrasyonu
              </h3>
              <p className="mt-2.5 max-w-xl text-sm leading-relaxed text-ink-muted">
                Kısa ömürlü, zaman damgalı ve HMAC imzalı kodlar. Ekran görüntüsüyle kopyalanamaz, paylaşılamaz. Replay koruması ve offline fail-closed güvenlik mimarisiyle saniyeler içinde geçiş.
              </p>
            </div>
            <div className="mt-6 flex flex-wrap gap-2 pt-4 border-t border-border/50">
              {["TOTP / HMAC İmzalı", "Anti-Replay Koruması", "Fail-Closed Güvenlik", "PWA Tarayıcı"].map((tag) => (
                <span key={tag} className="rounded-md border border-border bg-surface-raised/80 px-2.5 py-1 text-xs text-slate-300 font-mono">
                  {tag}
                </span>
              ))}
            </div>
          </motion.div>

          {/* Bento Card 2: Multi-Tenant RLS */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.08 }}
            className="enterprise-card rounded-2xl p-7 flex flex-col justify-between"
          >
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-accent/30 bg-accent/10">
                <ShieldCheck className="h-5 w-5 text-accent" aria-hidden="true" />
              </div>
              <h3 className="mt-5 text-lg font-bold text-white">
                PostgreSQL RLS İzolasyonu
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                Her kulüp kendi veri alanında. Veritabanı düzeyinde Row-Level Security politikalarıyla sıfır sızıntı garantisi.
              </p>
            </div>
            <div className="mt-6 font-mono text-xs text-accent">
              ✓ %100 Multi-Tenant İzolasyon
            </div>
          </motion.div>

          {/* Bento Card 3: Centralized Management */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.12 }}
            className="enterprise-card rounded-2xl p-7 flex flex-col justify-between"
          >
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-brand/30 bg-brand/10">
                <MonitorSmartphone className="h-5 w-5 text-brand-light" aria-hidden="true" />
              </div>
              <h3 className="mt-5 text-lg font-bold text-white">
                Merkezi Çok Şubeli Yönetim
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                Tüm şubeler ve antrenörler tek ekranda. Şube bazlı rol ve yetki matrisiyle tam yetki denetimi.
              </p>
            </div>
            <div className="mt-6 font-mono text-xs text-brand-light">
              ✓ Rol Bazlı RBAC & Kapsam
            </div>
          </motion.div>

          {/* Bento Card 4: Minor Unit Financial Engine */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.16 }}
            className="enterprise-card rounded-2xl p-7 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-brand/30 bg-brand/10">
                  <CreditCard className="h-5 w-5 text-brand-light" aria-hidden="true" />
                </div>
                <span className="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 font-mono text-xs text-accent">
                  Sıfır Yuvarlama Hatası
                </span>
              </div>
              <h3 className="mt-5 text-lg font-bold text-white">
                Kuruş Hassasiyetinde Finans
              </h3>
              <p className="mt-2.5 text-sm leading-relaxed text-ink-muted">
                Tüm mali hesaplamalar tamsayı kuruş ile yapılır. Otomatik dunning hatırlatmaları ve anlık mutabakat geçmişi.
              </p>
            </div>
            <div className="mt-6 font-mono text-xs text-accent">
              ✓ %100 Tamsayı Kuruş
            </div>
          </motion.div>

          {/* Bento Card 5 (Span 2 cols on Desktop): Group Class & PT Booking Engine */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="enterprise-card sm:col-span-2 rounded-2xl p-7 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-accent/30 bg-accent/10">
                  <BarChart3 className="h-5 w-5 text-accent" aria-hidden="true" />
                </div>
                <span className="rounded-full border border-accent/30 bg-accent/10 px-3 py-1 font-mono text-xs text-accent">
                  Pessimistic Concurrency Lock
                </span>
              </div>
              <h3 className="mt-5 text-xl font-bold text-white">
                Grup Dersi & PT Takvimi, Dinamik Yedek Sırası & Canlı Yoklama
              </h3>
              <p className="mt-2.5 max-w-xl text-sm leading-relaxed text-ink-muted">
                Sıfır çifte rezervasyon garantisi. Kontenjan dolduğunda otomatik FIFO yedek sırası, iptallerde anında asil listeye terfi, antrenör canlı yoklama defteri ve 1-on-1 PT randevu yönetimi.
              </p>
            </div>
            <div className="mt-6 flex flex-wrap gap-2 pt-4 border-t border-border/50">
              {["Pessimistic Lock (SELECT FOR UPDATE)", "Otomatik Yedek Terfisi", "Kayan Yoklama Çekmecesi", "1-on-1 PT Planlama"].map((tag) => (
                <span key={tag} className="rounded-md border border-border bg-surface-raised/80 px-2.5 py-1 text-xs text-slate-300 font-mono">
                  {tag}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

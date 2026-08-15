import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Hizmet Şartları",
  description: "GymClubNex SaaS platform kullanım ve hizmet sözleşmesi şartları.",
  alternates: {
    canonical: "/terms",
  },
};

export default function TermsPage() {
  return (
    <article className="min-h-screen bg-background py-20 px-5 sm:px-6 lg:px-8 text-foreground">
      <div className="mx-auto max-w-4xl">
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Hizmet ve Kullanım Şartları
        </h1>
        <p className="mt-2 text-sm text-ink-muted">
          Son güncelleme: 14 Ağustos 2026
        </p>

        <div className="mt-8 space-y-8 text-sm leading-relaxed text-ink-muted">
          <section>
            <h2 className="text-lg font-semibold text-foreground">1. Taraflar ve Hizmetin Niteliği</h2>
            <p className="mt-2">
              İşbu Kullanım Şartları (&quot;Sözleşme&quot;), GymClubNex bulut tabanlı fitness ağ işletim sistemini (&quot;Platform&quot;) kullanan spor kulüpleri, işletmeciler ve yetkili personel (&quot;Müşteri&quot; veya &quot;Kullanıcı&quot;) ile GymClubNex arasındaki hukuki şartları belirler.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">2. Hizmet Kapsamı ve Lisans</h2>
            <p className="mt-2">
              GymClubNex, Müşteri&apos;ye abonelik süresi boyunca geçerli olmak üzere münhasır olmayan, devredilemez bir bulut yazılım erişim hakkı (SaaS) tanır. Hizmet kapsamı; üye yönetimi, erişim kontrolü/turnike entegrasyonu, finansal kayıt yönetimi ve raporlama araçlarını içerir.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">3. Hesap Güvenliği ve Yetkili Kullanım</h2>
            <p className="mt-2">
              Müşteri, platforma erişim sağlayan yönetici ve personel hesaplarının güvenliğinden (güçlü parola kullanımı, iki faktörlü kimlik doğrulama - MFA aktifliği) sorumludur. Giriş anahtarları ve oturum belirteçleri üçüncü kişilerle paylaşılamaz.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">4. Hizmet Seviyesi (SLA) ve Kesintisizlik</h2>
            <p className="mt-2">
              GymClubNex, platformun yıllık bazda %99.9 erişilebilirlik (SLA) standardında çalışmasını hedefler. Planlı bakım çalışmaları önceden bildirilir. Ağ veya sunucu bağlantısının bulunmadığı durumlarda turnikeler ve erişim cihazları, tesis güvenliğini korumak amacıyla fail-closed (erişim kapalı) mimaride çalışır ve yetkisiz geçişlere izin verilmez.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">5. Fikri Mülkiyet ve Müşteri Verisi Mülkiyeti</h2>
            <p className="mt-2">
              Platformun kaynak kodları, algoritmaları, tasarımları ve markası münhasıran GymClubNex&apos;e aittir. Müşteri tarafından sisteme yüklenen tüm üye verileri, finansal veriler ve log kayıtları tamamen Müşteri&apos;nin mülkiyetindedir; sözleşme bitiminde talep halinde veri aktarımı sağlanır ve yasal saklama süreleri ile veri imha politikaları uyarınca güvenli biçimde anonimleştirilir veya silinir.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">6. Yürürlük ve Fesih</h2>
            <p className="mt-2">
              Abonelik süresi sonunda taraflar sözleşmeyi yenileyebilir veya 30 gün önceden bildirmek kaydıyla feshedebilir. Sözleşme şartlarının ağır ihlali durumunda hizmet tek taraflı olarak askıya alınabilir.
            </p>
          </section>
        </div>
      </div>
    </article>
  );
}

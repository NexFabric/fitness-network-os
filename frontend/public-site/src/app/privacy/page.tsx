import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Gizlilik Politikası",
  description: "GymClubNex veri işleme, gizlilik ve çerez ilkeleri.",
};

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-background py-20 px-5 sm:px-6 lg:px-8 text-foreground">
      <div className="mx-auto max-w-4xl">
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Gizlilik Politikası ve Çerez İlkeleri
        </h1>
        <p className="mt-2 text-sm text-ink-muted">
          Son güncelleme: 14 Ağustos 2026
        </p>

        <div className="mt-8 space-y-8 text-sm leading-relaxed text-ink-muted">
          <section>
            <h2 className="text-lg font-semibold text-foreground">1. Giriş ve Kapsam</h2>
            <p className="mt-2">
              GymClubNex (&quot;Platform&quot;, &quot;biz&quot; veya &quot;hizmet sağlayıcı&quot;), spor kulüpleri ve tesis işletmeleri için çok kiracılı (multi-tenant) bir kulüp işletim sistemi sunmaktadır. Bu Gizlilik Politikası, platformumuzu ziyaret eden kullanıcıların ve spor kulüplerine üye olan sporcuların kişisel verilerinin nasıl işlendiğini ve korunduğunu açıklamaktadır.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">2. Veri Sorumlusu ve Veri İşleyen Sıfatı</h2>
            <p className="mt-2">
              Platformumuzda iki farklı veri işleme rolü bulunmaktadır:
            </p>
            <ul className="mt-2 list-disc pl-5 space-y-1">
              <li>
                <strong className="text-foreground">Doğrudan Ziyaretçiler ve Hesap Sahipleri:</strong> GymClubNex web sitesini ziyaret eden veya platform hesabı açan kulüp yöneticileri için veri sorumlusudur.
              </li>
              <li>
                <strong className="text-foreground">Spor Kulübü Üyeleri (Sporcular):</strong> Kulüp üyelerinin kimlik, abonelik ve geçiş verileri bakımından ilgili Spor Kulübü <em>Veri Sorumlusu</em>, GymClubNex ise bulut altyapısını sağlayan <em>Veri İşleyen</em> sıfatındadır.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">3. İşlenen Kişisel Veriler ve Amaçları</h2>
            <p className="mt-2">
              Platform aracılığıyla aşağıdaki veri kategorileri toplanabilir:
            </p>
            <ul className="mt-2 list-disc pl-5 space-y-1">
              <li><strong>Kimlik ve İletişim Bilgileri:</strong> Ad, soyad, e-posta adresi, telefon numarası.</li>
              <li><strong>Kulüp ve Üyelik Bilgileri:</strong> Üyelik tipi, başlangıç/bitiş tarihleri, bakiye ve hak kullanım bilgileri.</li>
              <li><strong>Erişim ve Güvenlik Kayıtları:</strong> Turnike ve kapı geçiş logları, QR erişim doğrulama kayıtları, IP adresi ve oturum verileri.</li>
              <li><strong>Finansal Kayıtlar:</strong> Fatura geçmişi, ödeme referansları ve tahsilat durumu (Kart bilgileri platformumuzda saklanmaz; PCI-DSS uyumlu ödeme sağlayıcıları tarafından işlenir).</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">4. Veri İzolasyonu ve Güvenlik Tedbirleri</h2>
            <p className="mt-2">
              GymClubNex, kurumsal düzeyde çok kiracılı mimari (PostgreSQL Row-Level Security - RLS) kullanmaktadır. Her spor kulübünün verisi veritabanı seviyesinde izole edilmiştir ve hiçbir kulüp bir diğer kulübün verisine erişemez. Tüm veri aktarımları TLS 1.3 ile şifrelenir ve dinlenmeye karşı korunur.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">5. Çerezler (Cookies)</h2>
            <p className="mt-2">
              Web sitemizde yalnızca uygulamanın güvenli şekilde çalışması için zorunlu olan oturum çerezleri (session cookies) ve güvenlik belirteçleri (CSRF tokens) kullanılmaktadır. Üçüncü taraf reklam veya izleme çerezleri barındırılmaz.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">6. İletişim</h2>
            <p className="mt-2">
              Gizlilik politikamızla ilgili soru ve talepleriniz için{" "}
              <a href="mailto:privacy@gymclubnex.com" className="text-brand underline hover:text-brand-dark">
                privacy@gymclubnex.com
              </a>{" "}
              adresi üzerinden bizimle iletişime geçebilirsiniz.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "KVKK Aydınlatma Metni",
  description: "6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) uyarınca Aydınlatma Metni.",
  alternates: {
    canonical: "/kvkk",
  },
};

export default function KvkkPage() {
  return (
    <article className="min-h-screen bg-background py-20 px-5 sm:px-6 lg:px-8 text-foreground">
      <div className="mx-auto max-w-4xl">
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          KVKK Aydınlatma Metni
        </h1>
        <p className="mt-2 text-sm text-ink-muted">
          6698 Sayılı Kişisel Verilerin Korunması Kanunu Kapsamında Bilgilendirme
        </p>

        <div className="mt-8 space-y-8 text-sm leading-relaxed text-ink-muted">
          <section>
            <h2 className="text-lg font-semibold text-foreground">1. Veri Sorumlusunun Kimliği</h2>
            <p className="mt-2">
              6698 sayılı Kişisel Verilerin Korunması Kanunu (&quot;KVKK&quot;) uyarınca, GymClubNex olarak, veri sorumlusu sıfatıyla, kişisel verilerinizi aşağıda açıklanan amaçlar ve hukuki sebepler çerçevesinde işlemekteyiz.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">2. Kişisel Verilerin İşlenme Amaçları</h2>
            <p className="mt-2">
              Toplanan kişisel verileriniz;
            </p>
            <ul className="mt-2 list-disc pl-5 space-y-1">
              <li>Platform abonelik ve kullanıcı hesaplarının oluşturulması ve yönetilmesi,</li>
              <li>Spor salonu operasyonlarının, üye kayıtlarının ve erişim kontrolünün sağlanması,</li>
              <li>Hizmet güvenliğinin, bilgi güvenliği süreçlerinin ve yasal denetim gereksinimlerinin karşılanması,</li>
              <li>Müşteri destek taleplerinin karşılanması ve iletişim süreçlerinin yürütülmesi</li>
            </ul>
            <p className="mt-2">
              amaçlarıyla KVKK&apos;nın 5. ve 6. maddelerinde belirtilen kişisel veri işleme şartları dahilinde işlenmektedir.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">3. Kişisel Veri Toplamanın Yöntemi ve Hukuki Sebebi</h2>
            <p className="mt-2">
              Kişisel verileriniz, web sitemiz, mobil uyumlu yönetim panelleri, API entegrasyonları ve turnike tarayıcı donanımları vasıtasıyla elektronik ortamda toplanmaktadır. Bu veriler, &quot;Bir sözleşmenin kurulması veya ifasıyla doğrudan doğruya ilgili olması&quot;, &quot;Veri sorumlusunun hukuki yükümlülüğünü yerine getirebilmesi için zorunlu olması&quot; ve &quot;İlgili kişinin temel hak ve özgürlüklerine zarar vermemek kaydıyla, veri sorumlusunun meşru menfaatleri için veri işlenmesinin zorunlu olması&quot; hukuki sebeplerine dayalı olarak işlenmektedir.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">4. İlgili Kişinin Hakları (Madde 11)</h2>
            <p className="mt-2">
              KVKK&apos;nın 11. maddesi uyarınca veri sahipleri;
            </p>
            <ul className="mt-2 list-disc pl-5 space-y-1">
              <li>Kişisel verilerinin işlenip işlenmediğini öğrenme,</li>
              <li>Kişisel verileri işlenmişse buna ilişkin bilgi talep etme,</li>
              <li>Kişisel verilerin işlenme amacını ve bunların amacına uygun kullanılıp kullanılmadığını öğrenme,</li>
              <li>Yurt içinde veya yurt dışında kişisel verilerin aktarıldığı üçüncü kişileri bilme,</li>
              <li>Kişisel verilerin eksik veya yanlış işlenmiş olması hâlinde bunların düzeltilmesini isteme,</li>
              <li>KVKK 7. maddesinde öngörülen şartlar çerçevesinde kişisel verilerin silinmesini veya yok edilmesini isteme</li>
            </ul>
            <p className="mt-2">
              haklarına sahiptir.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-foreground">5. Başvuru ve İletişim</h2>
            <p className="mt-2">
              KVKK kapsamındaki haklarınıza ilişkin taleplerinizi, kimliğinizi tevsik edici belgeler ile birlikte{" "}
              <a href="mailto:kvkk@gymclubnex.com" className="text-brand underline hover:text-brand-deep">
                kvkk@gymclubnex.com
              </a>{" "}
              e-posta adresine iletebilirsiniz. Talepleriniz en geç 30 gün içinde ücretsiz olarak sonuçlandırılacaktır.
            </p>
          </section>
        </div>
      </div>
    </article>
  );
}

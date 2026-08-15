# Devir Notu — 2026-08-13

Bu dosya, projeyi devralan kişi ya da ajan için **tek giriş noktasıdır**. Diğer
dökümanlar detayı taşır; buradaki tablo nerede duracağını söyler.

**Branch:** `feat/production-readiness-deep-dive-hardening` · **Alembic head:** `x8b9c0d1e2f3` · **Deep-Dive Production Hardening & Full Pillars 1-10:** Completed & Audited.

---

## Önce şunu oku

| Ne arıyorsan | Dosya |
|---|---|
| Kod nerede (rota/model/dosya haritası) | `.codesight/wiki/index.md` — ~200 token, AST'den üretilir, pre-commit ile tazelenir |
| Ne yapıldı / ne yapılmadı (**otorite**) | `docs/PROGRESS_CHECKLIST.md` |
| Kalan iş listesi | `backend/docs/plans/REMAINING_WORK_BOARD.md` |
| Sistem mimarisi ve kararların **gerekçeleri** | `docs/ARCHITECTURE.md` |
| Mimari kararlar | `docs/adr/` (ADR-043 federasyon okuma, ADR-044 cihaz imzalama) |
| Güvenlik öz-değerlendirmesi | `docs/ops/ASVS_L2_COMPLIANCE_REPORT.md` |
| Yerel ortamı ayağa kaldırma | `READY_TO_RUN.md` |
| Kurallar / mühendislik sözleşmesi | `AGENTS.md` |

`.codesight` haritası **nerede** olduğunu söyler, **nasıl çalıştığını** değil —
değiştirmeden önce daima kaynağı oku.

---

## Şu an ne durumda

Phase 0–27.4 + Waves 1–3 ve Deep-Dive Production Hardening tamamlandı:
- **Outbox & Worker RLS İzolasyonu:** Outbox event handler registry (`notification.requested.v1`, `report.run.requested.v1`), tüm worker'larda (`outbox`, `notification`, `report`, `retention`) tenant RLS bağlamı (`current_tenant_id_var` + `SET LOCAL app.current_tenant_id`).
- **QR KMS Zarf Şifreleme:** `kms:enc:` ile `GenerateDataKey` & `Decrypt` deterministik anahtar çözümü, production ayar doğrulama kontrolü.
- **Break-Glass Yetki Denetimi:** `deps.py:get_tenant_id` içinde doğrudan UserRole'ü olmayan superuser erişimlerinde aktif `BreakGlassSession` zorunluluğu ve audit kaydı.
- **Dunning & Ödeme Denemeleri:** `FinanceService` içinde `PaymentAttempt` kaydı, `DunningPolicy` otomatik yeniden deneme takvimi ve aşım yönetimi.
- **Periyodik Veri İmha Worker'ı:** `app.workers.retention` ve `docker-compose.prod.yml` entegrasyonu ile otomatik KVKK/GDPR veri anonimleştirme/silme.
- **Sözleşme & Scanner Uyumu:** `terms/page.tsx` içinde offline turnike fail-closed (erişim kapalı) mimari teyidi.
- **Genişletilmiş E2E Testleri:** Resepsiyon arama/override, CSV veri göçü yükleme/önizleme ve 5 sekmeli üye portalı Playwright akışları.

**Kanıt durumu:** Gerçek PostgreSQL DB üzerinde 357 test passed · 1 skipped ve Playwright E2E testleri 39/39 (0 hata) ile yeşil.

Önceki dalgalar:

| PR / Dalga | İş |
|---|---|
| Wave 1–3 | Legal sayfalar, üye self-servis, adli turnike kararları, resepsiyon masası, KPI motoru, CSV veri göçü, dunning ve onboarding |
| #49 | Cihaz kanalı HMAC imzalama + tek kullanımlık nonce (ADR-044), scanner non-extractable CryptoKey, RBAC portalları, PWA ikonları |
| #50 | Post-merge doküman gerçeği, SBOM job'ının CI kapısından ayrılması |
| #51 | Redis tabanlı login rate limit, ölü idempotency stub'ının silinmesi |
| #52 | Operasyon konsolu: cihazlar, bildirimler, raporlar, personel, şube düzenleme, üyelik yaşam döngüsü |
| #53 | Plan kataloğu + abonelik oluşturma (API-1), gönderim/çalıştırma geçmişi (API-2), `.codesight` haritası |
| #55 | Phase 27.4 final closure: privileged MFA, private S3 rapor storage, gerçek metrics, frozen non-root image, required Playwright gate |
| #57 | Personel hesabı açma ucu + tek kullanımlık parola, zorunlu rotasyon (`password_reset` session), enrollment/rotation sıralaması |

**Test tabanı:** closure CI'da backend 315 passed · 1 skipped, Playwright 36 passed
(gerçek Chromium + gerçek backend). Kapılar: ruff, mypy, `alembic check`,
`check_tenancy`, `check_permissions`, `check_permissions_db`,
`check_no_money_floats`, 3 frontend build, CodeQL.

---

## Sıradaki iş (yapılabilir olanlar)

1. **Uygulamayı gerçek ortamda elle doğrulamak** — bugüne kadarki bütün kanıt CI'dan
   geliyor; hiç kimse ürünü tarayıcıda uçtan uca kullanmadı. `READY_TO_RUN.md` ile
   stack'i kaldır, en az şu akışları geç: privileged login → MFA enrollment →
   üyelik oluşturma → QR ile giriş → rapor çalıştırma ve indirme.
2. **Observability altyapısını bağlamak** — `/metrics` gerçek Prometheus metrikleri
   üretir; scraper, dashboard, alert ve trace backend'i dış altyapı işi olarak açıktır.
3. **E-posta davet akışı** — hesap açma bugün tek kullanımlık parolayı ekranda
   gösteriyor ve yönetici parolayı elden iletiyor. Token tablosu + şablon + public
   uç ile davet bağlantısına çevrilebilir; çalışan akışı bozmayan bir iyileştirme.

## Bu makineden kapatılamayanlar (sebebiyle)

| Madde | Neden |
|---|---|
| P1-3b runtime doğrulaması | Adapter hazır; gerçek S3/MinIO kovası ve kimlik bilgisiyle staging kanıtı gerekiyor |
| P2-3 QR sırları için KMS | Sağlayıcı SDK'sı + anahtar politikası gerekiyor; `qr_crypto.py` KMS referansını tanır, bilinçli `NotImplementedError` verir |
| P1-10 yedekten dönüş tatbikatı | Gerçek altyapıda koşup kanıtlanması gereken ops prosedürü |
| P1-11 / Phase 26 dış pentest + bağımsız onay | Tanımı gereği dışarıdan gelmeli |

**Proje production-ready DEĞİL.** Phase 26 çıkış kapısı geçilmedi ve ASVS raporu
**öz-değerlendirmedir**, denetim sonucu değildir. Pazarlama veya canlıya alma
kararı bu iki kanıt gelmeden verilmemelidir.

---

## Bilmen gereken tuzaklar

### PR #55 (merged) çalışma özeti — sonraki ajan için

| Alan | Yapılan |
|---|---|
| Auth | Privileged roller için password-only erişim kapatıldı; 10 dakikalık MFA setup session, Türkçe enrollment UI, TOTP/recovery ve başarılı kayıt sonrası yeni full session token |
| Reports | Production local disk yasaklandı; S3/MinIO upload, SSE/KMS seçeneği, tenant-bound key, presigned download, cleanup ve opaque local dev URI |
| Ops | Gerçek Prometheus request/dependency/outbox metrikleri; production config fail-closed notification/storage/metrics kontrolleri |
| Image/CI | Frozen `uv.lock`, pinned base digest, non-root image, healthcheck, required image build ve real backend/Postgres/Redis Playwright gate |
| Security | CodeQL path-expression bulgusu UUID-derived local namespace ile; cookie bulgusu MFA session rotation ile kapatıldı |
| Truth | Phase 26 false PASS kaldırıldı; ASVS 5.0 hazırlık öz-değerlendirmesi ile dış pentest/DR kanıtı ayrıldı |

**Önemli commitler:** `9b46162` ana closure, `4165034` migration metadata,
`4859498` auth fixture/action upgrades, `703994e` MFA E2E wait, `5e47810`
CodeQL hardening, `6dde88b` storage contract testi, `53cbb15` ve sonraki
doküman eşitlemeleri. **Yerelde test çalıştırılmadı; yalnız GitHub CI kullanıldı.**

Restore/PITR, gerçek S3 staging kanıtı, scraper/alert/trace kurulumu ve bağımsız
pentest **kodla tamamlanmış sayılmaz** — bunlar dış kanıt gerektirir.

- **`main` korumalı:** 1 onaylayan review + `enforce_admins` açık, 3 required check,
  `strict` (branch güncel olmalı), force-push/deletion kapalı. Repoda tek
  collaborator olduğu için review şartı karşılanamaz; GitHub kendi PR'ını
  onaylatmaz. Merge için ya ikinci bir insan gerekir ya da review sayısı geçici
  0 yapılıp **birebir** geri yüklenir — `enforce_admins` ve CI kapılarına asla
  dokunmadan, geri yükleme mutlaka doğrulanarak. Bu dansı her PR'da tekrar etmek
  istemiyorsan kalıcı çözüm review sayısını 0'a çekip gerçek kapıyı yeşil CI +
  `enforce_admins` olarak bırakmaktır; solo repoda dürüst olan da budur.
- **Login rate limit gerçektir.** Paralel tarayıcı suite'i paylaşılan hesaplarla
  20/dk bütçesini aşıp login'de patlar. Dev stack `RATE_LIMIT_LOGIN_MAX_REQUESTS=500`
  ile çalışır (`docker-compose.yml`); production sıkı varsayılanı korur.
- **`_seed_user` paylaşılan `GYM_OWNER` rolünü verir.** Testinde rolün izinlerini
  değiştirme — kendi özel rolünü kur, yoksa kardeş testleri çalışma sırasına göre
  kırarsın.
- **`members:read` ucu açar, `members:read:all` satırları açar.** İkincisi yoksa
  çağıran antrenör kapsamına düşer ve 403 alır; bu izin hatası değil, tasarımdır.
- **Cihaz kanalı imza ister.** `device_session` cookie'si tek başına yetmez;
  `X-Device-Signature/Timestamp/Nonce` zorunludur (ADR-044). Eşleştirme adımları
  `READY_TO_RUN.md`'de.
- **Para uçtan uca tam sayı kuruştur.** ORM'de float para alanı CI tarafından
  bloke edilir.

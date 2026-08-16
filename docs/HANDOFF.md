# Devir Notu — 2026-08-15

Bu dosya, projeyi devralan kişi ya da ajan için **tek giriş noktasıdır**. Diğer
dökümanlar detayı taşır; buradaki tablo nerede duracağını söyler.

**Branch:** `feat/public-site-modernization-and-seo` · **Alembic head:** `xe6f7a8b9c0d` · Phase 29 + invite + HAND-1 e2e + DSAR export/erasure + god-page split.

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

Grup Dersi & PT Takvimi / Rezervasyon Motoru (Milestone B1) ve Phase 0–27.4 + Waves 1–3 tamamlandı:
- **Veritabanı & RLS Güvenliği (`xa2b3c4d5e6f`):** 6 yeni tablo (`class_types`, `class_schedules`, `class_sessions`, `class_bookings`, `trainer_availabilities`, `pt_appointments`) `TenantMixin` ve PostgreSQL RLS politikaları ile izole edildi. 11 yeni RBAC izni tanımlandı.
- **Pessimistik Eşzamanlılık & Rezervasyon Motoru:** `SELECT ... FOR UPDATE` ile kapasite aşımını önleme, FIFO ardışık yedek sırası, iptal anında 1. sıradaki yedeğin otomatik asil listeye terfi edilmesi (`auto-promotion`), 1-on-1 PT randevu çakışma önleme kilidi ve Outbox event yayını.
- **Frontend Arayüzleri:**
  1. `📅 Grup Dersi & PT Takvimi (Classes.tsx)`: 4 sekmeli takvim, görsel seans kartları, doluluk çubuğu, seans planlama modalları ve kayan yoklama çekmecesi (Attendee Roster Drawer).
  2. `🏋️ Antrenör Portalı (TrainerPortal.tsx)`: Grup dersleri ve birebir PT seansları canlı yoklama defteri.
  3. `📱 Sporcu Portalı (MemberPortal.tsx)`: 6 sekmeli portal, 7 günlük seans filtreleri, kontenjan durumu, tek tıkla rezervasyon, yedek sırası takibi ve PT randevusu alma.
- **Doğrulama & Testler:** Gerçek PostgreSQL concurrency pytest testleri (5/5), Playwright E2E (`classes_and_booking_flows.spec.ts`, `console_clean.spec.ts`) ve 7/7 statik araçlar (0 hata) ile yeşil.

Önceki dalgalar:

| PR / Dalga | İş |
|---|---|
| Milestone B1 | Grup Dersi & PT Takvimi, kapasite yönetimi, dinamik yedek sırası, yoklama çekmecesi |
| Fed HQ | 6 sekmeli kurumsal federasyon HQ konsolu, kulüp yaşam döngüsü, pasaport dolaşımı, denetim & duyurular |
| #60 | Production hardening, outbox RLS worker, fail-closed KMS, reception override & CSV import E2E |
| Wave 1–3 | Legal sayfalar, üye self-servis, adli turnike kararları, resepsiyon masası, KPI motoru, CSV veri göçü, dunning ve onboarding |
| #49 | Cihaz kanalı HMAC imzalama + tek kullanımlık nonce (ADR-044), scanner non-extractable CryptoKey, RBAC portalları, PWA ikonları |
| #50 | Post-merge doküman gerçeği, SBOM job'ının CI kapısından ayrılması |
| #51 | Redis tabanlı login rate limit, ölü idempotency stub'ının silinmesi |
| #52 | Operasyon konsolu: cihazlar, bildirimler, raporlar, personel, şube düzenleme, üyelik yaşam döngüsü |
| #53 | Plan kataloğu + abonelik oluşturma (API-1), gönderim/çalıştırma geçmişi (API-2), `.codesight` haritası |
| #55 | Phase 27.4 final closure: privileged MFA, private S3 rapor storage, gerçek metrics, frozen non-root image, required Playwright gate |
| #57 | Personel hesabı açma ucu + tek kullanımlık parola, zorunlu rotasyon (`password_reset` session), enrollment/rotation sıralaması |

**Test tabanı:** GitHub CI ve lokalde backend pytest + Playwright
(gerçek Chromium + gerçek backend). Kapılar: ruff, mypy, `alembic check`,
`check_tenancy`, `check_permissions`, `check_permissions_db`,
`check_no_money_floats`, 3 frontend build. CodeQL workflow bu repoda yok
(HANDOFF bunu kapı diye saymaz).

---

## Sıradaki iş (yapılabilir olanlar)

1. **HAND-1 insan imzası** — tutanak `docs/ops/HAND1_BROWSER_PROOF.md`. Playwright
   invite / onboarding / portal / scanner / rapor linkini kapsar; insan onayı açık.
2. **Observability / S3 / PITR / pentest / KMS IAM** — dış kanıt; kod fail-closed.

## Bu makineden kapatılamayanlar (sebebiyle)

| Madde | Neden |
|---|---|
| P1-3b runtime doğrulaması | Adapter hazır; gerçek S3/MinIO kovası ve kimlik bilgisiyle staging kanıtı gerekiyor |
| P2-3 QR sırları için **üretim** KMS politikası | `qr_crypto.py` `kms:enc:` GenerateDataKey/Decrypt yolunu içerir; IAM/alias/rotation ve canlı decrypt kanıtı AWS tarafındadır |
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

# Devir Notu — 2026-08-13

Bu dosya, projeyi devralan kişi ya da ajan için **tek giriş noktasıdır**. Diğer
dökümanlar detayı taşır; buradaki tablo nerede duracağını söyler.

**Main HEAD:** `c015748` · **Closure PR:** [#55](https://github.com/NexFabric/fitness-network-os/pull/55) (`codex/phase27-production-closure`) · **Closure Alembic head:** `v5c6d7e8f9a0`.

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

Phase 0–27.3 `main`'de. Final production-closure kodu PR #55'te review bekliyor.
PR #55'in GitHub CI koşusunda backend **315 passed · 1 skipped**, Playwright
**36 passed**, tüm build/security/image kapıları yeşil oldu (run `31702800041`).
Sonraki CodeQL hardening değişikliklerinde Python, JS/TS ve Actions analizleri de
yeşil oldu (run `31703676406`). Yerelde test çalıştırılmadı.

Önceki dalgalar:

| PR | İş |
|---|---|
| #49 | Cihaz kanalı HMAC imzalama + tek kullanımlık nonce (ADR-044), scanner non-extractable CryptoKey, RBAC portalları, PWA ikonları |
| #50 | Post-merge doküman gerçeği, SBOM job'ının CI kapısından ayrılması |
| #51 | Redis tabanlı login rate limit, ölü idempotency stub'ının silinmesi |
| #52 | Operasyon konsolu: cihazlar, bildirimler, raporlar, personel, şube düzenleme, üyelik yaşam döngüsü |
| #53 | Plan kataloğu + abonelik oluşturma (API-1), gönderim/çalıştırma geçmişi (API-2), `.codesight` haritası |

**Test tabanı:** closure CI'da backend 315 passed · 1 skipped, Playwright 36 passed
(gerçek Chromium + gerçek backend). Kapılar: ruff, mypy, `alembic check`,
`check_tenancy`, `check_permissions`, `check_permissions_db`,
`check_no_money_floats`, 3 frontend build, CodeQL.

---

## Sıradaki iş (yapılabilir olanlar)

1. **PR #55 için bağımsız review alıp merge etmek** — privileged MFA enrollment,
   S3 rapor storage, metrics, container hardening ve required Playwright gate hazır.
2. **Kullanıcı hesabı açma ucu** — Personel ekranı bugün yalnızca *var olan*
   kullanıcıyı bağlayabiliyor; hesap oluşturan bir uç yok.
3. **Observability altyapısını bağlamak** — `/metrics` gerçek Prometheus metrikleri
   üretir; scraper, dashboard, alert ve trace backend'i dış altyapı işi olarak açıktır.

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

### PR #55 çalışma özeti — sonraki ajan için

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

Sonraki ajan önce PR #55 check'lerini ve review durumunu okumalı; yeşil required
checks + bağımsız review olmadan merge etmemeli. Merge sonrası `main` SHA/Alembic
head ve CI run linkini bu dosya, PROGRESS_CHECKLIST ve REMAINING_WORK_BOARD'a
işlemeli. Restore/PITR, gerçek S3 staging kanıtı, scraper/alert/trace kurulumu ve
bağımsız pentest kodla tamamlanmış sayılmamalıdır.

- **`main` korumalı:** 1 onaylayan review + `enforce_admins` açık. GitHub kendi
  PR'ını onaylatmaz; merge için ya ikinci bir insan gerekir ya da review şartı
  geçici kaldırılıp **birebir** geri yüklenir (zorunlu CI kapılarına ve
  `enforce_admins`'e dokunmadan).
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

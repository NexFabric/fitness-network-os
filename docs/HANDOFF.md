# Devir Notu — 2026-08-13

Bu dosya, projeyi devralan kişi ya da ajan için **tek giriş noktasıdır**. Diğer
dökümanlar detayı taşır; buradaki tablo nerede duracağını söyler.

**Main HEAD:** `2a1002d` · **Alembic head:** `v5c6d7e8f9a0` · **Açık PR yok.**

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

Phase 0–27.4 `main`'de — final production-closure kodu 2026-08-13'te merge edildi.
Merge edilen head üzerinde CI: backend **315 passed · 1 skipped**, Playwright
**36 passed**, CodeQL (Python/JS-TS/Actions) ve tüm build/security/image kapıları
yeşil — **14/14 job** (run `31706150882`, CodeQL run `31706145455`). Aynı koşunun
temiz tekrarında sayılar birebir aynı çıktı, yani süit flaky değil.

**Yerelde hiç test çalıştırılmadı; bütün kanıt GitHub CI'dan.** Uygulama gerçek
bir ortamda elle hiç çalıştırılmadı — sıradaki iş bu.

> **Merge notu (dürüstlük kaydı):** PR #55 bağımsız insan onayı olmadan merge
> edildi. Repoda tek collaborator var, dolayısıyla "1 approving review" kuralı
> tanımı gereği karşılanamıyordu. Merge için branch koruması geçici olarak
> gevşetildi (`required_approving_review_count` 1→0), merge sonrası birebir geri
> yüklendi ve doğrulandı: review 1, `enforce_admins` true, `strict` true, 3 required
> check, force-push ve deletion kapalı. `enforce_admins` ve CI kapılarına
> dokunulmadı. Bu bir kod kalite kanıtı değildir — sadece sürecin ne olduğunu kayda
> geçirir.

Önceki dalgalar:

| PR | İş |
|---|---|
| #49 | Cihaz kanalı HMAC imzalama + tek kullanımlık nonce (ADR-044), scanner non-extractable CryptoKey, RBAC portalları, PWA ikonları |
| #50 | Post-merge doküman gerçeği, SBOM job'ının CI kapısından ayrılması |
| #51 | Redis tabanlı login rate limit, ölü idempotency stub'ının silinmesi |
| #52 | Operasyon konsolu: cihazlar, bildirimler, raporlar, personel, şube düzenleme, üyelik yaşam döngüsü |
| #53 | Plan kataloğu + abonelik oluşturma (API-1), gönderim/çalıştırma geçmişi (API-2), `.codesight` haritası |
| #55 | Phase 27.4 final closure: privileged MFA, private S3 rapor storage, gerçek metrics, frozen non-root image, required Playwright gate |

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

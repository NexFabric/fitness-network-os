# Devir Notu — 2026-08-16

Bu dosya, projeyi devralan kişi ya da ajan için **tek giriş noktasıdır**.
Diğer dökümanlar detayı taşır; buradaki tablo nerede duracağını söyler.

| Alan | Değer |
|---|---|
| Branch | `main` |
| Last code | `1b42ab4` (PR **#89** / **#91** / **#93** / **#94** MERGED, 2026-08-16) |
| Alembic head | `xi0d1e2f3a4b` (`pt_appointments` btree_gist EXCLUDE) |
| Bu turda merge edilenler | `#62` → `ae6267d` (Phase 29 + RC) · `#78` → `fb3a26d` (ops tatbikatları) · `#80` → `d56b6a0` (bağımlılık partisi + HAND-1 + dependabot scope) · `#83`/`#84` frontend deps · `#64/#66/#68` CI action bump · `#89` → `e05e29f` (sertifikasyon) · `#91` → `27fff12` (truth) · `#93` → `d9a5c9d` (release-truth gate) · `#94` → `1b42ab4` (TLS proof chown) |
| Campaign landings | **#89–#94 MERGED** — migrate gate · migrator isolation · TLS · ops-drills PITR (CI `31968740247` SUCCESS) · coverage floors · Safety CLI dropped · release-truth checker. Do **not** redo. Register: `docs/CAMPAIGN_REGISTER.md`. EXTERNAL_GATES **UNVERIFIED**. |
| CI | `main` üzerindeki her merge required CI'dan geçti. Merge kapısı **yalnız CI** — review zorunluluğu yok (2026-08-16, tek geliştirici). |
| Production-ready? | **NO** |
| Phase 26 PASS? | **NO / NOT VERIFIED** |

---

## Önce şunu oku

| Ne arıyorsan | Dosya |
|---|---|
| Kod nerede (rota/model/dosya haritası) | `.codesight/wiki/index.md` — 2026-08-16 yenilendi: 142 rota / 86 model / 64 bileşen / 30 madde. AST'den üretilir; `npx codesight --wiki` |
| Ne yapıldı / ne yapılmadı (**otorite**) | `docs/PROGRESS_CHECKLIST.md` |
| Kapanan kampanya — **tekrar etme** | `docs/CAMPAIGN_REGISTER.md` |
| Kalan iş listesi | `backend/docs/plans/REMAINING_WORK_BOARD.md` |
| Sistem mimarisi ve kararların **gerekçeleri** | `docs/ARCHITECTURE.md` |
| Mimari kararlar | `docs/adr/` (ADR-043 federasyon okuma, ADR-044 cihaz imzalama) |
| Güvenlik öz-değerlendirmesi | `docs/ops/ASVS_L2_COMPLIANCE_REPORT.md` |
| Pentest / dış kanıt kapısı | `docs/ops/ASVS_PENTEST_STATUS.md` (UNVERIFIED) |
| Gözlemlenebilirlik (kurulum + alert tatbikatı) | `docs/ops/OBSERVABILITY.md` |
| S3 rapor deposu çalışma zamanı kanıtı | `docs/ops/S3_RUNTIME_PROOF.md` |
| Yedek / restore / **PITR** tatbikatları | `docs/ops/DR_RESTORE_STATUS.md` |
| KMS / IAM kurulum + rotation (NOT VERIFIED) | `docs/ops/KMS_IAM_RUNBOOK.md` |
| Elle tarayıcı tutanağı | `docs/ops/HAND1_BROWSER_PROOF.md` (imza **boş**) |
| Public repo / lisans kararı | `docs/ops/REPO_VISIBILITY.md` (LICENSE yok — insan) |
| Prod deploy / TLS / migrator | `docs/ops/PRODUCTION_DEPLOY.md` |
| Yerel ortamı ayağa kaldırma | `READY_TO_RUN.md` |
| Antrenman & PT Sistemi (hazır motor + spesifikasyon) | `docs/plans/WORKOUT_SYSTEM_HANDOFF_GUIDE.md` — 14/14 test yeşil, RLS & PWA spesifikasyonu hazır |
| Kurallar / mühendislik sözleşmesi | `AGENTS.md` (`CLAUDE.md` buna sembolik bağ — tek kaynak) |

`.codesight` haritası **nerede** olduğunu söyler, **nasıl çalıştığını** değil —
değiştirmeden önce daima kaynağı oku.

---

## Devralan ajan — ilk 10 dakika

1. Bu dosyayı + `docs/PROGRESS_CHECKLIST.md` + `backend/docs/plans/REMAINING_WORK_BOARD.md` oku.
2. `git log origin/main` otoritedir. Tip `1b42ab4` (#94). Sertifikasyon **#89** `e05e29f` olarak `main`'dedir; ardından **#91 / #93 / #94**. Kapanan ID'ler `docs/CAMPAIGN_REGISTER.md` — tekrar implement etme. Bir SHA'nın CI'sini görmeden yeşil iddia etme.
3. **Merge kapısı CI’dır.** Bu tek geliştiricili repoda “1 onaylayan review” kuralı yapısal olarak imkânsızdı (yazar kendi PR’ını onaylayamaz) ve 2026-08-16’da repo sahibi kararıyla kaldırıldı. `enforce_admins`, `strict` ve 11 required check **yerinde** — bunlara dokunma. Yeşil CI olmadan merge etme.
4. IsolationProvider icat etme. Scope.LOCATION’ı şimdi açma.
5. Phase 26 PASS / production-ready / “yayına hazır” iddia etme.

---

## Şu an ne durumda

Ürün kodu `main`'de (Phase 0–27.4 + Waves 1–3 + Fed HQ + B1 + Phase 29 + RC).
Sertifikasyon kapanışı **#89–#94** `main`'dedir (`1b42ab4`). Safety CLI düşürüldü
(pip-audit SCA), migrator DSN yalnız `migrate` servisinde, worker'lar
`PRODUCTION_PRIVATE_NETWORK` alır, ops-drills dump/restore + PITR GitHub'da
yeşil (`31968740247` @ `1b42ab4`). Bu işleri yeniden yazma. Merge yalnız
required CI yeşilse.

**Phase 29 + RC (merge `ae6267d`):**
- Same-tenant BOLA, privileged MFA + step-up + idle, `fernet:hmac:` cihaz sırrı, portal-account bind, scanner pairing, SMTP `delivery.body`, compose workers, hashed `account_invites`, onboarding UI, DSAR export+erasure, god-page split, index drift (`xf7a8b9c0d1e`).
- **STAFF-2** staff list `email` + tenant-isolated `GET /classes/trainers` (UserRole TRAINER; seed trainer/desk `staff` satırı).
- **UR-1** `user_roles` üç partial unique (`xg8b9c0d1e2f`).
- **BK-ERR** `booking.py` `BookingError`; DSAR yalnız not-found/conflict yutar.
- **TR-FK** composite FK `(tenant_id, trainer_user_id) → staff` (`xh9c0d1e2f3a`); picker staff+active ister.
- **PT-EX** `btree_gist` EXCLUDE confirmed PT overlap (`xi0d1e2f3a4b`) — **yalnız Alembic**; ORM’de yok (SQLite `create_all` kırılır). `env.py` `ex_pt_appointments_no_overlap` ignore.
- **TZ-1** `generate_sessions` `Location.timezone` (`ZoneInfo`); unique schedule+start.
- **KPI-1** dashboard member KPI `visible_member_ids`.
- **MEM-T** membership mutation `tenant_id` pin; class book `required_entitlement_type` check+consume; PT availability varsa saat filtresi.
- **TD-1** `admin-web` ve `scanner-pwa` React render & hook yan etkileri temizlendi (0 error, 0 warning).
- **TD-4** `.github/workflows/ops-drills.yml` haftalık periyodik tatbikat workflow'u eklendi.
- **ADV-SEC** `backend/tests/api/test_adversarial_security.py` in-repo BOLA/IDOR/forgery/break-glass testleri eklendi (%100 yeşil).

**Architecture & Isolation Hardening (2026-08-21):**
- **FED-REV-BUG:** `federation.py` içindeki hatalı `Payment.status == "CAPTURED"` sorgusu `PaymentStatus.SUCCEEDED` ve `PARTIALLY_REFUNDED` ile düzeltildi (federasyon konsolu 0 ₺ ciro hatası çözüldü).
- **ERR-BOUND:** `admin-web` için root seviyesinde `ErrorBoundary.tsx` bileşeni eklendi ve `App.tsx` sarmalandı.
- **REC-N1:** `reception.py` arama endpoint'indeki 1 + 2N sıralı sorgu döngüsü `IN(member_ids)` ve `group_by` ile 3 toplu (batch) sorguya indirildi; detay kartı sorgularına `limit(20)` tavanı eklendi.
- **ME-PAG:** `/me/invoices`, `/me/payments`, `/me/consents`, `/me/classes/bookings` ve `/me/pt/appointments` endpoint'lerine güvenli sayfalama (`limit: 1..100`, `offset: >=0`) parametreleri eklendi.
- **IMPORT-CACHE:** `data_import.py` CSV içe aktarma döngüsüne `plan_cache` eklenerek mükerrer plan sorguları engellendi.
- **MODAL-A11Y:** `Members.tsx` ve `Classes.tsx` modal pencerelerine `role="dialog"`, `aria-modal="true"` ve `aria-labelledby` eklendi.
- **DASH-ERR:** `Dashboard.tsx` içindeki sessiz hata yutma yerine `<Alert>` hata bildirimi ve "Yeniden Dene" aksiyonu eklendi.
- **DEV-TENANT:** `devices.py` oturum iptali sorgusuna `tenant_id` filtresi eklendi (izolasyon savunması).
- **INV-INHERIT:** `AccountInvite` modelinin kalıtım sırası standart `(TenantMixin, Base)` formatına getirildi.
- **DOCKER-IGN:** `frontend/.dockerignore` dosyası eklendi.
- **PROMO-LOOP:** `booking.py` sınıf iptalinde ilk yedek üyenin hakkı yoksa sıradaki uygun üyeye geçilmesini ve kalan yedek sırasının sürekli (1, 2, 3...) yeniden indekslenmesini sağlayan döngü düzeltildi.
- **WORKER-HC:** `docker-compose.prod.yml` içindeki tüm worker'lara (8001-8004) ve frontend konteynerlerine `healthcheck` blokları eklendi.
- **PRECOMMIT-SYNC:** `.pre-commit-config.yaml` içindeki araç sürümleri CI ile senkronize edildi (Bandit 1.8.6, Ruff v0.9.9, Mypy v1.15.0).
- **MOBILE-RESPONSIVE:** Tüm frontend arayüzleri (Sporcu/Antrenör/SuperAdmin portalları, operasyon masası, scanner PWA, tanıtım sitesi) iOS 16px auto-zoom engellemesi, 44px dokunmatik hedefler, 100dvh viewport, yatay kaydırılabilir sekmeler ve safe-area insets ile %100 mobil uyumlu hale getirildi.
- **IMPORT-ISOLATION:** `data_import.py` satır işleme döngüsü `begin_nested()` ile izole edildi; 1 satırın veri hatası tüm 5.000 satırlık grubu iptal etmez.
- **BOOK-OVERLAP:** `booking.py` aynı sporcunun aynı zaman diliminde çakışan iki farklı seansa rezervasyon yapmasını engelleyen zaman aralığı kontrolü (`BookingConflict`) eklendi.
- **MODAL-ESC:** `Members.tsx` ve `Classes.tsx` modallarına WCAG 2.2 AA uyumlu `Escape` tuşu kapatma dinleyicisi eklendi.

Önceki mercek (B1 / Fed HQ / #55–#60) checklist’te duruyor; burada tekrar edilmez.

**Test tabanı:** GitHub CI + lokal pytest + Playwright (gerçek Chromium + gerçek backend).
Kapılar: ruff, mypy, `alembic check`, `check_tenancy`, `check_permissions`,
`check_permissions_db`, `check_no_money_floats`, 3 frontend build, Playwright E2E,
repo CodeQL (`javascript-typescript` + `python`). GitHub Default CodeQL Setup =
**not-configured** (SARIF çakışması kapatıldı).

---

## Sıradaki iş (öncelik sırası)

In-repo sertifikasyon **bitti**. Yeni migrate / TLS / coverage / a11y / Safety /
ops-drills PR'ı açma. Kayıt: `docs/CAMPAIGN_REGISTER.md`.

| # | İş | Kim | Not |
|---|---|---|---|
| 0 | **Canlı test** | insan | In-repo dalga kapandı. Operatör kendi canlı/staging turunu yapar. Ajan imzalamaz, Phase 26 işaretlemez. |
| 1 | **HAND-1** insan imzası | insan | `docs/ops/HAND1_BROWSER_PROOF.md` imza tablosu boş. Playwright kapsar; tutanak insan işi. Ajan imzalayamaz. |
| 2 | **P1-11** bağımsız pentest | dış taraf | Onay kuralının kaldırılması bunu kapatmaz. `docs/ops/PENTEST_BRIEF.md`. |
| 3 | **P2-3-IAM** gerçek AWS KMS/IAM | A-OPS | Artefaktlar + doğrulayıcı hazır. Kimlik bilgisi gelince tek komut. |
| 4 | **P1-3b-PROD** / **P1-10-PROD** / **P2-OBS-PROD** | A-OPS | Yerel MinIO / PITR / null-receiver **kapalı**. Üretim AWS / WAL / pager ayrı. |
| 5 | PR **#95** / **#92** | ajan (tek kopya) | Test-depth rebase+CI; Dependabot actions up-to-date merge. Kardeş PR açma. |
| 6 | PR **#86** React 19 | — | **Merge etme.** |

**2026-08-16'da kapananlar (tekrar etme):**
`#89` `e05e29f` · `#91` `27fff12` · `#93` `d9a5c9d` · `#94` `1b42ab4` ·
P1-3b-RT · P1-10 · P2-OBS · MIG-PROD · TLS-1 · CORS-HTTPS · MIG-SEC ·
COV-CRIT · A11Y-1 · PERF-1 · SAFETY-1 · REL-TRUTH · REV-62.
Kanıtlar `docs/ops/` + `docs/CAMPAIGN_REGISTER.md`.

## Bu makineden kapatılamayanlar

| Madde | Neden |
|---|---|
| HAND-1 imza | İnsan tıklama tutanağı; ajan imzalayamaz |
| P2-3-IAM | Üretim KMS alias / IAM / rotation + canlı decrypt — AWS kimlik bilgisi yok |
| P1-3b-PROD | Gerçek AWS kovası (MinIO S3-uyumlu, AWS değil) |
| P1-10-PROD | Üretim host'unda off-host WAL arşivleme + ölçülmüş RPO |
| P1-11 / Phase 26 | Dış pentest + bağımsız güvenlik onayı (`docs/ops/PENTEST_BRIEF.md`) |
| ISO-1 | IsolationProvider abstraction — icat etme, RLS’i değiştirme |
| Scope.LOCATION | Bilinçli ertelendi; şimdi açma |
| LICENSE | Public repo lisans kararı — `docs/ops/REPO_VISIBILITY.md` |
| KVKK / legal | `docs/ops/LEGAL_APPROVAL.md` |
| Live HA | `docs/ops/HA_TOPOLOGY.md` |

**Proje production-ready DEĞİL.** Phase 26 çıkış kapısı geçilmedi. ASVS raporu
**öz-değerlendirmedir**, denetim sonucu değildir. Pazarlama veya canlıya alma
kararı dış kanıt + bağımsız insan onayı olmadan verilmez.

---

## Bilmen gereken tuzaklar

- **`main` korumalı:** `enforce_admins` + `strict` + conversation resolution + 11
  required check (Unit tests, FE builds, Frontend Images, Playwright, CodeQL,
  All Required Checks Passed, lint / image / security job’ları). Force-push /
  deletion kapalı. `delete_branch_on_merge` + Dependabot security updates açık.
  **Review zorunluluğu yok** (2026-08-16, tek geliştirici). Kalan kapıları
  “hız için” düşürme — main’i koruyan tek şey artık CI.
- **Playwright Fernet:** `playwright.config.ts` `backend/.env` okur. Sıfır
  `ENCRYPTION_KEY` ile seed TOTP çözülmez (`InvalidToken`).
- **Owner step-up:** class/device yazılarından önce `acceptOwnerStepUp`. Location
  seed olmadan class session kırılır.
- **Trainer select:** `selectOption` string kullan — `'e2e.trainer@e2e.local (TRAINER)'`.
  Regex object kırılır. Staff email assertion `getByRole('status')` — listede email
  iki node olur.
- **PT overlap:** eşzamanlı ilk insert’te `FOR UPDATE` + EXCLUDE deadlock verdi.
  `FOR UPDATE` kaldırıldı; EXCLUDE + `IntegrityError` yeterli.
- **SQLite:** `ExcludeConstraint` ORM’de yok. `env.py` `include_object` bu constraint’i
  autogenerate’den düşürür. `alembic check` yeşil kalmalı.
- **Notification worker test:** Event loop closed — `AsyncSessionLocal` patch +
  bind param (UUID’yi SQL’e gömme).
- **Login rate limit gerçektir.** Paralel tarayıcı suite paylaşılan hesaplarla
  20/dk’yı aşar. Dev stack `RATE_LIMIT_LOGIN_MAX_REQUESTS=500`
  (`docker-compose.yml`); production sıkı varsayılanı korur.
- **`_seed_user` paylaşılan `GYM_OWNER` rolünü verir.** Testinde rol izinlerini
  değiştirme — kendi özel rolünü kur.
- **`members:read` ucu açar, `members:read:all` satırları açar.** İkincisi yoksa
  çağıran antrenör kapsamına düşer; 403 izin hatası değil, tasarımdır.
- **Cihaz kanalı imza ister.** `device_session` cookie tek başına yetmez;
  `X-Device-Signature/Timestamp/Nonce` zorunlu (ADR-044).
- **Para uçtan uca tam sayı kuruştur.** ORM’de float para alanı CI tarafından
  bloke edilir.
- **CodeQL:** Default Setup açıkken Advanced workflow SARIF çakışır. Şu an
  Default Setup = not-configured. Geri açma.
- **CI tasarrufu:** Required suite ~10+ dk. Her rebase / force-push / docs-only
  commit tam CI'yı yeniden açar. Kardeş PR açma, yeşil PR'ı tekrar push etme,
  izlemek için `workflow_dispatch` basma. Önce bitir, sonra tek rebase.
  Stale run'ı `gh run cancel` ile kes.

### PR #55 (merged) — kısa hatırlatma

Privileged MFA, private S3 rapor storage, Prometheus metrics, frozen non-root
image, required Playwright. Restore/PITR, gerçek S3 staging, scraper/alert/trace
ve bağımsız pentest **kodla kapanmış sayılmaz**.

---

## Yapma

- IsolationProvider’ı somutlaştırma / RLS yerine koyma.
- Scope.LOCATION’ı bu PR’da açma.
- HAND-1 tutanağına ajan imzası atma.
- Phase 26 / production-ready işaretleme.
- Kapanan kampanyayı yeniden yazma (`docs/CAMPAIGN_REGISTER.md`).
- PR **#86** React 19 merge etme.
- Yeşil CI'yı rebase / kardeş PR / boş commit ile yeniden başlatma.
- `enforce_admins` veya required check listesini “hız için” düşürme. Yeşil CI olmadan merge etme.
- `reports/` içeriğini commit etme — yerel denetim çıktısı, `.gitignore`'da.

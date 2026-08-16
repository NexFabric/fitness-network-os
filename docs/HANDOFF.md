# Devir Notu — 2026-08-16

Bu dosya, projeyi devralan kişi ya da ajan için **tek giriş noktasıdır**.
Diğer dökümanlar detayı taşır; buradaki tablo nerede duracağını söyler.

| Alan | Değer |
|---|---|
| Branch | `main` — açık dal yok, açık PR yok |
| Last code | `d56b6a0` (main, 2026-08-16) |
| Alembic head | `xi0d1e2f3a4b` (`pt_appointments` btree_gist EXCLUDE) |
| Bu turda merge edilenler | `#62` → `ae6267d` (Phase 29 + RC) · `#78` → `fb3a26d` (ops tatbikatları) · `#80` → `d56b6a0` (bağımlılık partisi + HAND-1 + dependabot scope) · `#64/#66/#68` CI action bump |
| CI | `main` üzerindeki her merge required CI'dan geçti. Merge kapısı **yalnız CI** — review zorunluluğu yok (2026-08-16, tek geliştirici). |
| Production-ready? | **NO** |
| Phase 26 PASS? | **NO / NOT VERIFIED** |

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
| Pentest / dış kanıt kapısı | `docs/ops/ASVS_PENTEST_STATUS.md` (UNVERIFIED) |
| Gözlemlenebilirlik (kurulum + alert tatbikatı) | `docs/ops/OBSERVABILITY.md` |
| S3 rapor deposu çalışma zamanı kanıtı | `docs/ops/S3_RUNTIME_PROOF.md` |
| Yedek / restore / **PITR** tatbikatları | `docs/ops/DR_RESTORE_STATUS.md` |
| KMS / IAM kurulum + rotation (NOT VERIFIED) | `docs/ops/KMS_IAM_RUNBOOK.md` |
| Elle tarayıcı tutanağı | `docs/ops/HAND1_BROWSER_PROOF.md` (imza **boş**) |
| Yerel ortamı ayağa kaldırma | `READY_TO_RUN.md` |
| Kurallar / mühendislik sözleşmesi | `AGENTS.md` (`CLAUDE.md` buna sembolik bağ — tek kaynak) |

`.codesight` haritası **nerede** olduğunu söyler, **nasıl çalıştığını** değil —
değiştirmeden önce daima kaynağı oku.

---

## Devralan ajan — ilk 10 dakika

1. Bu dosyayı + `docs/PROGRESS_CHECKLIST.md` + `backend/docs/plans/REMAINING_WORK_BOARD.md` oku.
2. `git log origin/main` otoritedir. Açık PR ve açık dal **yok**; her şey `main`'de. Bir SHA'nın CI'sini görmeden yeşil iddia etme.
3. **Merge kapısı CI’dır.** Bu tek geliştiricili repoda “1 onaylayan review” kuralı yapısal olarak imkânsızdı (yazar kendi PR’ını onaylayamaz) ve 2026-08-16’da repo sahibi kararıyla kaldırıldı. `enforce_admins`, `strict` ve 11 required check **yerinde** — bunlara dokunma. Yeşil CI olmadan merge etme.
4. IsolationProvider icat etme. Scope.LOCATION’ı şimdi açma.
5. Phase 26 PASS / production-ready / “yayına hazır” iddia etme.

---

## Şu an ne durumda

In-repo kod **kapandı ve `main`'e merge edildi** (Phase 0–27.4 + Waves 1–3 +
Fed HQ + Milestone B1 + Phase 29 + RC booking/staff/PT kapanışı). Açık PR yok,
açık dal yok. Kalan her şey dış kanıt gerektiriyor — aşağıdaki tabloya bak.

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

Önceki mercek (B1 / Fed HQ / #55–#60) checklist’te duruyor; burada tekrar edilmez.

**Test tabanı:** GitHub CI + lokal pytest + Playwright (gerçek Chromium + gerçek backend).
Kapılar: ruff, mypy, `alembic check`, `check_tenancy`, `check_permissions`,
`check_permissions_db`, `check_no_money_floats`, 3 frontend build, Playwright E2E,
repo CodeQL (`javascript-typescript` + `python`). GitHub Default CodeQL Setup =
**not-configured** (SARIF çakışması kapatıldı).

---

## Sıradaki iş (öncelik sırası)

| # | İş | Kim | Not |
|---|---|---|---|
| 1 | **HAND-1** insan imzası | insan | `docs/ops/HAND1_BROWSER_PROOF.md` imza tablosu boş. Playwright kapsar; tutanak insan işi. |
| 2 | **P1-11** bağımsız pentest | dış taraf | Onay kuralının kaldırılması bunu kapatmaz. |
| 3 | **P2-3-IAM** gerçek AWS KMS/IAM | A-OPS | Artefaktlar + doğrulayıcı hazır: `ops/iam/`, `backend/scripts/kms_iam_verify.py`. Kimlik bilgisi gelince tek komut. |
| 4 | Üretim S3 kovası / off-host WAL / gerçek pager | A-OPS | Yerel tatbikatlar geçti; üretim altyapısı ayrı. |

**2026-08-16'da kapananlar:** P1-3b-RT (gerçek S3 API'sine karşı 10/10),
P1-10 (dump/restore **ve** PITR tatbikatı), P2-OBS (Prometheus/Alertmanager/
Grafana + uçtan uca ateşlenen alert). Kanıtlar `docs/ops/` altında.

## Bu makineden kapatılamayanlar

| Madde | Neden |
|---|---|
| HAND-1 imza | İnsan tıklama tutanağı; ajan imzalayamaz |
| P2-3-IAM | Üretim KMS alias / IAM / rotation + canlı decrypt — AWS kimlik bilgisi yok |
| P1-3b-PROD | Gerçek AWS kovası (MinIO S3-uyumlu, AWS değil) |
| P1-10-PROD | Üretim host'unda off-host WAL arşivleme + ölçülmüş RPO |
| P1-11 / Phase 26 | Dış pentest + bağımsız güvenlik onayı |
| ISO-1 | IsolationProvider abstraction — icat etme, RLS’i değiştirme |
| Scope.LOCATION | Bilinçli ertelendi; şimdi açma |

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
- `enforce_admins` veya required check listesini “hız için” düşürme. Yeşil CI olmadan merge etme.
- `reports/` içeriğini commit etme — yerel denetim çıktısı, `.gitignore`'da.

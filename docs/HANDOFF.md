# Devir Notu — 2026-08-16

Bu dosya, projeyi devralan kişi ya da ajan için **tek giriş noktasıdır**.
Diğer dökümanlar detayı taşır; buradaki tablo nerede duracağını söyler.

| Alan | Değer |
|---|---|
| Branch | `feat/public-site-modernization-and-seo` |
| Last code | `ab860f0` (`ab860f095da250d9a5757f1ac83d80f6734cbb10`) |
| Alembic head | `xi0d1e2f3a4b` (`pt_appointments` btree_gist EXCLUDE) |
| PR | [#62](https://github.com/NexFabric/fitness-network-os/pull/62) OPEN · MERGEABLE · **BLOCKED `REVIEW_REQUIRED`** |
| CI | `ab860f0` `31947417828` **SUCCESS**. Docs `e6a2d6c` `31947732456` **SUCCESS**. |
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
| Elle tarayıcı tutanağı | `docs/ops/HAND1_BROWSER_PROOF.md` (imza **boş**) |
| Yerel ortamı ayağa kaldırma | `READY_TO_RUN.md` |
| Kurallar / mühendislik sözleşmesi | `AGENTS.md` |

`.codesight` haritası **nerede** olduğunu söyler, **nasıl çalıştığını** değil —
değiştirmeden önce daima kaynağı oku.

---

## Devralan ajan — ilk 10 dakika

1. Bu dosyayı + `docs/PROGRESS_CHECKLIST.md` + `backend/docs/plans/REMAINING_WORK_BOARD.md` oku.
2. `gh pr view 62` ile PR’ı tazeleyin. Kod `ab860f0` ve docs `e6a2d6c` required CI **SUCCESS**. Bu oturum durdu; yeni docs SHA’nın CI’sini iddia etme.
3. **PR #62’yi merge etme.** GitHub yazarın (`emrahub`) kendi PR’ını onaylatmaz. Kullanıcı sözlü “onaylıyorum” ≠ GitHub `APPROVE`. İkinci bir insan hesabı gerekir. `enforce_admins` ve required check listesine dokunma.
4. IsolationProvider icat etme. Scope.LOCATION’ı şimdi açma.
5. Phase 26 PASS / production-ready / “yayına hazır” iddia etme.

---

## Şu an ne durumda

In-repo kod bu dalda **kapandı** (Phase 0–27.4 + Waves 1–3 + Fed HQ + Milestone B1 + Phase 29 + RC booking/staff/PT kapanışı). `main`’e **merge edilmedi**.

**Bu dalda kapanan son kod (Phase 29 + RC):**
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
| 1 | PR #62 bağımsız `APPROVE` | **ikinci insan GitHub hesabı** | Self-approve yasak. Merge yok. |
| 2 | **HAND-1** insan imzası | insan | `docs/ops/HAND1_BROWSER_PROOF.md` imza tablosu boş. Playwright kapsar; tutanak insan işi. |
| 3 | S3 / PITR / pentest / OBS / KMS IAM | A-OPS | Dış kanıt. Kod fail-closed. Uydurma. |

## Bu makineden kapatılamayanlar

| Madde | Neden |
|---|---|
| PR #62 merge | 1 required review + `enforce_admins`; yazar kendi PR’ını onaylayamaz |
| HAND-1 imza | İnsan tıklama tutanağı; ajan imzalayamaz |
| P1-3b-RT | Gerçek S3/MinIO kovası + kimlik bilgisi |
| P2-3-IAM | Üretim KMS alias / IAM / rotation + canlı decrypt |
| P1-10 | Gerçek altyapıda restore/PITR tatbikatı |
| P1-11 / Phase 26 | Dış pentest + bağımsız APPROVE |
| ISO-1 | IsolationProvider abstraction — icat etme, RLS’i değiştirme |
| Scope.LOCATION | Bilinçli ertelendi; şimdi açma |

**Proje production-ready DEĞİL.** Phase 26 çıkış kapısı geçilmedi. ASVS raporu
**öz-değerlendirmedir**, denetim sonucu değildir. Pazarlama veya canlıya alma
kararı dış kanıt + bağımsız insan onayı olmadan verilmez.

---

## Bilmen gereken tuzaklar

- **`main` korumalı:** 1 onaylayan review + `enforce_admins` + dismiss stale +
  conversation resolution + `strict`. Required checks: Unit tests, FE builds,
  Frontend Images, Playwright, CodeQL, All Required Checks Passed (ve lint /
  image / security job’ları). Force-push / deletion kapalı. `delete_branch_on_merge`
  + Dependabot security updates açık. Review sayısını 0 yapmak solo-repo dansıdır;
  **bu turda yapma** — kullanıcı merge istemedi, ikinci insan bekleniyor.
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
- `enforce_admins` veya required check listesini “hız için” düşürme.
- `reports/` untracked dizinini commit etme (yerel artık).

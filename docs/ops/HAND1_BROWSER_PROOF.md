# HAND-1 — Elle tarayıcı kanıtı

Bu tutanak **P1-11 pentest değildir.** Yerel/staging’de birinci kulüp akışının
bir insan tarafından tıklandığını kaydeder.

**Alembic:** `xe6f7a8b9c0d` · **Dal:** `feat/public-site-modernization-and-seo`

Otomatik karşılık (CI / yerel Playwright): `invite_accept.spec.ts`,
`onboarding.spec.ts`, `portal_account.spec.ts`, `scanner_pair.spec.ts`,
`ops_surfaces.spec.ts` (rapor çıktı linki), `reception_and_product_flows.spec.ts`
(portal İletişim: Paketi indir + Verilerimi sil, silme confirm iptali).
`playwright.config.ts` `backend/.env` okur — sıfır Fernet ile seed TOTP çözülmez.
2026-08-16 yerel: 15/15 geçti (ENCRYPTION_KEY eşleşmeli). İnsan imzası hâlâ boş.

## Önkoşul

`READY_TO_RUN.md`: `docker compose up` (includes `migrate` one-shot) →
`seed_role_matrix.py` (TOTP’li owner). Vite `:5173` + scanner `:5174` still on host.

## Akış (her satırı PASS/FAIL işaretle)

| # | Adım | Sonuç |
|---|---|---|
| 1 | `e2e.owner@e2e.local` + TOTP → ops panel | |
| 2 | `/locations` — şube oluştur | |
| 3 | `/plans` — fiyat kuruş, yayınla (geri alınamaz) | |
| 4 | `/members` — üye + e-posta → portal hesabı → `/invite` parola | |
| 5 | `/staff` — hesap oluştur → davet linki (OTP yok) | |
| 6 | `/devices` — provision, API key bir kez | |
| 7 | Scanner `:5174` — cihaz ID + API key + tenant eşle | |
| 8 | `/member` QR çıkar → scanner GRANT; aynı jti 409 | |
| 9 | `/reports` çalıştır → çıktı 200 (local provider) | |
| 10 | `/onboarding` — aşamalar, eksik şubede advance reddi | |

## İmza

| Alan | Değer |
|---|---|
| Tarih | |
| Kim | |
| Ortam | local / staging |
| Genel | PASS / FAIL |
| Not | |

Phase 26 / production-ready bu dosyayla işaretlenmez.

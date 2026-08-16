# HAND-1 — Elle tarayıcı kanıtı

Bu tutanak **P1-11 pentest değildir.** Birinci kulüp akışının gerçek bir
tarayıcıda baştan sona çalıştığını kaydeder.

**Alembic:** `xi0d1e2f3a4b` · **Dal:** `main` (`ae6267d`)

## İki ayrı kayıt — karıştırma

| Kayıt | Ne kanıtlar | Durum |
|---|---|---|
| **Otomatik koşum** (aşağıda) | Akışın gerçek Chromium + gerçek backend'de teknik olarak çalıştığı | ✅ **51/51 PASS**, 2026-08-16 |
| **İnsan imzası** (en altta) | Sorumlu bir insanın ürüne bakıp onayladığı | ⬜ **BOŞ** |

Otomatik koşum insan imzasının yerine geçmez. Otomasyon "buton çalışıyor" der;
insan "bu ürün kullanılabilir" der. İkincisini ajan imzalayamaz.

## Otomatik koşum — 2026-08-16

Koşan: Claude (ajan), `npx playwright test`, gerçek Chromium + gerçek backend +
PostgreSQL + Redis. **51 passed (29.0s)**, 0 failed.

| # | Adım | Kapsayan spec | Sonuç |
|---|---|---|---|
| 1 | `e2e.owner@e2e.local` + TOTP → ops panel | `admin_auth`, `role_isolation` (gym owner → ops console) | ✅ PASS |
| 2 | `/locations` — şube oluştur | `locations_edit` | ✅ PASS |
| 3 | `/plans` — fiyat kuruş, yayınla (geri alınamaz) | `plans_membership` | ✅ PASS |
| 4 | `/members` — üye + e-posta → portal hesabı → `/invite` parola | `portal_account`, `invite_accept` | ✅ PASS |
| 5 | `/staff` — hesap oluştur → davet linki (OTP yok) | `staff_provision`, `invite_accept` | ✅ PASS |
| 6 | `/devices` — provision, API key bir kez | `devices_admin` (anahtar bir kez + reload'da yok) | ✅ PASS |
| 7 | Scanner `:5174` — cihaz ID + API key + tenant eşle | `scanner_pair`, `scanner_access` | ✅ PASS |
| 8 | `/member` QR çıkar → scanner GRANT; aynı jti 409 | `member_qr_roundtrip` (bir kez geçerli, replay reddedilir) | ✅ PASS |
| 9 | `/reports` çalıştır → çıktı 200 | `ops_surfaces` (tanım oluştur + çalıştır) | ✅ PASS |
| 10 | `/onboarding` — aşamalar, eksik şubede advance reddi | `onboarding` | ✅ PASS |

Ek olarak aynı koşumda geçenler: rol izolasyonu (çapraz portal erişimi reddi,
`localStorage`'da sahte tenant id konsolu açmıyor), 4 portalda sıfır konsol
hatası, resepsiyon override, CSV import, federasyon HQ 6 sekme.

### Koşarken bulunan tuzak — bunu bilmeden koşma

`playwright.config.ts` kendi backend'ini `127.0.0.1:8000`'de başlatır ve
`backend/.env` okur. **Dev docker stack aynı portu tutuyorsa** Playwright kendi
sunucusunu başlatamaz ve testler docker backend'ine düşer. Docker compose
`ENCRYPTION_KEY=MDAwMDA...`, `.env` ise başka bir anahtar taşır — seed edilmiş
TOTP sırrı çözülemez ve **her login testi `/login`'de takılır**.

İlk koşumda tam olarak bu oldu: **31 failed / 17 passed**. Belirti "auth bozuk"
gibi görünür, gerçek sebep anahtar uyuşmazlığıdır. Backend logunda login
isteğinin hiç görünmemesi ayırt edici işarettir.

Çözüm: Playwright'tan önce `docker stop fitness-os-backend`. Aynı anahtarla
yeniden seed etmek de çalışır ama port çakışması sürdüğü için önerilmez.

### Yeniden üretme

```bash
docker compose up -d postgres redis          # migrate one-shot dahil
docker stop fitness-os-backend               # portu Playwright'a bırak
cd backend && set -a && source .env && set +a && ./.venv/bin/python scripts/seed_role_matrix.py
cd ../frontend/e2e && npx playwright test
```

## İmza — insan

Bu tabloyu yalnızca 10 adımı **kendi gözüyle** tıklayan kişi doldurur.
Yukarıdaki otomatik koşum bu satırları doldurmaz.

| Alan | Değer |
|---|---|
| Tarih | |
| Kim | |
| Ortam | local / staging |
| Genel | PASS / FAIL |
| Not | |

Phase 26 / production-ready bu dosyayla işaretlenmez.

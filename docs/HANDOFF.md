# Devir Notu — 2026-08-13

Bu dosya, projeyi devralan kişi ya da ajan için **tek giriş noktasıdır**. Diğer
dökümanlar detayı taşır; buradaki tablo nerede duracağını söyler.

**Main HEAD:** `a60d55c` · **Alembic head:** `u4b5c6d7e8f9` · Açık PR yok ·
CI yeşil · Dependabot 0 açık alarm · Çalışma ağacı temiz.

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

Phase 0–27.3 `main`'de. Beş dalga bu oturumda girdi:

| PR | İş |
|---|---|
| #49 | Cihaz kanalı HMAC imzalama + tek kullanımlık nonce (ADR-044), scanner non-extractable CryptoKey, RBAC portalları, PWA ikonları |
| #50 | Post-merge doküman gerçeği, SBOM job'ının CI kapısından ayrılması |
| #51 | Redis tabanlı login rate limit, ölü idempotency stub'ının silinmesi |
| #52 | Operasyon konsolu: cihazlar, bildirimler, raporlar, personel, şube düzenleme, üyelik yaşam döngüsü |
| #53 | Plan kataloğu + abonelik oluşturma (API-1), gönderim/çalıştırma geçmişi (API-2), `.codesight` haritası |

**Test tabanı:** backend 309 passed · 1 skipped, Playwright 37 passed (gerçek
Chromium + gerçek backend). Kapılar: ruff, mypy, `alembic check`,
`check_tenancy`, `check_permissions`, `check_permissions_db`,
`check_no_money_floats`, 3 frontend build, CodeQL.

---

## Sıradaki iş (yapılabilir olanlar)

1. **MFA kayıt UX'i** — backend tam (TOTP + Fernet + kurtarma kodları), eksik
   olan yalnızca arayüz akışı. En düşük riskli, en yüksek değerli sıradaki adım.
2. **Kullanıcı hesabı açma ucu** — Personel ekranı bugün yalnızca *var olan*
   kullanıcıyı bağlayabiliyor; hesap oluşturan bir uç yok.
3. **`/metrics`** şu an Prometheus placeholder'ı; gerçek metrik pipeline'ı bir
   altyapı kararı bekliyor.

## Bu makineden kapatılamayanlar (sebebiyle)

| Madde | Neden |
|---|---|
| P1-3b imzalı object-storage URL'i + şifreleme | Gerçek S3/MinIO kovası ve kimlik bilgisi gerekiyor; raporlar özel diske CSV yazıyor |
| P2-3 QR sırları için KMS | Sağlayıcı SDK'sı + anahtar politikası gerekiyor; `qr_crypto.py` KMS referansını tanır, bilinçli `NotImplementedError` verir |
| P1-10 yedekten dönüş tatbikatı | Gerçek altyapıda koşup kanıtlanması gereken ops prosedürü |
| P1-11 / Phase 26 dış pentest + bağımsız onay | Tanımı gereği dışarıdan gelmeli |

**Proje production-ready DEĞİL.** Phase 26 çıkış kapısı geçilmedi ve ASVS raporu
**öz-değerlendirmedir**, denetim sonucu değildir. Pazarlama veya canlıya alma
kararı bu iki kanıt gelmeden verilmemelidir.

---

## Bilmen gereken tuzaklar

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

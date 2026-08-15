# GymClubNex — Production Readiness P0 Closure & Review Plan

## 🎯 Hedef ve Kapsam
Bu plan, PR #59 üzerindeki release candidate (`feat/production-readiness-p0-and-dr`) için NO-GO kararına yol açan tüm P0 ve P1 mimari, runtime, güvenlik, iş mantığı ve operasyonel açıkları kapatarak sistemi gerçek bir **Production-Ready GO** seviyesine ulaştırmayı hedefler.

---

## 📋 10 Ana Eylem Sütunu

### Sütun 1: CI & Toolchain Gate Temizliği
- [ ] `backend/` dizinindeki 32 adet Ruff linting / formatlama hatasını düzelt.
- [ ] `uv run ruff check .` ve `uv run ruff format --check .` komutlarının sıfır hata ile geçmesini sağla.
- [ ] `uv run mypy app` tip kontrollerini doğrula.

### Sütun 2: Production Worker Stack & Runtime Sertleştirme (P0)
- [ ] `backend/app/core/config.py`: Worker çalışma zamanı için Settings validasyonunu decouple et veya `docker-compose.prod.yml` içindeki eksik zorunlu değişkenleri (`MIGRATOR_DATABASE_URL`, `CORS_ORIGINS`, `ALLOWED_HOSTS`, `METRICS_BEARER_TOKEN`, `S3_BUCKET_NAME`, `QR_KMS_MODE`) tamamla.
- [ ] `backend/app/workers/outbox.py`:
  - `dummy_publisher` yerine güvenli event routing entegrasyonu sağla.
  - `process_pending_inbox` çağrısını servis imzasına (`tenant_id`, `handlers={...}`) uygun hale getir; hatalı `worker_id` argümanını kaldır.
  - Worker döngülerine explicit `await db.commit()` ekle (servisler flush-only olduğu için).
- [ ] `backend/app/workers/report.py`: `execute_run()` sonrası explicit `commit()` ekle.

### Sütun 3: Tenant Lifecycle Hard Fence (P0)
- [ ] `backend/app/api/deps.py` içindeki `get_current_device`:
  - `Tenant.status` kontrolü ekle (`SUSPENDED` veya `CLOSED` ise `403/401` fırlat).
- [ ] Outbox, Notification ve Report worker döngülerinde non-active tenant filtrelemesini güvenceye al.
- [ ] Askıya alınmış / kapatılmış salon cihazlarının isteklerinin engellendiğini doğrulayan testler yaz.

### Sütun 4: Business Gate Truth & Eksiksiz Tamamlama (P0)
- [ ] **Onboarding Orkestrasyonu (`backend/app/api/v1/endpoints/onboarding.py`)**:
  - `/advance` adımına gerçek veritabanı önkoşul doğrulaması ekle (Location, PlanVersion, Staff/UserRole, Payment config).
  - Önkoşullar sağlanmadan `COMPLETED` aşamasına geçişi engelle.
- [ ] **CSV Data Import Pipeline (`backend/app/services/data_import.py`)**:
  - Deterministik çakışma yönetimi ve detaylı satır hatası raporlama.
  - Doğrudan `Membership(status="ACTIVE")` yerine `MembershipService` üzerinden geçerek outbox event'leri, invariant'lar ve wallet haklarını oluştur.
  - `start_date` alanını işle ve hata yutma (`except Exception: pass`) mekanizmasını kaldır.
  - Bounded pagination ekle.
- [ ] **Dunning & Tahsilat Kurtarma Workflow (`backend/app/services/dunning.py`)**:
  - `PaymentAttempt` ve `DunningPolicy` için retry zamanlama, grace period ve bildirim akışını yaz.
  - Access Engine ile entegre et: Grace period bitiminde dunning durumu erişim reddi (`DENY_DUNNING_PAST_DUE`) üretsin.

### Sütun 5: Privileged Access Yönetimi & Break-Glass (P0)
- [ ] **Resepsiyon Manuel Geçiş (`/reception/checkin/{id}/override`)**:
  - `access:override` iznini RBAC matrisine ekle ve endpoint'e bağla.
  - `AuditEvent` kaydını (`action="access.manual_override"`) aktör, sebep, orijinal ret kararı ve override sonucuyla birlikte immutable olarak yaz.
- [ ] **Break-Glass Destek Erişimi**:
  - `/admin/break-glass` router'ını API'ye ekle.
  - `get_tenant_id` içinde süper kullanıcıların yabancı tenant'lara erişimi için aktif `BreakGlassSession` zorunluluğu getir.

### Sütun 6: Forensic Access Karar Snapshot'ları
- [ ] `AccessAttempt.snapshot_data` içeriğine:
  - `membership_id`, `membership_status`,
  - `entitlement_before` / `entitlement_after`,
  - `policy_id`, `policy_version`, `engine_version` ("v1.1"),
  - `correlation_id` / `request_id`,
  - `dunning_state` alanlarını eksiksiz ekle.

### Sütun 7: QR KMS & Production Fail-Closed Kripto (P0)
- [ ] `backend/app/core/qr_crypto.py`: Gerçek KMS sağlayıcı entegrasyonu ve fail-closed mock/kms çözücü ekle.
- [ ] `Settings.validate_production()` içine `QR_KMS_MODE` zorunluluğu koy.
- [ ] Key rotasyonu ve geçersiz anahtar testi ekle.

### Sütun 8: Retention Enforcement & Hukuki Metin Senkronizasyonu
- [ ] `DataRetentionService` scheduler/enforcement mantığını yaz (`anonymize/delete/archive`).
- [ ] `frontend/public-site/src/app/terms/page.tsx` ve `privacy/page.tsx`:
  - %99.9 uptime ve offline turnike geçiş iddialarını gerçek mimariyle (fail-closed) senkronize et.
  - Veri silme ve saklama taahhütlerini gerçek politikalarla eşleştir.

### Sütun 9: DR / PITR Altyapısı ve Kanıt Dokümantasyonu
- [ ] DR kılavuzunu ve scriptlerini sürekli WAL arşivleme ve PITR (Point-in-Time Recovery) tatbikatlarıyla güncelle.
- [ ] RPO (<= 5 dk) ve RTO (< 30 dk) metriklerini doğrula.

### Sütun 10: E2E Playwright Testleri ve Bağımsız Review Agent Denetimi
- [ ] Yeni ekranlar için (Reception override, CSV import preview, Member self-service, Onboarding) Playwright testleri ekle.
- [ ] `define_subagent` / `invoke_subagent` ile bağımsız bir Review & Approval Agent görevlendir ve tüm değişiklikleri denetle.

# GymClubNex (Fitness Network OS) — Sistem Mimarisi

**Son güncelleme:** 2026-08-12
**Kaynak:** Bu doküman `~/.gemini/antigravity-cli/brain/` altında, git dışında tutulan
bir taslaktan repo'ya taşındı ve koda karşı doğrulanarak düzeltildi. Mimari
doküman artık yalnızca burada yaşar.

**İlgili:** `AGENTS.md` (kurallar) · `docs/MASTER_SPEC.md` (gereksinimler) ·
`docs/RBAC.md` (yetki matrisi) · `docs/adr/` (mimari kararlar)

---

## 1. Genel sistem bakışı

```mermaid
graph TD
    subgraph Client_Layer ["İstemci Katmanı"]
        A["Admin Web (Vite :5173)<br/>4 rol portalı + ops konsolu"]
        B["Scanner PWA (Vite :5174)<br/>turnike kiosk"]
        C["public-site<br/>pazarlama sitesi"]
    end

    subgraph Gateway ["Güvenlik & API Katmanı (FastAPI :8000)"]
        D[HttpOnly Cookie Auth + CSRF]
        E[Rate Limiter + Security Headers]
        F["Tenant Context (SET LOCAL) → RLS"]
    end

    subgraph Domain ["Domain Servisleri"]
        G[Auth & MFA TOTP]
        H[Member & Membership]
        I[Access & QR Validation]
        J[Finance - amount_minor]
        K[Outbox / Inbox]
        L["Federation (cross-tenant read)"]
    end

    subgraph Data ["Veri Katmanı"]
        M[("PostgreSQL<br/>shared DB + FORCE RLS")]
        N[(Redis)]
        O[Object storage - raporlar]
    end

    A --> D
    B --> D
    D --> E --> F
    F --> G & H & I & J & K & L
    G & H & I & J & K & L --> M
    E --> N
    K --> O
```

`public-site` bağımsız bir pazarlama uygulamasıdır; API'ye bağlı değildir ve
portal modelinin parçası değildir.

---

## 2. Rol → Portal haritası

Platformda **11 kanonik rol** (`backend/permissions.yml`) ve **5 portal yüzeyi**
vardır. İkisi bire bir değildir — aşağıdaki tablo gerçek eşlemedir.

| Portal | Rota | Erişebilen roller | İşlev |
|---|---|---|---|
| Federasyon Konsolu | `/superadmin` | `PLATFORM_SUPER_ADMIN`, `FEDERATION_ADMIN`, `FEDERATION_ANALYST`, `FEDERATION_SUPPORT` | Organizasyon/kulüp dizini, tenant başına metrikler, sistem audit kayıtları, tenant'a geçiş, pasaport kuralları, uyumluluk sicili ve ağ duyuruları |
| Kulüp Operasyon Konsolu | `/` (+ `/classes`, `/members`, `/locations`, `/finance`) | `GYM_OWNER`, `GYM_ADMIN`, `GYM_MANAGER`, `ACCOUNTANT`, `FRONT_DESK` | Üye kaydı, abonelik, şube, finans, ders programı takvimi ve yoklama çekmecesi |
| Antrenör Portalı | `/trainer` | `TRAINER` (+ `GYM_OWNER`, `GYM_ADMIN`) | Atanmış üyeler, turnike giriş geçmişi, hak kontrolü, grup dersleri ve 1-on-1 PT seansları canlı yoklama defteri |
| Sporcu Portalı | `/member` | `MEMBER` | Üyelik/hak durumu, 60 sn'lik tek kullanımlık giriş QR'ı, grup dersi rezervasyonu (yedek sırası) ve birebir PT randevusu alma |
| Kapı Okuyucu PWA | `:5174` (ayrı uygulama) | *cihaz principal'ı* — kullanıcı rolü değil | QR doğrulama, hak düşümü, röle tetikleme |

**Giriş kapısı:** `/portal` — oturum açmış kullanıcıya yalnızca **kendi
rollerinin açtığı** kartları gösterir. Rol yoksa boş durum gösterir.

**Rota alias'ları:** `/federation` → `/superadmin`, `/athlete` → `/member`,
`/home` → `/portal`.

**Yönlendirme:** Login sonrası `homeRouteFor()`
(`frontend/admin-web/src/auth/roles.ts`) kullanıcıyı en geniş yetkili portalına
gönderir.

### Yetkilendirme nerede uygulanır

Rol ayrımı üç katmanda birden zorunludur; hiçbiri tek başına yeterli sayılmaz:

1. **Frontend** — `RequireAuth` (sunucudan doğrulanmış oturum, `GET /me/session`)
   + `RequireRole`. Bu yalnızca **kullanılabilirlik** katmanıdır, güvenlik sınırı değildir.
2. **API** — her handler `AuthorizationService.require_tenant` / `require_self`
   ile izin kontrolü yapar. Gerçek yetki sınırı burasıdır.
3. **Veritabanı** — RLS politikaları (`FORCE ROW LEVEL SECURITY`) tenant
   sızıntısını yapısal olarak imkânsız kılar.

---

## 3. Tenant izolasyonu

- Her tenant'a ait tablo: `tenant_id` (NOT NULL) + index + `UNIQUE(tenant_id, id)` + RLS politikası. CI kapısı: `scripts/check_tenancy.py`.
- Politika: `tenant_id = nullif(current_setting('app.current_tenant_id', true), '')::uuid`, `FORCE ROW LEVEL SECURITY` ile tablo sahibi de muaf değil.
- Context **transaction-scoped** (`SET LOCAL`), `after_begin` listener'ı ile commit sonrası yeniden kurulur (`app/db/session.py`).
- Context boşsa sorgu **sıfır satır** döner (fail-closed).

**RLS'siz kalan tablolar ve gerekçesi**

| Tablo | Gerekçe |
|---|---|
| `tenants`, `organizations` | Tenant bariyerinin *üstünde* — dizin verisi |
| `users`, `user_sessions` | Kimlik doğrulama artefaktı; tenant'a ait değil |
| `device_sessions` | Tenant'ı *türeten* bootstrap okuması; policy burada her cihaz isteğini kapatırdı. Tek pre-context okuma budur — `devices` ve `device_nonces` context kurulduktan sonra, tam RLS altında okunur |

### Cross-tenant okuma

Federasyon agregaları RLS'i genişletmez. Tenant listesi sayfalanır ve her
tenant için GUC tek tek kurularak salt-okunur sorgu yapılır — her SQL ifadesi
hâlâ tek bir tenant görür. Karar ve reddedilen alternatifler:
**`docs/adr/ADR-043-federation-scope-reads.md`**.

`is_superuser` bir federasyon yetkisi değil, **tenant taklit bayrağıdır**:
sahibi `X-Tenant-ID` ile herhangi bir tenant'ı adresleyebilir. Bu erişim artık
`superuser.tenant_impersonation` audit olayı yazar.

---

## 4. QR erişim akışı

```mermaid
sequenceDiagram
    participant M as Sporcu (/member)
    participant API as FastAPI
    participant K as Kiosk PWA (:5174)

    M->>API: POST /access/qr/issue-self {ttl_seconds}
    Note over API: member_id KABUL EDİLMEZ<br/>session → members.user_id ile çözülür
    API-->>M: {token, jti, exp}
    Note over M: QR tarayıcıda yerel üretilir<br/>(token üçüncü tarafa gitmez)
    M->>K: QR göster
    K->>API: POST /devices/qr/validate {token}<br/>+ X-Device-Signature / Timestamp / Nonce
    Note over API: cihaz istek imzası (HMAC-SHA256) + nonce<br/>sonra QR imza + exp + jti replay kontrolü<br/>cihazın kendi device_id/location_id'si kullanılır
    API-->>K: granted / denied(reason)
    K->>K: röle tetikle
```

- Üye kendi adına QR üretir; başkası adına üretemez (istek şemasında alan yok).
- Personel yolu ayrıdır: `POST /access/qr/issue` + `access:issue` izni.
- Aynı token ikinci kez taranırsa `replay` ile reddedilir.
- Kiosk çevrimdışıyken **deny-by-default** uygular.
- Cihaz kimliği iki parçadır: `device_session` cookie'si **ve** `POST /devices/auth`
  yanıtında bir kez verilen imza sırrı (cookie'de taşınmaz). Her istek
  `METHOD\npath\ntimestamp\nnonce\nsha256(body)` üzerinden HMAC-SHA256 ile
  imzalanır; ±300 sn saat toleransı, nonce tek kullanımlıktır (`device_nonces`).
  Çalınan cookie tek başına yetmez, yakalanan imzalı istek tekrar oynatılamaz.
  Karar ve reddedilen alternatifler: **`docs/adr/ADR-044-device-request-signing.md`**.

---

## 5. Üyelik ve plan alanı

Bir abonelik daima **yayımlanmış bir plan sürümüne** karşı satılır. Katalog ile
abonelik arasındaki sınır kasıtlıdır: fiyat, ürün tanımında değil, satış anında
aboneliğe **kopyalanır**.

```mermaid
graph LR
    P[Plan<br/>ürün tanımı] --> PV1["PlanVersion v1<br/>taslak"]
    P --> PV2["PlanVersion v2<br/>yayımlandı"]
    PV2 -->|"POST /memberships"| M["Membership<br/>price_snapshot + terms_snapshot"]
    M --> MP[MembershipPeriod]
    M --> MH[MembershipStatusHistory]
    M -.->|dondur / çöz / iptal / yenile / süre doldu| M
```

Kurallar ve gerekçeleri:

- **Sürüm numarası sunucuda atanır** (`create_plan_version`). İstemciden gelse
  aynı anda taslak açan iki operatör aynı numarayı isteyebilir ve biri
  diğerinin yerini sessizce alırdı.
- **Yayımlama tek yönlüdür.** Yayımlanmış sürüm düzenlenemez, geri alınamaz —
  satılmış abonelikler o fiyata bağlıdır. Fiyat değişikliği = yeni sürüm.
- **Taslak satılamaz.** `start_membership` yalnızca `is_published` sürümü kabul
  eder, aksi hâlde 400 döner.
- **Fiyat anlık kopyalanır** (`price_snapshot`, `price_snapshot_currency`,
  `terms_snapshot`). Sonraki bir sürüm geçmişi yeniden yazamaz.
- **Bir üyede tek canlı abonelik.** `ACTIVE / FROZEN / PAST_DUE / SCHEDULED /
  PENDING` durumlarından biri varsa ikinci başlatma reddedilir.
- **Para uçtan uca tam sayı kuruştur** (`amount_minor`). UI'daki `499,90`
  girdisi float'tan geçmeden basamak ayrıştırmasıyla `49990`'a çevrilir; ORM'de
  float para alanı CI tarafından bloke edilir (`check_no_money_floats.py`).
- Yetki: katalog ve abonelik başlatma `memberships:read` / `memberships:write`
  izinlerini kullanır. Ayrı bir `plans:*` çifti eklenmedi — aynı şeyi söyleyen
  ikinci bir izin matrisi göç gerektirirdi.

Gelecek durumlar (`SCHEDULED`) `start_date` geleceğe verildiğinde servis
tarafından seçilir; istemci durum gönderemez.

---

## 6. Federasyon ve Çoklu Kulüp Ağı (HQ) Mimarisi

Federasyon, münferit kulüplerin (tenant) üstünde yer alan organizasyon/franchise çatı yapısıdır.

```mermaid
graph TD
    Fed[Federasyon / Organizasyon HQ<br/>organization_id]
    Fed --> G1["Kulüp 1 (Tenant A)<br/>RLS İzolasyonu"]
    Fed --> G2["Kulüp 2 (Tenant B)<br/>RLS İzolasyonu"]
    Fed --> G3["Kulüp 3 (Tenant C)<br/>RLS İzolasyonu"]
    
    G1 --> L1["Şube 1 (Location)"]
    G1 --> D1["Turnike Cihazları (Devices)"]
    
    Fed -.->|ADR-043 GUC Döngüsü| M["Konsolide Analitik & Raporlar"]
    Fed --> P["Federasyon Pasaportu<br/>(Çapraz Kulüp Dolaşım Matrisi)"]
    Fed --> C["Uyumluluk & Denetim Sicili<br/>(TSE, ISO, Hijyen)"]
    Fed --> A["Ağ Duyuruları Yayını"]
```

Kurallar ve Tasarım İlkeleri:
- **Federation != Tenant; Gym = Tenant:** Kulüp düzeyindeki tüm veriler (üyeler, turnike geçişleri, ödemeler, kasalar) PostgreSQL RLS (`tenant_id`) ile kesin olarak yalıtılmıştır.
- **ADR-043 Çapraz Kulüp Okuma Güvencesi:** Federasyon okumaları RLS politikalarını gevşetmez veya RLS-bypass rolleri kullanmaz. `FederationService`, her bir tenant için sırayla `SET LOCAL app.current_tenant_id = :id` GUC'unu kurar, sayfa tavanı (`MAX_TENANT_PAGE = 50`) uygular ve `_leave_tenant()` ile temizler. Sayfa sınırını aşan durumlarda `partial: true` bayrağı döner.
- **Kulüp Yaşam Döngüsü & Askıya Alma:** Federasyon yöneticisi bir kulübü gerekçe belirterek anında `SUSPENDED` durumuna alabilir. Askıya alınan kulübün hem insan girişleri hem de turnike tarayıcı cihaz yetkileri (`deps.py:_verify_tenant_status`) kesilir.
- **Federasyon Pasaportu & Mahsuplaşma:** `passport_configs` tablosu üzerinden hangi kulübün hangi üyelik paket seviyelerini (VIP, Gold vb.) misafir olarak kabul edeceği, aylık geçiş kotası ve ziyaret başı mahsuplaşma ücreti (`guest_fee_minor`) yönetilir.
- **Uyumluluk & Muayene Sicili:** `compliance_records` ile kulüplerin resmi TSE/ISO/Hijyen denetim kayıtları merkezi olarak tutulur.
- **Ağ Duyuruları:** `network_alerts` ile tüm ağa veya belirli bir kulübün paneline doğrudan uyarı/duyuru broadcast edilir.

---

## 7. Grup Dersi & Birebir PT Rezervasyon Motoru (B1)

Grup ders seansları, şablon programlar, kapasite kotaları, dinamik yedek sırası ve 1-on-1 Personal Training (PT) randevu motoru mimarisidir.

```mermaid
graph TD
    CT[ClassType<br/>Ders Kataloğu: Reformer, Yoga, HIIT] --> CSCH["ClassSchedule (Haftalık Şablon)<br/>Pzt 10:00, Çrş 18:00"]
    CSCH --> CS["ClassSession (Somut Takvim Seansı)<br/>16 Ağu 11:00 · Kapasite: 10"]
    
    CS -->|"book_session (SELECT FOR UPDATE)"| CB1["ClassBooking #1<br/>Durum: CONFIRMED"]
    CS -->|"book_session (Kapasite Dolu)"| CB2["ClassBooking #2<br/>Durum: WAITLISTED (Sıra: 1)"]
    
    CB1 -.->|"cancel_booking"| CB1_CANCELLED["İptal Edildi"]
    CB2 ==>|"Atomik Otomatik Terfi (Auto-Promotion)"| CB2_PROMOTED["CONFIRMED (Asil Listeye Alındı)"]
    
    TA[TrainerAvailability<br/>Antrenör Çalışma Saatleri] --> PTA["PtAppointment<br/>1-on-1 Birebir PT Randevusu"]
```

### Temel Prensipler ve Concurrency Güvenceleri:
1. **Pessimistik Kilitleme (`SELECT ... FOR UPDATE`):** `ClassBookingService.book_session` ve `cancel_booking` çağrılarında hedef `class_sessions` satırı PostgreSQL üzerinde kilitlenir (`with_for_update()`). Eşzamanlı 10 rezervasyon burst denemesinde kapasite kesinlikle aşılmaz (sıfır overbooking).
2. **Kapasite ve Dinamik Yedek Sırası (FIFO Waitlist):**
   - Doluluk < Kapasite ise kayıt `CONFIRMED` olarak oluşturulur ve `class.booking_confirmed.v1` eventi yayınlanır.
   - Doluluk >= Kapasite ise kayıt `WAITLISTED` durumuna alınır, ardışık kuyruk numarası (`waitlist_position = 1..N`) verilir ve `class.booking_waitlisted.v1` eventi yayınlanır.
   - Kısmi tekil indeks (`uq_class_bookings_active_member`), üyenin aynı derse mükerrer aktif kayıt yapmasını veritabanı seviyesinde bloke eder.
3. **Otomatik Asil Listeye Terfi (`Auto-Promotion`):**
   - Asil listedeki bir üye rezervasyonunu iptal ettiğinde (`cancel_booking`), 1. sıradaki yedek (`waitlist_position = 1`) anında `CONFIRMED` statüsüne yükseltilir, `waitlist_position` alanı temizlenir ve `class.booking_promoted.v1` eventi üretilir.
   - Kalan tüm yedek üyelerin sıraları (`2..N`) tek bir atomik sorguyla kaydırılır (`waitlist_position = waitlist_position - 1`).
4. **Geç İptal Eşiği (`Cancellation Cutoff Window`):** Seans başlangıcına `cancellation_cutoff_minutes` süresinden daha az kalmışsa iptal işlemi `is_late_cancellation = True` olarak işaretlenir; kulüp no-show/hak yakma politikalarını işletebilir.
5. **Antrenör Çakışma Önleme (PT Conflict Lock):** `PtBookingService`, antrenörün mevcut randevularını zaman aralığı (`start_time_utc < new_end AND end_time_utc > new_start`) üzerinde kilitler; çakışan randevu denemeleri `409 Conflict` ile reddedilir.
6. **PostgreSQL RLS & Composite FK:** 6 tablo (`class_types`, `class_schedules`, `class_sessions`, `class_bookings`, `trainer_availabilities`, `pt_appointments`) `TenantMixin` ve PostgreSQL RLS ile yalıtılmıştır.

---

## 8. Bilinen açık maddeler

Bu bölüm doküman ile gerçeğin ayrışmasını önlemek içindir.

- `device_sessions` tablosunda RLS yok (yukarıdaki gerekçe — bilinçli tasarım).
- Ağır federasyon analitiği için rollup tablosu henüz yok (ADR-043 yol 3, ertelendi).
- Login rate limit normalde Redis'te ortak pencere kullanır; **Redis erişilemezse
  süreç-içi pencereye düşer** — yani çok süreçli kurulumda limit süreç sayısı kadar
  çarpılır. Bilinçli fail-open (login cache kesintisinde kapanmasın), `rate_limit.redis_*`
  uyarısıyla loglanır.
- Üretimde raporlar özel S3/MinIO storage'a yazılır: server-side encryption,
  tenant-bound key, kısa ömürlü presigned URL, bounded cleanup. Kod `main`'de;
  **gerçek bir kovaya hiç yazmadı** — staging kanıtı için kova ve kimlik bilgisi gerekir.
- QR imza sırları için AWS KMS zarf şifrelemesi (`kms:enc:` ile `GenerateDataKey` & `Decrypt`) ve fail-closed production boot kontrolleri `app.core.qr_crypto` altında uygulanmıştır; yerel geliştirmede `local:hmac:` kullanılır.
- `/metrics` gerçek request/dependency/outbox Prometheus metrikleri üretir; scraper,
  dashboard, alert ve trace backend'i dış altyapı işi olarak açıktır.
- Privileged roller için password-only erişim kapalıdır: kısa ömürlü restricted
  setup session, TOTP kayıt UX'i ve başarılı kayıt sonrası session rotation.
- Personel hesabı `POST /staff/accounts` ile açılır: tek kullanımlık parola bir kez
  döner, hesap `must_change_password` ile işaretlenir ve login yalnızca parola
  değiştirmeye yeten kısıtlı `password_reset` session verir. Session seviyesi tek
  yerde (`resolve_auth_level`) kararlaştırılır; MFA kaydı rotasyonun yerine geçmez.
  Parola teslimi ekrandan yapılır — e-posta davet akışı henüz yok.
- Phase 26 çıkış kapısı **geçilmedi**: dış pentest kanıtı yok.

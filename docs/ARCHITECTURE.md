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
| Federasyon Konsolu | `/superadmin` | `PLATFORM_SUPER_ADMIN`, `FEDERATION_ADMIN`, `FEDERATION_ANALYST`, `FEDERATION_SUPPORT` | Organizasyon/kulüp dizini, tenant başına metrikler, sistem audit kayıtları, tenant'a geçiş |
| Kulüp Operasyon Konsolu | `/` (+ `/members`, `/locations`, `/finance`) | `GYM_OWNER`, `GYM_ADMIN`, `GYM_MANAGER`, `ACCOUNTANT`, `FRONT_DESK` | Üye kaydı, abonelik, şube, finans |
| Antrenör Portalı | `/trainer` | `TRAINER` (+ `GYM_OWNER`, `GYM_ADMIN`) | Atanmış üyeler, turnike giriş geçmişi, hak kontrolü |
| Sporcu Portalı | `/member` | `MEMBER` | Üyelik/hak durumu, 60 sn'lik tek kullanımlık giriş QR'ı |
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

## 5. Bilinen açık maddeler

Bu bölüm doküman ile gerçeğin ayrışmasını önlemek içindir.

- `device_sessions` tablosunda RLS yok (yukarıdaki gerekçe — bilinçli tasarım).
- Ağır federasyon analitiği için rollup tablosu henüz yok (ADR-043 yol 3, ertelendi).
- Login rate limit normalde Redis'te ortak pencere kullanır; **Redis erişilemezse
  süreç-içi pencereye düşer** — yani çok süreçli kurulumda limit süreç sayısı kadar
  çarpılır. Bilinçli fail-open (login cache kesintisinde kapanmasın), `rate_limit.redis_*`
  uyarısıyla loglanır.
- Phase 26 çıkış kapısı **geçilmedi**: dış pentest kanıtı yok.

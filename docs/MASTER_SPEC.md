# FITNESS NETWORK OS — IMPLEMENTATION LOCKED MASTER SPECIFICATION

# 128. Eksik kalan en önemli mimari: Isolation Tier

İlk plan:

```text
Shared PostgreSQL
+
tenant_id
+
RLS
```

olarak kalsın.

Ama domain kodu:

```text
Tenant
   ↓
IsolationProvider
   ├── SharedRLS
   ├── DedicatedSchema
   └── DedicatedDatabase
```

şeklinde düşünülmeli.

Paketler ileride:

```text
CORE
Shared DB + RLS

PRO
Shared DB + RLS

ENTERPRISE
Dedicated schema (opsiyon)

FEDERATION ENTERPRISE
Dedicated DB (opsiyon)
```

olabilir.

Ama uygulama:

```python
get_member()
create_payment()
renew_membership()
```

seviyesinde tenant'ın hangi DB modelini kullandığını bilmemeli.

# 129. Tenant lifecycle eksik kalmıştı

Tenant yalnız:

```text
ACTIVE
INACTIVE
```

olmamalı.

Tam state machine:

```text
LEAD
 ↓
CONTRACTED
 ↓
PROVISIONING
 ↓
CONFIGURING
 ↓
MIGRATING
 ↓
READY
 ↓
ACTIVE
 ↓
SUSPENDED
 ↓
OFFBOARDING
 ↓
RETENTION
 ↓
DELETED
```

Örneğin `SUSPENDED`:

```text
Admin login       ALLOW
Members           ALLOW/DENY policy
New sales         DENY
QR access         configurable
Data export       ALLOW
```

olabilir.

`OFFBOARDING` sırasında:

```text
new writes             DENY
API keys               REVOKE
sessions               REVOKE
devices                REVOKE
webhooks               DISABLE
automation             STOP
data export            CREATE
data deletion          SCHEDULE
```

yapacağız.

# 130. Data Retention Engine

Şimdiye kadar “delete” dedik ama bunu ayrı domain yapmamız gerekiyor.

```text
data_retention_policies
data_retention_rules
deletion_requests
deletion_jobs
legal_holds
anonymization_jobs
```

Örneğin:

```text
Attendance
retain X

Financial transaction
retain Y

Audit log
retain Z

Marketing lead
retain A

Health/progress
retain B
```

Buradaki süreleri kodda hard-code etmeyelim.

```text
purpose
jurisdiction
tenant_policy
legal_basis
retention_period
deletion_method
```

ile policy haline getirelim.

# 131. Data Classification

Her kolon aynı güvenlik seviyesinde değil.

Ben:

```text
PUBLIC
INTERNAL
PERSONAL
CONFIDENTIAL
SPECIAL_CATEGORY
FINANCIAL
SECURITY_SECRET
```

sınıflandırması eklerdim.

Örneğin:

```text
first_name           PERSONAL
email                PERSONAL
body_fat             SPECIAL_CATEGORY
injury                SPECIAL_CATEGORY
payment_amount        FINANCIAL
password_hash         SECURITY_SECRET
QR signing key        SECURITY_SECRET
```

Progress/health alanları özellikle ayrı tutulmalı; KVKK sağlık ve biyometrik verileri özel nitelikli kişisel veri kapsamında ele alıyor. 

# 132. Consent Registry

Şunları birbirinden ayıracağız:

```text
privacy notice acknowledgement
marketing consent
WhatsApp consent
SMS consent
photo consent
health data consent
wearable consent
biometric consent
```

Model:

```text
consent_definitions
consent_versions
consent_records

member_id
consent_type
document_version
status
given_at
withdrawn_at
source
ip
```

Consent değişince geçmiş kayıt değiştirilmez. Yeni version çıkar.

# 133. Data Subject Request Center

İleride üye:

```text
Verilerimi göster
Düzelt
Dışa aktar
Belirli verileri sil
Marketing iletişimini kapat
```

isteyebilir.

Internal workflow:

```text
REQUEST
 ↓
VERIFY IDENTITY
 ↓
ASSESS
 ↓
EXECUTE
 ↓
APPROVE
 ↓
AUDIT
```

olmalı.

# 134. Authorization'ı iki aşamalı tasarlayalım

MVP:

```text
RBAC
+
Scope
+
RLS
```

doğru.

Ama federasyon ağı büyüdükçe şu ilişkiler çıkacak:

```text
User
 ↓
owns
Gym A

Trainer
 ↓
assigned_to
Member X

Federation Analyst
 ↓
can_view_aggregate
Region Y
```

Bu aşamada relationship-based authorization gerekebilir.

OpenFGA bu amaç için ReBAC + ABAC tarzı fine-grained authorization motoru sunuyor. 

Ben yine de **MVP'de OpenFGA koymam**.

Ama authorization interface'i:

```text
AuthorizationService

can(
 actor,
 action,
 resource,
 context
)
```

şeklinde tanımlarım. Sonradan implementation değişebilir.

# 135. Background jobs için Tenant Envelope

Çok kritik bir eksik.

Queue mesajı:

```json
{
  "event_id": "...",
  "tenant_id": "...",
  "actor_id": "...",
  "correlation_id": "...",
  "idempotency_key": "...",
  "payload": {}
}
```

taşımalı.

Worker:

```text
Job arrives
 ↓
Resolve tenant
 ↓
Validate tenant ACTIVE
 ↓
Establish RLS context
 ↓
Authorization
 ↓
Execute
```

yapmalı.

# 136. Noisy Neighbor koruması

Multi-tenant SaaS'ta bir gym:

```text
1M member export
```

başlatıp diğer gym'lerin QR girişini yavaşlatmamalı.

Bu yüzden:

```text
per-tenant API quota
per-tenant export quota
per-tenant job concurrency
per-tenant notification quota
per-tenant webhook quota
```

eklerdim.

# 137. Resource Budget

Plan entitlement yalnız feature değil:

```text
members_limit
locations_limit
staff_limit
storage_limit
API requests
WhatsApp quota
report exports
automation runs
```

da içerebilir.

```text
TenantQuotaService
```

oluşturacağız.

# 138. QR signing key lifecycle

QR'ın cryptographic tasarımında key rotation eksikti.

Örneğin:

```text
QR signing keys

kid = qr-2026-08-a
ACTIVE

kid = qr-2026-07
VERIFY_ONLY

kid = qr-2026-06
REVOKED
```

Token:

```text
kid
credential_id
jti
iat
exp
aud
tenant
```

taşır.

Böylece anahtar değiştirmek tüm üyeleri logout etmek anlamına gelmez.

# 139. Secret Management

Şunlar DB `.env` içinde saçılmamalı:

```text
Payment credentials
WhatsApp secrets
SMTP
QR signing keys
Device secrets
OAuth credentials
Encryption keys
```

Logical model:

```text
integration_secret_reference
```

olmalı.

Uygulama secret'ın kendisini değil secret-manager referansını kullanmalı.

# 140. Access Gateway'i vendor-neutral yapalım

```text
                     ACCESS CORE
                          │
                   Device Adapter API
                          │
        ┌─────────────────┼────────────────┐
        │                 │                │
       QR               ZKTeco           OSDP
        │                 │                │
     Tablet           Adapter          Adapter
```

Bizim ürün:

```text
ZKTecoService
```

değil:

```text
AccessDeviceAdapter
```

kullanmalı.

# 141. OSDP roadmap'e girsin

Hardware partner programında tercihen:

```text
OSDP
```

destekleyen cihazları hedefleyebiliriz.

Uzun vadeli hardware roadmap:

```text
Phase 1
Camera QR

Phase 2
Vendor APIs
ZKTeco etc.

Phase 3
OSDP Gateway

Phase 4
Certified Hardware Ecosystem
```

olmalı.

# 142. Device Capability Registry

Her cihaz aynı şeyi yapamaz.

```text
device_capabilities

QR_SCAN
RFID
NFC
FINGERPRINT
FACE
ENTRY_RELAY
EXIT_RELAY
OFFLINE_CACHE
REMOTE_UNLOCK
OSDP_SECURE_CHANNEL
```

# 143. Device heartbeat

Her Gateway:

```text
heartbeat every N sec
```

göndersin.

```text
ONLINE
DEGRADED
OFFLINE
CLOCK_DRIFT
SYNC_PENDING
CERTIFICATE_EXPIRING
```

durumu oluşabilsin.

# 144. Clock drift

QR ve fiziksel access sisteminde saat çok kritik.

Gateway:

```text
local_timestamp
server_timestamp
clock_offset
```

tutsun.

# 145. Offline access conflict resolution

Offline gateway:

```text
member active
```

snapshot'ı gördü.
Cloud'da 5 dakika sonra member blocked oldu.
Gateway internet yok.

Burada policy gerekiyor:

```text
offline entitlement TTL
emergency block list
last_known_state
```

# 146. PWA offline sınırlarını doğru çizelim

Member PWA:

```text
membership card
last known status
schedule
stored QR shell
```

gösterebilir.

Ama **güvenlik açısından yeni geçerli QR credential'ı yalnız client cache'den üretmemeli.**

# 147. Idempotency Framework

Bu şimdiye kadar eksikti ve P0.

Şu endpoint'lerde zorunlu:

```text
create payment
refund
renew membership
create invoice
consume entitlement
book class
issue guest pass
process webhook
```

Client:

```text
Idempotency-Key
```

gönderir.

Server:

```text
idempotency_keys

tenant_id
key
operation
request_hash
response
status
expires_at
```

tutar.

# 148. Webhook Inbox

Provider webhook gönderdi. Doğrudan business logic çalıştırmamalıyız.

```text
Webhook
 ↓
Verify signature
 ↓
webhook_inbox
 ↓
ACK
 ↓
Worker
 ↓
Idempotency check
 ↓
Process
```

# 149. Webhook Outbox

Biz dış sisteme gönderirken:

```text
member.created
payment.received
checkin.created
```

eventleri:

```text
webhook_subscriptions
webhook_deliveries
```

üzerinden gönderelim.

# 150. Standard Event Envelope

Internal event formatını standardize edelim.

```json
{
  "specversion": "1.0",
  "id": "...",
  "source": "membership",
  "type": "membership.renewed.v1",
  "time": "...",
  "subject": "...",
  "tenantid": "...",
  "correlationid": "...",
  "data": {}
}
```

# 151. Event versioning

Kesinlikle:

```text
membership.renewed.v1
```

düşünelim.

# 152. Automation engine büyüdüğünde workflow engine opsiyonu

İlk sürüm:

```text
DB + worker
```

yeterli.

# 153. SaaS billing'i kendi member billing'imizden tamamen ayıralım

```text
GYM MEMBER BILLING
```

bizim gym domain'imiz.

```text
PLATFORM BILLING
```

ise kullanım bazlı olabilir:

```text
active_members
locations
messages
API calls
storage
```

# 154. Metering

Bunun için:

```text
usage_events

tenant_id
metric
quantity
timestamp
source_event
```

tutalım.

# 155. Search altyapısı eksik

Başlangıçta PostgreSQL search yeterli.
Ama interface:

```text
SearchService
```

olsun.

Tenant-aware search şart:

```text
tenant_id
+
resource authorization
```

# 156. Report Engine

Hazır dashboard ile custom report farklı şeyler.

Model:

```text
report_definitions
report_runs
report_exports
scheduled_reports
```

# 157. Export güvenliği

Büyük export:

```text
request
 ↓
authorization snapshot
 ↓
async job
 ↓
encrypted file
 ↓
short-lived signed link
 ↓
auto-delete
```

olmalı.

# 158. Analytics PII ayrımı

Federation analytics warehouse'a mümkünse:

```text
member_id
```

yerine pseudonymous analytics key gönderilebilir.

# 159. Observability baştan kurulmalı

Her request:

```text
trace_id
tenant_id
request_id
user_id
operation
```

taşısın.

```text
FastAPI
 ↓
OpenTelemetry
 ↓
Collector
 ↓
Telemetry backend
```

# 160. Kritik business metrics ayrı

Business operational:

```text
QR validation latency
payment webhook lag
notification backlog
device offline count
failed imports
outbox backlog
```

# 161. Correlation ID

Hepsinde:

```text
correlation_id
```

aynı kalmalı.

# 162. PII log sanitization

Log:

```text
email
phone
health data
payment details
QR token
```

içermemeli.

# 163. Backup yetmez: restore drill

Plan:

```text
Daily backup
PITR
 ↓
Monthly automated restore
 ↓
Integrity checks
 ↓
Restore report
```

olmalı.

# 164. Disaster Recovery Runbook

Şu senaryoları yazılı hale getirelim:

```text
PostgreSQL unavailable
Redis unavailable
payment provider down
WhatsApp down
Access cloud down
Local Gateway down
object storage down
bad deployment
tenant security incident
QR signing key compromise
```

# 165. Security Incident Mode

Örneğin tenant credential leak:

```text
SUSPEND API KEYS
REVOKE SESSIONS
ROTATE SECRETS
FREEZE INTEGRATIONS
PRESERVE AUDIT
```

tek operasyonla yapılabilsin.

# 166. Feature rollout sistemi

Feature flag sadece:

```text
ON/OFF
```

olmamalı.

```text
platform
federation
tenant
location
percentage rollout
beta cohort
```

scope'u destekleyebilir.

# 167. Configuration versioning

```text
tenant_config_versions
```

Böylece:

```text
rollback to v128
```

mümkün olur.

# 168. Pricing versioning de aynı

```text
Platform Pro

2026
₺X

2027
₺Y
```

Eski müşteri contract'ı değişmemeli.

# 169. Accounting integration abstraction

Domain:

```text
AccountingAdapter
```

olmalı.

# 170. Money modeli

Para:

```text
float
```

olmaz.

```text
amount_minor
currency
```

veya decimal fixed precision.

# 171. Timezone tasarımı

Her timestamp:

```text
UTC
```

saklanır.

Ama:

```text
Federation timezone
Tenant timezone
Location timezone
User timezone
```

ayrıdır.

# 172. Localization

Bizim:

```text
i18n
currency
date formats
number formats
timezones
tenant branding
```

baştan desteklenebilir olmalı.

# 173. Accessibility

Ürün:

```text
admin
member
scanner
```

üç yüzeyde de keyboard navigation, contrast, screen-reader label gibi temel accessibility standartlarına uymalı.

# 174. Import Engine'i ayrı subsystem yapalım

```text
UPLOAD
 ↓
DETECT SCHEMA
 ↓
MAP
 ↓
NORMALIZE
 ↓
VALIDATE
 ↓
MATCH
 ↓
DEDUP
 ↓
PREVIEW
 ↓
IMPORT
 ↓
RECONCILE
```

olmalı.

# 175. Import rollback

Import batch:

```text
import_batch_id
```

ile bütün oluşturulan kayıtları işaretlesin.

# 176. Import reconciliation

```text
Old outstanding:  ₺120,230
New outstanding:  ₺120,230
✓ MATCH
```

# 177. Public API maturity model

```text
Internal API
 ↓
Partner API
 ↓
Public API
```

# 178. Integration Registry

```text
integration_definitions
integration_installations
integration_credentials
integration_mappings
integration_sync_runs
integration_errors
```

# 179. Integration Health

Gym:

```text
INTEGRATIONS

WhatsApp       ✓ HEALTHY
Payment        ✓ HEALTHY
Turnstile      ⚠ DEGRADED
Accounting     ✕ AUTH EXPIRED
```

# 180. GitHub projelerinden tam olarak ne alalım?

- **LaraGym**: membership domain, attendance, branch, PWA, audit
- **Spine Fitness**: device bridge, gate enforcement, partial payment, dedup, WhatsApp delivery lifecycle
- **Gympify**: SaaS feature benchmark, branding, custom domain, POS, QR/biometric, multi-location
- **FastAPI official template**: backend/frontend skeleton, Docker/CI yaklaşımı

# 181. GitHub konusunda önemli lisans/kalite prensibi

Her repo için onboarding checklist olmalı.

# 182. Database CI Gate

Her tenant-owned tablo için otomatik kontrol:

```text
✓ tenant_id exists
✓ NOT NULL
✓ index exists
✓ RLS enabled
✓ FORCE RLS where applicable
✓ SELECT policy
✓ INSERT policy
✓ UPDATE policy
✓ DELETE policy
✓ composite FK
✓ tenant tests
```

# 183. Schema Linter

Kendi script'imiz:

```text
scripts/check_tenancy.py
```

database metadata'yı tarasın. Merge bloklansın.

# 184. Permission Matrix CI

Bir YAML source-of-truth olsun.
Test generator buradan ALLOW/DENY senaryoları çıkarsın.

# 185. Contract tests

Integration adapter implement ediyorsa hepsi aynı test suite'i geçmeli.

# 186. Architecture Fitness Functions

CI yalnız unit test çalıştırmasın. Şunları da korusun:

```text
Domain A cannot import Domain B internals
No cross-tenant table without RLS
No controller accesses DB directly
No payment using float
No QR token without exp/jti
No health field exposed to federation DTO
```

# 187. Domain dependency rule

Örneğin:

```text
Membership
  ↓
Entitlements
```

ama:

```text
Membership
→ WhatsApp SDK
```

yasak.

# 188. Yeni tablolarla veri modeli genişlemesi

Toplam tablo 90-110 civarı. (TENANCY, PRIVACY, SECURITY, IDEMPOTENCY, WEBHOOK, DEVICE, IMPORT, REPORT, INTEGRATION, METERING tabloları)

# 189. Yeni ADR seti

```text
ADR-013 Hybrid Tenant Isolation
ADR-014 Tenant Lifecycle
ADR-015 Data Classification & Retention
ADR-016 Consent Versioning
ADR-017 Authorization Abstraction
ADR-018 Tenant Job Envelope
ADR-019 Idempotency
ADR-020 Webhook Inbox/Outbox
ADR-021 CloudEvents-compatible Events
ADR-022 Access Device Adapter
ADR-023 Offline Access Gateway
ADR-024 QR Signing Key Rotation
ADR-025 OpenTelemetry
ADR-026 Integration Adapter Framework
ADR-027 Metrics Registry
ADR-028 Platform Metering
ADR-029 Money & Currency
ADR-030 UTC + Location Timezone Semantics
```

# 190. Güncellenmiş implementation sırası

### Wave 0A — Architecture Lock
### Wave 0B — Security Foundation
### Wave 1 — Gym Core
### Wave 2 — Membership
### Wave 3 — Finance
### Wave 4 — Access
### Wave 5 — Operational MVP
### Wave 6 — Growth
### Wave 7 — Federation
### Wave 8 — Platform
### Wave 9 — Network
### Wave 10 — Intelligence

# 191. MVP çıkmadan geçilmesi gereken 10 Gate

| Gate | Zorunlu |
|---|---:|
| Tenant isolation test | ✅ |
| RLS coverage | ✅ |
| Permission regression | ✅ |
| Payment idempotency | ✅ |
| QR replay test | ✅ |
| Cross-tenant cache/storage test | ✅ |
| Backup restore test | ✅ |
| Tenant export/offboarding test | ✅ |
| Observability/SLO dashboard | ✅ |
| Load test | ✅ |

# 192. Load test profili

Gerçekçi senaryolarla test. Access latency (p50, p95, p99) ölçülür.

# 193. En önemli load-test prensibi

Noisy neighbor test. (Örn: Bir tenant dev export yaparken diğeri QR okutuyor mu?)

# 194. Business continuity test

Offline Access Gateway testleri.

# 195. Son ürün benchmark'ı

LaraGym + Spine Fitness + Gympify + Modern SaaS isolation + OpenFGA style extensibility.

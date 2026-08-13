# GymClubNex — AI Context Map

> **Stack:** fastapi | sqlalchemy | react | python
> **Microservices:** backend, fitness-network-os-frontend, admin-web, gymclubnex-e2e, public-site, scanner-pwa

> 88 routes | 71 models | 38 components | 60 lib files | 17 env vars | 6 middleware | 43% test coverage
> **Token savings:** this file is ~11,700 tokens. Without it, AI exploration would cost ~114,300 tokens. **Saves ~102,500 tokens per conversation.**
> **Last scanned:** 2026-08-13 18:44 — re-run after significant changes

---

# Routes

## CRUD Resources

- **``** GET | POST | GET/:id | PATCH/:id
- **`/deliveries`** GET | POST | GET/:id → Deliverie
- **`/runs`** GET | POST | GET/:id → Run
- **`/{trainer_user_id}/members`** GET | POST | GET/:id | DELETE/:id → Member

## Other Routes

- `POST` `/qr/issue` params() → in: IssueQrRequest, out: IssueQrResponse [auth]
- `POST` `/qr/issue-self` params() → in: IssueQrRequest, out: IssueQrResponse [auth]
- `POST` `/qr/validate` params() → in: IssueQrRequest, out: IssueQrResponse [auth]
- `POST` `/keys/rotate` params() → in: IssueQrRequest, out: IssueQrResponse
- `GET` `/keys` params() → in: UUI, out: IssueQrResponse
- `GET` `/organizations` params() → in: FederationScop, out: list
- `GET` `/tenants` params() → in: FederationScop, out: list
- `GET` `/tenants/{tenant_id}` params(tenant_id) → in: FederationScop, out: list
- `GET` `/federation/summary` params() → in: FederationScop, out: list
- `GET` `/audit` params() → in: FederationScop, out: list
- `GET` `/csrf` params() → out: CsrfResponse [auth]
- `POST` `/login` params() → in: LoginRequest, out: CsrfResponse [auth, db] ✓
- `POST` `/password` params() → in: LoginRequest, out: CsrfResponse [auth, db]
- `POST` `/logout` params() → in: LoginRequest, out: CsrfResponse [auth, db]
- `POST` `/provision` params() → in: ProvisionDeviceRequest, out: ProvisionDeviceResponse [auth]
- `POST` `/auth` params() → in: ProvisionDeviceRequest, out: ProvisionDeviceResponse [auth, db]
- `POST` `/revoke` params() → in: ProvisionDeviceRequest, out: ProvisionDeviceResponse [auth, db]
- `GET` `/` params() → in: UUI, out: ProvisionDeviceResponse [auth, db] ✓
- `POST` `/{member_id}/entitlements/check` params(member_id) → in: UUID, out: EntitlementAccessResponse [auth]
- `POST` `/{member_id}/entitlements/consume` params(member_id) → in: UUID, out: EntitlementAccessResponse [auth]
- `POST` `/billing-accounts` params() → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/invoices` params() → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/invoices/{invoice_id}/issue` params(invoice_id) → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/invoices/{invoice_id}/void` params(invoice_id) → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/payments` params() → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/payments/{payment_id}/refunds` params(payment_id) → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/credits` params() → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/credits/{credit_id}/apply` params(credit_id) → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/discounts` params() → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/reconciliations` params() → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/reconciliations/items/{item_id}/match` params(item_id) → in: BillingAccountCreate, out: BillingAccountResponse
- `POST` `/reconciliations/{run_id}/complete` params(run_id) → in: BillingAccountCreate, out: BillingAccountResponse
- `GET` `/invoices` params() → out: BillingAccountResponse
- `GET` `/payments` params() → out: BillingAccountResponse
- `GET` `/session` params() → in: AsyncSessio, out: MeSessionResponse [auth]
- `GET` `/profile` params() → in: AsyncSessio, out: MeSessionResponse [auth]
- `GET` `/member` params() → in: AsyncSessio, out: MeSessionResponse [auth] ✓
- `GET` `/memberships` params() → in: AsyncSessio, out: MeSessionResponse [auth]
- `GET` `/entitlements` params() → in: AsyncSessio, out: MeSessionResponse [auth]
- `GET` `/checkins` params() → in: AsyncSessio, out: MeSessionResponse [auth, db]
- `POST` `/entitlements/check` params() → in: MeEntitlementCheckRequest, out: MeSessionResponse [auth]
- `POST` `/{member_id}/status` params(member_id) → in: MemberCreate, out: MemberResponse
- `POST` `/{member_id}/tags` params(member_id) → in: MemberCreate, out: MemberResponse
- `GET` `/{member_id}/tags` params(member_id) → out: MemberResponse
- `POST` `/{member_id}/notes` params(member_id) → in: MemberCreate, out: MemberResponse
- `GET` `/{member_id}/notes` params(member_id) → out: MemberResponse
- `POST` `/{member_id}/consents` params(member_id) → in: MemberCreate, out: MemberResponse
- `GET` `/{member_id}/memberships` params(member_id) → out: MemberResponse
- `GET` `/{member_id}/access-logs` params(member_id) → out: MemberResponse [db]
- `POST` `/{membership_id}/freeze` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
- `POST` `/{membership_id}/unfreeze` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
- `POST` `/{membership_id}/cancel` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
- `POST` `/{membership_id}/renew` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
- `POST` `/{membership_id}/expire` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
- `POST` `/{membership_id}/past-due` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
- `POST` `/setup` params() → out: MfaSetupResponse [db, cache]
- `POST` `/verify` params() → out: MfaSetupResponse [auth, db]
- `POST` `/templates` params() → in: TemplateCreate, out: TemplateResponse
- `GET` `/templates` params() → in: UUI, out: TemplateResponse
- `POST` `/{plan_id}/versions` params(plan_id) → in: PlanCreate, out: PlanResponse
- `GET` `/versions` params() → in: UUI, out: PlanResponse
- `POST` `/versions/{plan_version_id}/publish` params(plan_version_id) → in: PlanCreate, out: PlanResponse
- `POST` `/definitions` params() → in: DefinitionCreate, out: DefinitionResponse
- `GET` `/definitions` params() → in: UUI, out: DefinitionResponse
- `POST` `/artifacts/cleanup` params() → in: DefinitionCreate, out: DefinitionResponse
- `POST` `/accounts` params() → in: StaffLinkRequest, out: StaffResponse [cache]
- `GET` `/public` params()
- `GET` `/health` params() [auth, db, cache] ✓
- `GET` `/live` params() ✓
- `GET` `/ready` params() [auth, db, cache]
- `GET` `/metrics` params() [auth] ✓
- `GET` `/ping` params() ✓

---

# Schema

### Base
- id: UUID (pk, default)
- created_at: DateTime (default)
- updated_at: DateTime (default)

### SigningKey
- kid: String (index)
- status: Enum (default)
- algorithm: String (default)
- key_material: String

### Device
- name: String
- location_id: UUID
- capabilities: with_variant (default)
- status: Enum (default)
- last_heartbeat_at: DateTime (nullable)
- api_key_hash: String (nullable)
- is_active: bool (default)
- _relations_: location: Location, sessions: DeviceSession

### DeviceSession
- device_id: UUID
- token_hash: String (unique, index)
- ip_address: String (nullable)
- expires_at: DateTime
- is_revoked: bool (default)
- signing_key_material: String (nullable)
- _relations_: device: Device

### AccessAttempt
- member_id: unknown (nullable)
- device_id: unknown (nullable)
- status: Enum
- denial_reason: String (nullable)
- jti: String (nullable, index)
- method: String (nullable, default)
- timestamp: DateTime (default)
- _relations_: member: Member, device: Device

### Checkin
- member_id: UUID
- location_id: UUID
- device_id: unknown (nullable)
- checkin_time: DateTime (default)
- checkout_time: DateTime (nullable)
- _relations_: member: Member, location: Location, device: Device

### OfflineSnapshot
- device_id: UUID
- snapshot_type: String
- payload: with_variant
- version: int (default)
- _relations_: device: Device

### DeviceNonce
- device_session_id: UUID
- nonce: String
- expires_at: DateTime (index)

### QrJtiReplay
- jti: String
- member_id: unknown (nullable)
- credential_id: String (nullable)
- expires_at: DateTime
- consumed_at: DateTime (default)

### AuditEvent
- user_id: unknown (index, nullable)
- action: String (index)
- resource_type: String (index)
- resource_id: unknown (index, nullable)
- old_state: JSON (nullable)
- new_state: JSON (nullable)
- ip_address: String (nullable)
- user_agent: String (nullable)

### ConsentDefinition
- name: String
- consent_type: String
- description: String (nullable)

### ConsentVersion
- definition_id: UUID
- version_number: String
- document_url: String (nullable)

### ConsentRecord
- member_id: UUID
- consent_type: String
- document_version: String
- status: String
- given_at: DateTime (nullable)
- withdrawn_at: DateTime (nullable)
- source: String (nullable)
- ip_address: String (nullable)

### EntitlementDefinition
- code: String
- name: String
- description: String (nullable)
- type: Enum
- is_active: Boolean (default)

### PlanEntitlement
- plan_version_id: UUID
- entitlement_id: UUID
- quantity: Integer (default)
- unlimited: Boolean (default)

### MembershipEntitlement
- membership_id: UUID
- entitlement_id: UUID
- source_plan_version_id: unknown (nullable)
- granted_quantity: Integer (default)
- unlimited: Boolean (default)
- valid_from: DateTime (nullable)
- valid_until: DateTime (nullable)
- status: String (default)

### EntitlementWallet
- member_id: UUID
- membership_id: UUID
- membership_entitlement_id: UUID
- entitlement_id: UUID
- allocated: Integer (default)
- reserved: Integer (default)
- consumed: Integer (default)
- remaining: Integer (default)
- expires_at: DateTime (nullable)

### EntitlementTransaction
- wallet_id: UUID
- membership_id: unknown (nullable)
- entitlement_id: unknown (nullable)
- transaction_type: String
- quantity: Integer (default)
- balance_before: Integer (default)
- balance_after: Integer (default)
- idempotency_key: String
- actor_id: unknown (nullable)
- reason: String (nullable)

### PassportConfig
- is_active: Boolean (default)
- allowed_home_gym_tiers: String (nullable)
- rules: JSON (nullable)

### ComplianceRecord
- certification_name: String
- status: String
- audit_date: DateTime (default)
- auditor_notes: String (nullable)

### NetworkAlert
- organization_id: UUID (fk)
- target_tenant_id: unknown (fk, nullable)
- title: String
- message: String
- severity: String (default)

### BillingAccount
- user_id: unknown (fk, nullable, index)
- member_id: unknown (nullable, index)
- currency: String (default)
- status: String (default)
- _relations_: invoices: Invoice, payments: Payment

### Invoice
- billing_account_id: UUID (index)
- membership_id: unknown (nullable, index)
- invoice_number: String (nullable)
- status: String (default)
- due_date: DateTime (nullable)
- issued_at: DateTime (nullable)
- voided_at: DateTime (nullable)
- currency: String (default)
- total_amount_minor: Integer (default)
- paid_amount_minor: Integer (default)
- discount_amount_minor: Integer (default)
- idempotency_key: String (nullable)
- _relations_: billing_account: BillingAccount, items: InvoiceItem, allocations: PaymentAllocation

### InvoiceItem
- invoice_id: UUID (index)
- description: String
- unit_amount_minor: Integer (default)
- quantity: Integer (default)
- amount_minor: Integer
- source_type: String (nullable)
- source_id: unknown (nullable)
- _relations_: invoice: Invoice

### Payment
- billing_account_id: UUID (index)
- amount_minor: Integer
- refunded_amount_minor: Integer (default)
- currency: String (default)
- status: String (default)
- method: String
- provider: String (nullable)
- provider_ref: String (nullable)
- idempotency_key: String (nullable)
- paid_at: DateTime (nullable)
- _relations_: billing_account: BillingAccount, allocations: PaymentAllocation

### PaymentAllocation
- payment_id: UUID (index)
- invoice_id: UUID (index)
- amount_minor: Integer
- _relations_: payment: Payment, invoice: Invoice, reversals: PaymentAllocationReversal

### PaymentAllocationReversal
- allocation_id: UUID (index)
- refund_id: unknown (nullable, index)
- amount_minor: Integer
- reason: String (nullable)
- _relations_: allocation: PaymentAllocation

### Refund
- payment_id: UUID (index)
- amount_minor: Integer
- currency: String (default)
- status: String (default)
- reason: String (nullable)
- idempotency_key: String
- actor_id: unknown (nullable)

### CreditNote
- billing_account_id: UUID (index)
- amount_minor: Integer
- remaining_minor: Integer
- currency: String (default)
- status: String (default)
- reason: String (nullable)
- idempotency_key: String
- actor_id: unknown (nullable)

### CreditApplication
- credit_note_id: UUID (index)
- invoice_id: UUID (index)
- amount_minor: Integer

### Discount
- code: String
- name: String
- amount_minor: Integer (nullable)
- percent_bps: Integer (nullable)
- is_active: Boolean (default)

### InvoiceDiscount
- invoice_id: UUID (index)
- discount_id: unknown (nullable)
- description: String
- amount_minor: Integer

### ReconciliationRun
- status: String (default)
- notes: Text (nullable)
- started_at: DateTime
- completed_at: DateTime (nullable)
- actor_id: unknown (nullable)

### ReconciliationItem
- run_id: UUID (index)
- external_ref: String
- amount_minor: Integer
- currency: String (default)
- status: String (default)
- matched_payment_id: unknown (nullable)

### Lead
- first_name: String
- last_name: String
- email: String (nullable, index)
- phone: String (nullable, index)
- source: String (nullable)
- status: String (default)

### Opportunity
- lead_id: unknown (nullable)
- member_id: unknown (nullable)
- stage: String (default)
- value_amount_minor: Integer (nullable)
- currency: String (default)
- probability: Integer (nullable)

### Task
- title: String
- description: Text (nullable)
- status: String (default)
- due_date: DateTime (nullable)
- assigned_to: unknown (fk, nullable)
- lead_id: unknown (nullable)
- member_id: unknown (nullable)

### RetentionCockpit
- member_id: UUID (unique)
- health_score: Integer (nullable)
- churn_probability_bps: Integer (nullable)
- last_calculated_at: DateTime (nullable)
- risk_level: String (nullable)

### IdempotencyKey
- key: String (index, unique)
- request_path: String
- request_params: JSON (nullable)
- response_status_code: Integer (nullable)
- response_body: JSON (nullable)
- expires_at: DateTime

### IdempotencyRecord
- key: String
- operation: String
- request_hash: String
- status: String (default)
- response_status: Integer (nullable)
- response_body: JSON (nullable)
- resource_type: String (nullable)
- resource_id: unknown (nullable)
- completed_at: DateTime (nullable)
- expires_at: DateTime
- locked_until: DateTime (nullable)
- owner_token: String (nullable)
- attempt_count: Integer (default)

### Location
- name: String
- timezone: String (default)
- address: String (nullable)

### Member
- member_number: String (index)
- first_name: String
- last_name: String
- email: String (nullable, index)
- phone: String (nullable, index)
- status: String (default)
- user_id: unknown (fk, nullable, index)

### Tag
- member_id: UUID
- name: String

### Note
- member_id: UUID
- content: String

### Plan
- name: String
- description: String (nullable)
- is_active: Boolean (default)

### PlanVersion
- plan_id: UUID
- version: Integer
- price_amount_minor: Integer
- currency: String (default)
- billing_cycle_months: Integer
- terms: JSON
- is_published: Boolean (default)
- published_at: DateTime (nullable)

### Membership
- member_id: UUID
- plan_version_id: UUID
- status: String (default)
- start_date: DateTime
- end_date: DateTime (nullable)
- scheduled_cancellation_at: DateTime (nullable)
- price_snapshot: Integer (nullable)
- price_snapshot_currency: String (nullable)
- terms_snapshot: JSON (nullable)

### Entitlement
- member_id: UUID
- membership_id: unknown (nullable)
- entitlement_type: String
- balance: Integer (default)

### MembershipPeriod
- membership_id: UUID
- start_date: DateTime
- end_date: DateTime
- is_active: Boolean (default)

### MembershipFreeze
- membership_id: UUID
- start_date: DateTime
- expected_end_date: DateTime (nullable)
- actual_end_date: DateTime (nullable)
- previous_status: String (nullable)
- reason: String (nullable)

### MembershipStatusHistory
- membership_id: UUID
- old_status: String
- new_status: String
- changed_at: DateTime
- changed_by_user_id: unknown (nullable)

### MembershipCancellation
- membership_id: UUID
- cancelled_at: DateTime
- effective_date: DateTime
- reason: String (nullable)
- changed_by_user_id: unknown (nullable)

### MembershipRenewal
- membership_id: UUID
- next_plan_version_id: unknown (nullable)
- renewal_date: DateTime
- status: String (default)
- price_snapshot: Integer (nullable)
- price_snapshot_currency: String (nullable)
- terms_snapshot: JSON (nullable)
- changed_by_user_id: unknown (nullable)

### NotificationTemplate
- code: String
- name: String
- channel: String
- subject_template: String (nullable)
- body_template: Text
- is_active: bool (default)
- locale: String (nullable)

### NotificationDelivery
- template_id: unknown (nullable)
- recipient_user_id: unknown (fk, nullable)
- recipient_address: String (nullable)
- channel: String
- status: String (default, index)
- subject: String (nullable)
- body: Text (nullable)
- context: JSON (default)
- error_message: Text (nullable)
- attempt_count: Integer (default)
- available_at: DateTime (nullable)
- sent_at: DateTime (nullable)
- dedupe_key: String (nullable)
- provider: String (nullable)
- provider_message_id: String (nullable)
- source_event_type: String (nullable)
- source_event_id: String (nullable)
- correlation_id: String (nullable)
- _relations_: template: NotificationTemplate, recipient: User

### Organization
- name: String
- domain: String (unique, nullable)
- _relations_: tenants: Tenant

### OutboxEvent
- event_type: String
- payload: JSON
- status: String (default, index)
- error_message: Text (nullable)
- attempt_count: Integer (default)
- available_at: DateTime (nullable)
- processed_at: DateTime (nullable)
- aggregate_type: String (nullable)
- aggregate_id: unknown (nullable)
- dedupe_key: String (nullable)
- worker_id: String (nullable)
- lease_until: DateTime (nullable)

### InboxEvent
- event_id: String (index)
- event_type: String
- payload: JSON
- status: String (default, index)
- error_message: Text (nullable)
- attempt_count: Integer (default)
- processed_at: DateTime (nullable)
- available_at: DateTime (nullable)

### Permission
- name: String (unique, index)
- description: String
- _relations_: roles: Role

### Role
- name: String (unique, index)
- description: String
- is_system: Boolean (default)
- _relations_: permissions: Permission, user_roles: UserRole

### UserRole
- user_id: UUID (fk, index)
- role_id: UUID (fk, index)
- tenant_id: unknown (fk, nullable, index)
- organization_id: unknown (fk, nullable, index)
- _relations_: role: Role

### ReportDefinition
- code: String
- name: String
- description: Text (nullable)
- report_type: String (default)
- config: JSON (default)
- is_active: bool (default)
- _relations_: runs: ReportRun

### ReportRun
- definition_id: UUID
- status: String (default)
- result_url: String (nullable)
- export_format: String (nullable)
- row_count: Integer (nullable)
- error_message: Text (nullable)
- parameters: JSON (nullable)
- requested_by_user_id: unknown (nullable)
- dedupe_key: String (nullable)
- started_at: DateTime (nullable)
- finished_at: DateTime (nullable)
- _relations_: definition: ReportDefinition

### Staff
- user_id: UUID (fk, index)
- location_id: unknown (nullable)
- role: String (default)

### Tenant
- name: String
- organization_id: UUID (fk)
- location_code: String (unique)
- _relations_: organization: Organization

### TrainerAssignment
- trainer_user_id: UUID (fk, index)
- member_id: UUID (index)
- is_active: Boolean (default)

### User
- email: String (unique, index)
- hashed_password: String
- is_active: Boolean (default)
- is_superuser: Boolean (default)
- must_change_password: Boolean (default)
- _relations_: sessions: UserSession, devices: UserDevice, mfa_methods: UserMfaMethod, user_roles: UserRole

### UserSession
- user_id: UUID (fk)
- token_hash: String (unique, index)
- ip_address: String (nullable)
- user_agent: String (nullable)
- expires_at: DateTime
- is_revoked: Boolean (default)
- auth_level: String (default)
- _relations_: user: User

### UserDevice
- user_id: UUID (fk)
- device_id: String (unique, index)
- device_name: String (nullable)
- is_trusted: Boolean (default)
- _relations_: user: User

### UserMfaMethod
- user_id: UUID (fk)
- secret: String (nullable)
- method_type: String (nullable)
- encrypted_secret: String (nullable)
- provider_id: String (nullable)
- is_active: Boolean (default)
- hashed_recovery_codes: with_variant (default)
- failed_attempts: int (default)
- locked_until: DateTime (nullable)
- _relations_: user: User

### DummyTenantItem
- name: String

---

# Components

- **App** — `frontend/admin-web/src/App.tsx`
- **AuthProvider** — `frontend/admin-web/src/auth/AuthContext.tsx`
- **Layout** — `frontend/admin-web/src/components/Layout.tsx`
- **MemberAccessLogs** — props: memberId — `frontend/admin-web/src/components/MemberAccessLogs.tsx`
- **MemberMemberships** — props: memberId — `frontend/admin-web/src/components/MemberMemberships.tsx`
- **ReloadPrompt** — `frontend/admin-web/src/components/ReloadPrompt.tsx`
- **RequireAuth** — `frontend/admin-web/src/components/RequireAuth.tsx`
- **RequireRole** — props: allowed — `frontend/admin-web/src/components/RequireRole.tsx`
- **Dashboard** — `frontend/admin-web/src/pages/Dashboard.tsx`
- **Devices** — `frontend/admin-web/src/pages/Devices.tsx`
- **Finance** — `frontend/admin-web/src/pages/Finance.tsx`
- **Locations** — `frontend/admin-web/src/pages/Locations.tsx`
- **Login** — `frontend/admin-web/src/pages/Login.tsx`
- **MemberPortal** — `frontend/admin-web/src/pages/MemberPortal.tsx`
- **Members** — `frontend/admin-web/src/pages/Members.tsx`
- **MfaSetup** — `frontend/admin-web/src/pages/MfaSetup.tsx`
- **Notifications** — `frontend/admin-web/src/pages/Notifications.tsx`
- **PasswordChange** — `frontend/admin-web/src/pages/PasswordChange.tsx`
- **Plans** — `frontend/admin-web/src/pages/Plans.tsx`
- **PortalHome** — `frontend/admin-web/src/pages/PortalHome.tsx`
- **Reports** — `frontend/admin-web/src/pages/Reports.tsx`
- **Staff** — `frontend/admin-web/src/pages/Staff.tsx`
- **SuperAdminPortal** — `frontend/admin-web/src/pages/SuperAdminPortal.tsx`
- **TrainerPortal** — `frontend/admin-web/src/pages/TrainerPortal.tsx`
- **RootLayout** — `frontend/public-site/src/app/layout.tsx`
- **Home** — `frontend/public-site/src/app/page.tsx`
- **Architecture** [client] — `frontend/public-site/src/components/Architecture.tsx`
- **BrandMark** — props: size, showWordmark — `frontend/public-site/src/components/BrandMark.tsx`
- **Cta** [client] — `frontend/public-site/src/components/Cta.tsx`
- **Features** [client] — `frontend/public-site/src/components/Features.tsx`
- **Footer** — `frontend/public-site/src/components/Footer.tsx`
- **Header** [client] — `frontend/public-site/src/components/Header.tsx`
- **Hero** [client] — `frontend/public-site/src/components/Hero.tsx`
- **Metrics** [client] — `frontend/public-site/src/components/Metrics.tsx`
- **Pricing** [client] — `frontend/public-site/src/components/Pricing.tsx`
- **App** — `frontend/scanner-pwa/src/App.tsx`
- **CameraQrScanner** — props: onDecode, active, onStop — `frontend/scanner-pwa/src/components/CameraQrScanner.tsx`
- **ReloadPrompt** — `frontend/scanner-pwa/src/components/ReloadPrompt.tsx`

---

# Libraries

- `backend/alembic/env.py`
  - function include_object: (object, name, type_, reflected, compare_to) -> bool
  - function run_migrations_offline: () -> None
  - function do_run_migrations: (connection) -> None
  - function run_migrations_online: () -> None
  - function run_async_migrations: () -> None
- `backend/alembic/versions/0a561fd73793_update_rbac_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/261bdee314d7_sync_usermfamethod.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/32bea30c0ed8_add_federation_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/332634d9dc20_phase_27_add_mfa_totp_fields.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/45e716039e1c_add_phase_8_membership_domain_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/62afa7f4b3b1_add_status_to_membership_renewals.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/6590aca081d6_make_expected_end_date_nullable.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/67eca287af30_add_operational_mvp_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/7558a909338a_phase_27_add_audit_events_model.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/8d4b31a89f92_add_growth_and_crm_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/8d7e354b271c_composite_tenant_fks.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/96b95a7a1de8_phase_27_add_device_auth_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/9d407d31b6cb_seed_rbac_canonical_matrix.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/a1b2c3d4e5f6_add_access_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/b3655ea622c4_add_chk_user_roles_tenant_or_org.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/b3e2852df357_add_entitlement_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/b5994ffbd643_add_membership_cancellation_and_renewal_.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/bc4033d03939_add_terms_json_fields.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/c4f9a1b2e3d0_seed_entitlement_permissions.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/c938894ffe0d_add_organization_and_tenant_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/c938894ffe0e_add_wave_1_core_gym_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/c938894ffe0f_add_wave_2_membership.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/ca8b3fd77206_add_missing_tables.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/d5e6f7a8b9c0_phase10_finance_domain.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/dd603a516953_add_users_rbac_and_finance_models.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/e0675d75481a_add_phase_8_fixes.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/e6f7a8b9c0d1_seed_finance_permissions.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/f7a8b9c0d1e2_phase11_remove_money_floats.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/h1a2b3c4d5e6_phase12_idempotency_records.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/i2b3c4d5e6f7_phase13_qr_access_engine.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/j3c4d5e6f7a8_seed_access_permissions.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/k4d5e6f7a8b9_phase14_member_gym_core.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/l5e6f7a8b9c0_phase15_outbox_inbox_engine.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/m6f7a8b9c0d1_seed_outbox_permissions.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/n7a8b9c0d1e2_phase15_5_integrity_closure.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/o8b9c0d1e2f3_phase15_5b_rbac_member_user_bind.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/p9c0d1e2f3a4_phase15_5c_trust_boundaries.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/q0d1e2f3a4b5_phase16_notifications_reports.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/r1e2f3a4b5c6_seed_devices_manage_permission.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/s2f3a4b5c6d7_trainer_assignments_and_member_read_all.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/t3a4b5c6d7e8_audit_events_rls.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/u4b5c6d7e8f9_device_channel_request_signing.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/v5c6d7e8f9a0_privileged_mfa_session_level.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/alembic/versions/w6d7e8f9a0b1_forced_password_rotation.py` — function upgrade: () -> None, function downgrade: () -> None
- `backend/fix_tests.py` — function repl_success: (m)
- `backend/scripts/check_no_money_floats.py`
  - function scan_models: () -> list[str]
  - function scan_source_ast: () -> list[str]
  - function main: () -> int
- `backend/scripts/check_permissions.py` — function main: ()
- `backend/scripts/check_permissions_db.py` — function main: () -> int
- `backend/scripts/check_release_truth.py`
  - function require: (path, *needles) -> list[str]
  - function forbid: (path, *needles) -> list[str]
  - function main: () -> int
- `backend/scripts/check_tenancy.py` — function check_db_rls: (errors, table_name), function main_async: ()
- `backend/scripts/process_notification_due.py`
  - function build_parser: () -> argparse.ArgumentParser
  - function main: (argv) -> int
  - function process_due_for_tenant: (session, tenant_id, *, limit, max_attempts) -> dict[str, int]
- `backend/scripts/seed_active_membership.py` — function seed_active_membership: ()
- `backend/scripts/seed_demo_tenant.py` — function main: (argv) -> int, function seed_demo: (*, email, password, role_name, with_member, with_location) -> dict[str, str | None]
- `backend/scripts/seed_entitlements.py` — function seed_entitlements: ()
- `backend/scripts/seed_role_matrix.py` — function main: () -> int, function seed: () -> dict[str, object]
- `backend/src/backend/__init__.py` — function main: () -> None
- `frontend/admin-web/src/api/client.ts`
  - function getBaseUrl: () => string
  - function getTenantId: () => string | null
  - function setAuth: (tenantId) => void
  - function clearAuth: () => void
  - function isAuthenticated: () => boolean
  - function ensureCsrf: () => Promise<string>
  - _...3 more_
- `frontend/admin-web/src/auth/roles.ts`
  - function homeRouteFor: (roles, isSuperuser) => string
  - type RoleName
  - const ROLES
  - const FEDERATION_ROLES: RoleName[]
  - const OPS_ROLES: RoleName[]
  - const TRAINER_ROLES: RoleName[]
  - _...1 more_
- `frontend/scanner-pwa/src/api/client.ts`
  - function getBaseUrl: () => string
  - function getTenantId: () => string | null
  - function setAuth: (tenantId) => void
  - function clearAuth: () => void
  - function getDeviceKey: () => Promise<CryptoKey | null>
  - function authenticateDevice: (deviceId, tenantId, apiKey) => Promise<DeviceAuthResult>
  - _...5 more_

---

# Config

## Environment Variables

- `ALLOW_DESTRUCTIVE_TEST_RESET` **required** — backend/tests/conftest.py
- `CI` **required** — frontend/e2e/playwright.config.ts
- `DATABASE_URL` (has default) — backend/.env.example
- `E2E_OWNER_TOTP_SECRET` (has default) — backend/scripts/seed_role_matrix.py
- `ENCRYPTION_KEY` **required** — backend/app/core/security.py
- `ENVIRONMENT` **required** — backend/app/core/security.py
- `MIGRATOR_DATABASE_URL` (has default) — backend/.env.example
- `NEXT_PUBLIC_ADMIN_URL` **required** — frontend/public-site/src/components/Cta.tsx
- `QR_KMS_MODE` (has default) — backend/app/core/qr_crypto.py
- `REDIS_URL` (has default) — backend/.env.example
- `SMTP_PASS` **required** — backend/app/services/notification_providers.py
- `SMTP_PORT` (has default) — backend/app/services/notification_providers.py
- `SMTP_USER` **required** — backend/app/services/notification_providers.py
- `TEST_DATABASE_URL` **required** — backend/scripts/check_permissions_db.py
- `TEST_RUNTIME_DATABASE_URL` (has default) — backend/tests/conftest.py
- `VITE_API_URL` (has default) — frontend/scanner-pwa/.env
- `VITE_SCANNER_URL` (has default) — frontend/admin-web/src/pages/PortalHome.tsx

## Config Files

- `backend/.env.example`
- `docker-compose.yml`
- `frontend/admin-web/tailwind.config.js`
- `frontend/admin-web/vite.config.ts`
- `frontend/public-site/next.config.ts`
- `frontend/scanner-pwa/tailwind.config.js`
- `frontend/scanner-pwa/vite.config.ts`

---

# Middleware

## auth
- csrf — `backend/app/api/middleware/csrf.py`
- request_logging — `backend/app/api/middleware/request_logging.py`
- test_rate_limit — `backend/tests/api/test_rate_limit.py`
- auth — `frontend/e2e/tests/helpers/auth.ts`

## rate-limit
- rate_limit — `backend/app/api/middleware/rate_limit.py`

## cors
- test_config_cors — `backend/tests/core/test_config_cors.py`

---

# Dependency Graph

## Most Imported Files (change these carefully)

- `backend/app/models/user.py` — imported by **43** files
- `backend/app/models/tenant.py` — imported by **39** files
- `backend/app/models/organization.py` — imported by **34** files
- `backend/app/db/base.py` — imported by **32** files
- `backend/app/api/deps.py` — imported by **31** files
- `backend/app/models/member.py` — imported by **30** files
- `backend/app/models/rbac.py` — imported by **27** files
- `backend/app/db/session.py` — imported by **22** files
- `backend/app/models/membership.py` — imported by **20** files
- `frontend/admin-web/src/api/client.ts` — imported by **19** files
- `backend/app/db/rls.py` — imported by **18** files
- `backend/app/core/authorization.py` — imported by **18** files
- `backend/app/main.py` — imported by **18** files
- `backend/app/core/config.py` — imported by **16** files
- `backend/app/models/location.py` — imported by **12** files
- `backend/app/models/outbox.py` — imported by **12** files
- `frontend/admin-web/src/components/ui/index.ts` — imported by **12** files
- `backend/app/models/access.py` — imported by **11** files
- `frontend/admin-web/src/auth/AuthContext.tsx` — imported by **11** files
- `backend/app/core/security.py` — imported by **10** files

## Import Map (who imports what)

- `backend/app/models/user.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/devices.py`, `backend/app/api/v1/endpoints/entitlements.py` +38 more
- `backend/app/models/tenant.py` ← `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/app/services/resolution.py`, `backend/app/workers/notification.py`, `backend/app/workers/report.py` +34 more
- `backend/app/models/organization.py` ← `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/scripts/seed_demo_tenant.py`, `backend/scripts/seed_role_matrix.py`, `backend/tests/api/test_admin_federation.py` +29 more
- `backend/app/db/base.py` ← `backend/alembic/env.py`, `backend/app/models/access.py`, `backend/app/models/audit.py`, `backend/app/models/consent.py`, `backend/app/models/entitlement.py` +27 more
- `backend/app/api/deps.py` ← `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/admin.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/devices.py`, `backend/app/api/v1/endpoints/entitlements.py` +26 more
- `backend/app/models/member.py` ← `backend/app/api/v1/endpoints/auth.py`, `backend/app/models/__init__.py`, `backend/app/services/access.py`, `backend/app/services/federation.py`, `backend/app/services/finance.py` +25 more
- `backend/app/models/rbac.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/models/__init__.py`, `backend/app/models/user.py`, `backend/app/services/notification.py` +22 more
- `backend/app/db/session.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/memberships.py`, `backend/app/api/v1/endpoints/plans.py`, `backend/app/main.py`, `backend/app/workers/notification.py` +17 more
- `backend/app/models/membership.py` ← `backend/app/models/__init__.py`, `backend/app/services/entitlement.py`, `backend/app/services/federation.py`, `backend/app/services/membership.py`, `backend/app/services/resolution.py` +15 more
- `frontend/admin-web/src/api/client.ts` ← `frontend/admin-web/src/auth/AuthContext.tsx`, `frontend/admin-web/src/components/Layout.tsx`, `frontend/admin-web/src/components/MemberAccessLogs.tsx`, `frontend/admin-web/src/components/MemberMemberships.tsx`, `frontend/admin-web/src/pages/Dashboard.tsx` +14 more

---

# Test Coverage

> **43%** of routes and models are covered by tests
> 72 test files found

## Covered Routes

- POST:/login
- GET:/
- POST:
- GET:
- GET:/member
- GET:/health
- GET:/live
- GET:/metrics
- GET:/ping

## Covered Models

- Base
- SigningKey
- Device
- DeviceSession
- AccessAttempt
- Checkin
- OfflineSnapshot
- QrJtiReplay
- AuditEvent
- ConsentDefinition
- ConsentRecord
- EntitlementDefinition
- MembershipEntitlement
- EntitlementWallet
- EntitlementTransaction
- PassportConfig
- ComplianceRecord
- BillingAccount
- Invoice
- InvoiceItem
- Payment
- PaymentAllocation
- PaymentAllocationReversal
- Refund
- Discount
- ReconciliationItem
- Lead
- Opportunity
- Task
- RetentionCockpit
- IdempotencyRecord
- Location
- Member
- Tag
- Note
- Plan
- PlanVersion
- Membership
- Entitlement
- MembershipPeriod
- MembershipFreeze
- MembershipRenewal
- NotificationTemplate
- NotificationDelivery
- Organization
- OutboxEvent
- InboxEvent
- Permission
- Role
- UserRole
- ReportDefinition
- ReportRun
- Staff
- Tenant
- TrainerAssignment
- User
- UserSession
- UserMfaMethod
- DummyTenantItem

---

# CI/CD Pipelines

## GitHub Actions (1 workflow)

| Workflow | Triggers | Jobs | Deploy | Environments |
|---|---|---|---|---|
| CI | push, pull_request | 10 | — | — |

### CI

> `.github/workflows/ci.yml`

- **security** on `ubuntu-latest` — 7 steps
  - `actions/checkout@v5`
  - `trufflesecurity/trufflehog@a7082b69f5bc6167bbe27ebab82bf6707f267bf6`
  - `actions/setup-python@v6`
- **sbom** on `ubuntu-latest` — 2 steps
  - `actions/checkout@v5`
  - `anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610`
- **lint** on `ubuntu-latest` — 10 steps
  - `actions/checkout@v5`
  - `actions/setup-python@v6`
- **test** on `ubuntu-latest` — 9 steps (needs: security, lint)
  - `actions/checkout@v5`
  - `actions/setup-python@v6`
- **admin-web** on `ubuntu-latest` — 4 steps
  - `actions/checkout@v5`
  - `actions/setup-node@v5`
- **scanner-pwa** on `ubuntu-latest` — 4 steps
  - `actions/checkout@v5`
  - `actions/setup-node@v5`
- **production-image** on `ubuntu-latest` — 2 steps
  - `actions/checkout@v5`
- **public-site** on `ubuntu-latest` — 4 steps
  - `actions/checkout@v5`
  - `actions/setup-node@v5`
- **browser-e2e** on `ubuntu-latest` — 11 steps (needs: test, admin-web, scanner-pwa)
  - `actions/checkout@v5`
  - `actions/setup-python@v6`
  - `actions/setup-node@v5`
  - `actions/upload-artifact@v4`
- **all-green** on `ubuntu-latest` — 1 steps (needs: test, admin-web, scanner-pwa, public-site, production-image, browser-e2e)

---
_Source: .github/workflows/ci.yml_
_Generated by codesight-cicd-plugin_

---

# Git Hooks

> **Note for agents:** These hooks fire automatically on git operations and will block the operation if they fail.

## `pre-commit` — raw git hook

- **set**: `set -e`
- **changed=$(git**: `changed=$(git diff --cached --name-only --diff-filter=ACMR)`
- **case**: `case "$changed" in`
- ***.py|*.ts|*.tsx|*.md|*backend/*|*frontend/*|*docs/*)**: `*.py|*.ts|*.tsx|*.md|*backend/*|*frontend/*|*docs/*) ;;`
- ***)**: `*) exit 0 ;;`
- **esac**: `esac`
- **command**: `command -v npx >/dev/null 2>&1 || exit 0`
- **npx**: `npx --yes --no-install codesight --wiki >/dev/null 2>&1 || exit 0`
- **if**: `if [ -d docs ]; then`
- **npx**: `npx --yes --no-install codesight --mode knowledge docs -o .codesight >/dev/null 2>&1 || true`
- **fi**: `fi`
- **git**: `git add .codesight >/dev/null 2>&1 || true`
- **exit**: `exit 0`

_Source: .git/hooks/pre-commit_

---

_Generated by [codesight](https://github.com/Houseofmvps/codesight) — see your codebase clearly_
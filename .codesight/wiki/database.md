# Database

> **Navigation aid.** Schema shapes and field types extracted via AST. Read the actual schema source files before writing migrations or query logic.

**sqlalchemy** — 86 models

### Base

pk: `id` (UUID)

- `id`: UUID _(pk, default)_
- `created_at`: DateTime _(default)_
- `updated_at`: DateTime _(default)_

### SigningKey

- `kid`: String _(index)_
- `status`: Enum _(default)_
- `algorithm`: String _(default)_
- `key_material`: String

### Device

- `name`: String
- `location_id`: UUID
- `capabilities`: with_variant _(default)_
- `status`: Enum _(default)_
- `last_heartbeat_at`: DateTime _(nullable)_
- `api_key_hash`: String _(nullable)_
- `is_active`: bool _(default)_
- _relations_: location: Location, sessions: DeviceSession

### DeviceSession

- `device_id`: UUID
- `token_hash`: String _(unique, index)_
- `ip_address`: String _(nullable)_
- `expires_at`: DateTime
- `is_revoked`: bool _(default)_
- `signing_key_material`: String _(nullable)_
- _relations_: device: Device

### AccessAttempt

- `member_id`: unknown _(nullable)_
- `device_id`: unknown _(nullable)_
- `status`: Enum
- `denial_reason`: String _(nullable)_
- `jti`: String _(nullable, index)_
- `method`: String _(nullable, default)_
- `snapshot_data`: with_variant _(nullable)_
- `timestamp`: DateTime _(default)_
- _relations_: member: Member, device: Device

### Checkin

- `member_id`: UUID
- `location_id`: UUID
- `device_id`: unknown _(nullable)_
- `checkin_time`: DateTime _(default)_
- `checkout_time`: DateTime _(nullable)_
- _relations_: member: Member, location: Location, device: Device

### OfflineSnapshot

- `device_id`: UUID
- `snapshot_type`: String
- `payload`: with_variant
- `version`: int _(default)_
- _relations_: device: Device

### DeviceNonce

- `device_session_id`: UUID
- `nonce`: String
- `expires_at`: DateTime _(index)_

### QrJtiReplay

- `jti`: String
- `member_id`: unknown _(nullable)_
- `credential_id`: String _(nullable)_
- `expires_at`: DateTime
- `consumed_at`: DateTime _(default)_

### AuditEvent

- `user_id`: unknown _(index, nullable)_
- `action`: String _(index)_
- `resource_type`: String _(index)_
- `resource_id`: unknown _(index, nullable)_
- `old_state`: JSON _(nullable)_
- `new_state`: JSON _(nullable)_
- `ip_address`: String _(nullable)_
- `user_agent`: String _(nullable)_

### ClassType

- `name`: String
- `category`: String _(default)_
- `duration_minutes`: Integer _(default)_
- `default_capacity`: Integer _(default)_
- `color_hex`: String _(default)_
- `required_entitlement_type`: String _(nullable)_
- `cancellation_cutoff_minutes`: Integer _(default)_
- `is_active`: Boolean _(default)_

### ClassSchedule

fk: trainer_user_id

- `location_id`: UUID
- `class_type_id`: UUID
- `trainer_user_id`: UUID _(fk, index)_
- `day_of_week`: SmallInteger
- `start_time`: Time
- `end_time`: Time
- `room_name`: String _(nullable)_
- `capacity`: Integer
- `is_active`: Boolean _(default)_

### ClassSession

fk: trainer_user_id

- `location_id`: UUID
- `class_type_id`: UUID
- `schedule_id`: unknown _(nullable)_
- `trainer_user_id`: UUID _(fk, index)_
- `start_time_utc`: DateTime _(index)_
- `end_time_utc`: DateTime
- `room_name`: String _(nullable)_
- `capacity`: Integer
- `status`: ClassSessionStatus _(default)_

### ClassBooking

- `session_id`: UUID
- `member_id`: UUID
- `status`: ClassBookingStatus _(default)_
- `waitlist_position`: Integer _(nullable)_
- `booked_at`: DateTime
- `attended_at`: DateTime _(nullable)_
- `cancelled_at`: DateTime _(nullable)_
- `cancellation_reason`: String _(nullable)_
- `is_late_cancellation`: Boolean _(default)_

### TrainerAvailability

fk: trainer_user_id

- `trainer_user_id`: UUID _(fk, index)_
- `location_id`: UUID
- `day_of_week`: SmallInteger
- `start_time`: Time
- `end_time`: Time
- `slot_duration_minutes`: Integer _(default)_
- `is_active`: Boolean _(default)_

### PtAppointment

fk: trainer_user_id

- `trainer_user_id`: UUID _(fk, index)_
- `member_id`: UUID
- `location_id`: UUID
- `start_time_utc`: DateTime _(index)_
- `end_time_utc`: DateTime
- `status`: PtAppointmentStatus _(default)_
- `notes`: Text _(nullable)_
- `booked_at`: DateTime
- `attended_at`: DateTime _(nullable)_
- `cancelled_at`: DateTime _(nullable)_

### BreakGlassSession

- `actor_id`: UUID _(index)_
- `target_tenant_id`: UUID _(index)_
- `reason`: Text
- `ticket_reference`: String
- `status`: String _(default)_
- `granted_at`: DateTime
- `expires_at`: DateTime
- `revoked_at`: DateTime _(nullable)_
- `actions_taken`: Text _(nullable)_

### ConsentDefinition

- `name`: String
- `consent_type`: String
- `description`: String _(nullable)_

### ConsentVersion

- `definition_id`: UUID
- `version_number`: String
- `document_url`: String _(nullable)_

### ConsentRecord

- `member_id`: UUID
- `consent_type`: String
- `document_version`: String
- `status`: String
- `given_at`: DateTime _(nullable)_
- `withdrawn_at`: DateTime _(nullable)_
- `source`: String _(nullable)_
- `ip_address`: String _(nullable)_

### DataImportBatch

- `filename`: String
- `status`: String _(default)_
- `total_rows`: Integer _(default)_
- `valid_rows`: Integer _(default)_
- `invalid_rows`: Integer _(default)_
- `imported_rows`: Integer _(default)_
- `created_by_user_id`: UUID
- `created_at`: DateTime _(default)_
- `completed_at`: DateTime _(nullable)_
- _relations_: rows: DataImportRow

### DataImportRow

- `batch_id`: UUID _(index)_
- `row_number`: Integer
- `status`: String _(default)_
- `raw_data`: with_variant
- `parsed_data`: with_variant _(nullable)_
- `error_message`: Text _(nullable)_
- _relations_: batch: DataImportBatch

### DsarRequest

fk: requested_by_user_id

- `member_id`: UUID
- `requested_by_user_id`: unknown _(fk, nullable)_
- `kind`: String
- `status`: String
- `due_at`: DateTime
- `package_uri`: String _(nullable)_
- `rejection_reason`: Text _(nullable)_
- `dedupe_key`: String _(nullable)_

### EntitlementDefinition

- `code`: String
- `name`: String
- `description`: String _(nullable)_
- `type`: Enum
- `is_active`: Boolean _(default)_

### PlanEntitlement

- `plan_version_id`: UUID
- `entitlement_id`: UUID
- `quantity`: Integer _(default)_
- `unlimited`: Boolean _(default)_

### MembershipEntitlement

- `membership_id`: UUID
- `entitlement_id`: UUID
- `source_plan_version_id`: unknown _(nullable)_
- `granted_quantity`: Integer _(default)_
- `unlimited`: Boolean _(default)_
- `valid_from`: DateTime _(nullable)_
- `valid_until`: DateTime _(nullable)_
- `status`: String _(default)_

### EntitlementWallet

- `member_id`: UUID
- `membership_id`: UUID
- `membership_entitlement_id`: UUID
- `entitlement_id`: UUID
- `allocated`: Integer _(default)_
- `reserved`: Integer _(default)_
- `consumed`: Integer _(default)_
- `remaining`: Integer _(default)_
- `expires_at`: DateTime _(nullable)_

### EntitlementTransaction

- `wallet_id`: UUID
- `membership_id`: unknown _(nullable)_
- `entitlement_id`: unknown _(nullable)_
- `transaction_type`: String
- `quantity`: Integer _(default)_
- `balance_before`: Integer _(default)_
- `balance_after`: Integer _(default)_
- `idempotency_key`: String
- `actor_id`: unknown _(nullable)_
- `reason`: String _(nullable)_

### PassportConfig

- `is_active`: Boolean _(default)_
- `allowed_home_gym_tiers`: String _(nullable)_
- `rules`: JSON _(nullable)_

### ComplianceRecord

- `certification_name`: String
- `status`: String
- `audit_date`: DateTime _(default)_
- `auditor_notes`: String _(nullable)_

### NetworkAlert

fk: organization_id, target_tenant_id

- `organization_id`: UUID _(fk)_
- `target_tenant_id`: unknown _(fk, nullable)_
- `title`: String
- `message`: String
- `severity`: String _(default)_

### BillingAccount

fk: user_id

- `user_id`: unknown _(fk, nullable, index)_
- `member_id`: unknown _(nullable, index)_
- `currency`: String _(default)_
- `status`: String _(default)_
- _relations_: invoices: Invoice, payments: Payment

### Invoice

- `billing_account_id`: UUID _(index)_
- `membership_id`: unknown _(nullable, index)_
- `invoice_number`: String _(nullable)_
- `status`: String _(default)_
- `due_date`: DateTime _(nullable)_
- `issued_at`: DateTime _(nullable)_
- `voided_at`: DateTime _(nullable)_
- `currency`: String _(default)_
- `total_amount_minor`: Integer _(default)_
- `paid_amount_minor`: Integer _(default)_
- `discount_amount_minor`: Integer _(default)_
- `retry_count`: Integer _(default)_
- `next_retry_at`: DateTime _(nullable)_
- `idempotency_key`: String _(nullable)_
- _relations_: billing_account: BillingAccount, items: InvoiceItem, allocations: PaymentAllocation

### InvoiceItem

- `invoice_id`: UUID _(index)_
- `description`: String
- `unit_amount_minor`: Integer _(default)_
- `quantity`: Integer _(default)_
- `amount_minor`: Integer
- `source_type`: String _(nullable)_
- `source_id`: unknown _(nullable)_
- _relations_: invoice: Invoice

### Payment

- `billing_account_id`: UUID _(index)_
- `amount_minor`: Integer
- `refunded_amount_minor`: Integer _(default)_
- `currency`: String _(default)_
- `status`: String _(default)_
- `method`: String
- `provider`: String _(nullable)_
- `provider_ref`: String _(nullable)_
- `idempotency_key`: String _(nullable)_
- `paid_at`: DateTime _(nullable)_
- _relations_: billing_account: BillingAccount, allocations: PaymentAllocation

### PaymentAllocation

- `payment_id`: UUID _(index)_
- `invoice_id`: UUID _(index)_
- `amount_minor`: Integer
- _relations_: payment: Payment, invoice: Invoice, reversals: PaymentAllocationReversal

### PaymentAllocationReversal

- `allocation_id`: UUID _(index)_
- `refund_id`: unknown _(nullable, index)_
- `amount_minor`: Integer
- `reason`: String _(nullable)_
- _relations_: allocation: PaymentAllocation

### Refund

- `payment_id`: UUID _(index)_
- `amount_minor`: Integer
- `currency`: String _(default)_
- `status`: String _(default)_
- `reason`: String _(nullable)_
- `idempotency_key`: String
- `actor_id`: unknown _(nullable)_

### CreditNote

- `billing_account_id`: UUID _(index)_
- `amount_minor`: Integer
- `remaining_minor`: Integer
- `currency`: String _(default)_
- `status`: String _(default)_
- `reason`: String _(nullable)_
- `idempotency_key`: String
- `actor_id`: unknown _(nullable)_

### CreditApplication

- `credit_note_id`: UUID _(index)_
- `invoice_id`: UUID _(index)_
- `amount_minor`: Integer

### Discount

- `code`: String
- `name`: String
- `amount_minor`: Integer _(nullable)_
- `percent_bps`: Integer _(nullable)_
- `is_active`: Boolean _(default)_

### InvoiceDiscount

- `invoice_id`: UUID _(index)_
- `discount_id`: unknown _(nullable)_
- `description`: String
- `amount_minor`: Integer

### ReconciliationRun

- `status`: String _(default)_
- `notes`: Text _(nullable)_
- `started_at`: DateTime
- `completed_at`: DateTime _(nullable)_
- `actor_id`: unknown _(nullable)_

### ReconciliationItem

- `run_id`: UUID _(index)_
- `external_ref`: String
- `amount_minor`: Integer
- `currency`: String _(default)_
- `status`: String _(default)_
- `matched_payment_id`: unknown _(nullable)_

### PaymentAttempt

- `invoice_id`: UUID _(index)_
- `billing_account_id`: UUID _(index)_
- `attempt_number`: Integer _(default)_
- `amount_minor`: Integer
- `currency`: String _(default)_
- `status`: String _(default)_
- `gateway_provider`: String _(nullable)_
- `gateway_attempt_ref`: String _(nullable)_
- `error_code`: String _(nullable)_
- `error_message`: Text _(nullable)_
- `attempted_at`: DateTime _(default)_

### DunningPolicy

- `name`: String _(default)_
- `grace_period_days`: Integer _(default)_
- `max_retry_attempts`: Integer _(default)_
- `retry_interval_days`: Integer _(default)_
- `block_access_on_failure`: Boolean _(default)_
- `is_active`: Boolean _(default)_

### Lead

- `first_name`: String
- `last_name`: String
- `email`: String _(nullable, index)_
- `phone`: String _(nullable, index)_
- `source`: String _(nullable)_
- `status`: String _(default)_

### Opportunity

- `lead_id`: unknown _(nullable)_
- `member_id`: unknown _(nullable)_
- `stage`: String _(default)_
- `value_amount_minor`: Integer _(nullable)_
- `currency`: String _(default)_
- `probability`: Integer _(nullable)_

### Task

fk: assigned_to

- `title`: String
- `description`: Text _(nullable)_
- `status`: String _(default)_
- `due_date`: DateTime _(nullable)_
- `assigned_to`: unknown _(fk, nullable)_
- `lead_id`: unknown _(nullable)_
- `member_id`: unknown _(nullable)_

### RetentionCockpit

- `member_id`: UUID _(unique)_
- `health_score`: Integer _(nullable)_
- `churn_probability_bps`: Integer _(nullable)_
- `last_calculated_at`: DateTime _(nullable)_
- `risk_level`: String _(nullable)_

### IdempotencyKey

- `key`: String _(index, unique)_
- `request_path`: String
- `request_params`: JSON _(nullable)_
- `response_status_code`: Integer _(nullable)_
- `response_body`: JSON _(nullable)_
- `expires_at`: DateTime

### IdempotencyRecord

- `key`: String
- `operation`: String
- `request_hash`: String
- `status`: String _(default)_
- `response_status`: Integer _(nullable)_
- `response_body`: JSON _(nullable)_
- `resource_type`: String _(nullable)_
- `resource_id`: unknown _(nullable)_
- `completed_at`: DateTime _(nullable)_
- `expires_at`: DateTime
- `locked_until`: DateTime _(nullable)_
- `owner_token`: String _(nullable)_
- `attempt_count`: Integer _(default)_

### AccountInvite

fk: user_id

- `user_id`: UUID _(fk)_
- `token_hash`: String
- `purpose`: String
- `expires_at`: DateTime
- `accepted_at`: DateTime _(nullable)_

### Location

- `name`: String
- `timezone`: String _(default)_
- `address`: String _(nullable)_

### Member

fk: user_id

- `member_number`: String _(index)_
- `first_name`: String
- `last_name`: String
- `email`: String _(nullable, index)_
- `phone`: String _(nullable, index)_
- `status`: String _(default)_
- `user_id`: unknown _(fk, nullable, index)_

### Tag

- `member_id`: UUID
- `name`: String

### Note

- `member_id`: UUID
- `content`: String

### Plan

- `name`: String
- `description`: String _(nullable)_
- `is_active`: Boolean _(default)_

### PlanVersion

- `plan_id`: UUID
- `version`: Integer
- `price_amount_minor`: Integer
- `currency`: String _(default)_
- `billing_cycle_months`: Integer
- `terms`: JSON
- `is_published`: Boolean _(default)_
- `published_at`: DateTime _(nullable)_

### Membership

- `member_id`: UUID
- `plan_version_id`: UUID
- `status`: String _(default)_
- `start_date`: DateTime
- `end_date`: DateTime _(nullable)_
- `scheduled_cancellation_at`: DateTime _(nullable)_
- `price_snapshot`: Integer _(nullable)_
- `price_snapshot_currency`: String _(nullable)_
- `terms_snapshot`: JSON _(nullable)_

### Entitlement

- `member_id`: UUID
- `membership_id`: unknown _(nullable)_
- `entitlement_type`: String
- `balance`: Integer _(default)_

### MembershipPeriod

- `membership_id`: UUID
- `start_date`: DateTime
- `end_date`: DateTime
- `is_active`: Boolean _(default)_

### MembershipFreeze

- `membership_id`: UUID
- `start_date`: DateTime
- `expected_end_date`: DateTime _(nullable)_
- `actual_end_date`: DateTime _(nullable)_
- `previous_status`: String _(nullable)_
- `reason`: String _(nullable)_

### MembershipStatusHistory

- `membership_id`: UUID
- `old_status`: String
- `new_status`: String
- `changed_at`: DateTime
- `changed_by_user_id`: unknown _(nullable)_

### MembershipCancellation

- `membership_id`: UUID
- `cancelled_at`: DateTime
- `effective_date`: DateTime
- `reason`: String _(nullable)_
- `changed_by_user_id`: unknown _(nullable)_

### MembershipRenewal

- `membership_id`: UUID
- `next_plan_version_id`: unknown _(nullable)_
- `renewal_date`: DateTime
- `status`: String _(default)_
- `price_snapshot`: Integer _(nullable)_
- `price_snapshot_currency`: String _(nullable)_
- `terms_snapshot`: JSON _(nullable)_
- `changed_by_user_id`: unknown _(nullable)_

### NotificationTemplate

- `code`: String
- `name`: String
- `channel`: String
- `subject_template`: String _(nullable)_
- `body_template`: Text
- `is_active`: bool _(default)_
- `locale`: String _(nullable)_

### NotificationDelivery

fk: recipient_user_id

- `template_id`: unknown _(nullable)_
- `recipient_user_id`: unknown _(fk, nullable)_
- `recipient_address`: String _(nullable)_
- `channel`: String
- `status`: String _(default, index)_
- `subject`: String _(nullable)_
- `body`: Text _(nullable)_
- `context`: JSON _(default)_
- `error_message`: Text _(nullable)_
- `attempt_count`: Integer _(default)_
- `available_at`: DateTime _(nullable)_
- `sent_at`: DateTime _(nullable)_
- `dedupe_key`: String _(nullable)_
- `provider`: String _(nullable)_
- `provider_message_id`: String _(nullable)_
- `source_event_type`: String _(nullable)_
- `source_event_id`: String _(nullable)_
- `correlation_id`: String _(nullable)_
- _relations_: template: NotificationTemplate, recipient: User

### TenantOnboarding

- `current_stage`: String _(default)_
- `step_data`: with_variant
- `is_completed`: Boolean _(default)_
- `completed_at`: DateTime _(nullable)_

### Organization

- `name`: String
- `domain`: String _(unique, nullable)_
- _relations_: tenants: Tenant

### OutboxEvent

- `event_type`: String
- `payload`: JSON
- `status`: String _(default, index)_
- `error_message`: Text _(nullable)_
- `attempt_count`: Integer _(default)_
- `available_at`: DateTime _(nullable)_
- `processed_at`: DateTime _(nullable)_
- `aggregate_type`: String _(nullable)_
- `aggregate_id`: unknown _(nullable)_
- `dedupe_key`: String _(nullable)_
- `worker_id`: String _(nullable)_
- `lease_until`: DateTime _(nullable)_

### InboxEvent

- `event_id`: String _(index)_
- `event_type`: String
- `payload`: JSON
- `status`: String _(default, index)_
- `error_message`: Text _(nullable)_
- `attempt_count`: Integer _(default)_
- `processed_at`: DateTime _(nullable)_
- `available_at`: DateTime _(nullable)_

### Permission

- `name`: String _(unique, index)_
- `description`: String
- _relations_: roles: Role

### Role

- `name`: String _(unique, index)_
- `description`: String
- `is_system`: Boolean _(default)_
- _relations_: permissions: Permission, user_roles: UserRole

### UserRole

fk: user_id, role_id, tenant_id, organization_id

- `user_id`: UUID _(fk, index)_
- `role_id`: UUID _(fk, index)_
- `tenant_id`: unknown _(fk, nullable, index)_
- `organization_id`: unknown _(fk, nullable, index)_
- _relations_: role: Role

### ReportDefinition

- `code`: String
- `name`: String
- `description`: Text _(nullable)_
- `report_type`: String _(default)_
- `config`: JSON _(default)_
- `is_active`: bool _(default)_
- _relations_: runs: ReportRun

### ReportRun

- `definition_id`: UUID
- `status`: String _(default)_
- `result_url`: String _(nullable)_
- `export_format`: String _(nullable)_
- `row_count`: Integer _(nullable)_
- `error_message`: Text _(nullable)_
- `parameters`: JSON _(nullable)_
- `requested_by_user_id`: unknown _(nullable)_
- `dedupe_key`: String _(nullable)_
- `started_at`: DateTime _(nullable)_
- `finished_at`: DateTime _(nullable)_
- _relations_: definition: ReportDefinition

### DataRetentionPolicy

- `data_category`: String
- `description`: Text
- `retention_days`: Integer _(nullable)_
- `deletion_method`: String _(default)_
- `legal_basis`: String _(nullable)_
- `is_active`: Boolean _(default)_
- `requires_legal_review`: Boolean _(default)_

### Staff

fk: user_id

- `user_id`: UUID _(fk, index)_
- `location_id`: unknown _(nullable)_
- `role`: String _(default)_

### Tenant

fk: organization_id

- `name`: String
- `organization_id`: UUID _(fk)_
- `location_code`: String _(unique)_
- `status`: String _(default)_
- `suspended_at`: DateTime _(nullable)_
- `closed_at`: DateTime _(nullable)_
- `suspension_reason`: Text _(nullable)_
- `closure_reason`: Text _(nullable)_
- _relations_: organization: Organization

### TrainerAssignment

fk: trainer_user_id

- `trainer_user_id`: UUID _(fk, index)_
- `member_id`: UUID _(index)_
- `is_active`: Boolean _(default)_

### User

- `email`: String _(unique, index)_
- `hashed_password`: String
- `is_active`: Boolean _(default)_
- `is_superuser`: Boolean _(default)_
- `must_change_password`: Boolean _(default)_
- _relations_: sessions: UserSession, devices: UserDevice, mfa_methods: UserMfaMethod, user_roles: UserRole

### UserSession

fk: user_id

- `user_id`: UUID _(fk)_
- `token_hash`: String _(unique, index)_
- `ip_address`: String _(nullable)_
- `user_agent`: String _(nullable)_
- `expires_at`: DateTime
- `is_revoked`: Boolean _(default)_
- `auth_level`: String _(default)_
- `last_seen_at`: DateTime _(nullable)_
- `last_step_up_at`: DateTime _(nullable)_
- _relations_: user: User

### UserDevice

fk: user_id

- `user_id`: UUID _(fk)_
- `device_id`: String _(unique, index)_
- `device_name`: String _(nullable)_
- `is_trusted`: Boolean _(default)_
- _relations_: user: User

### UserMfaMethod

fk: user_id

- `user_id`: UUID _(fk)_
- `secret`: String _(nullable)_
- `method_type`: String _(nullable)_
- `encrypted_secret`: String _(nullable)_
- `provider_id`: String _(nullable)_
- `is_active`: Boolean _(default)_
- `hashed_recovery_codes`: with_variant _(default)_
- `failed_attempts`: int _(default)_
- `locked_until`: DateTime _(nullable)_
- _relations_: user: User

### DummyTenantItem

- `name`: String

## Schema Source Files

Read and edit these files when adding columns, creating migrations, or changing relations:

- `backend/app/models/user.py` — imported by **71** files
- `backend/app/models/tenant.py` — imported by **63** files
- `backend/app/models/organization.py` — imported by **56** files
- `backend/app/models/rbac.py` — imported by **44** files
- `backend/app/models/member.py` — imported by **43** files
- `backend/app/db/base.py` — imported by **38** files
- `backend/app/db/session.py` — imported by **35** files
- `backend/app/models/membership.py` — imported by **28** files
- `backend/app/models/location.py` — imported by **24** files
- `backend/app/db/rls.py` — imported by **22** files
- `backend/app/models/access.py` — imported by **19** files
- `backend/app/models/outbox.py` — imported by **17** files
- `backend/app/models/finance.py` — imported by **16** files

---
_Back to [overview.md](./overview.md)_
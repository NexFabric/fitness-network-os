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
- snapshot_data: with_variant (nullable)
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

### BreakGlassSession
- actor_id: UUID (index)
- target_tenant_id: UUID (index)
- reason: Text
- ticket_reference: String
- status: String (default)
- granted_at: DateTime
- expires_at: DateTime
- revoked_at: DateTime (nullable)
- actions_taken: Text (nullable)

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

### DataImportBatch
- filename: String
- status: String (default)
- total_rows: Integer (default)
- valid_rows: Integer (default)
- invalid_rows: Integer (default)
- imported_rows: Integer (default)
- created_by_user_id: UUID
- created_at: DateTime (default)
- completed_at: DateTime (nullable)
- _relations_: rows: DataImportRow

### DataImportRow
- batch_id: UUID (index)
- row_number: Integer
- status: String (default)
- raw_data: with_variant
- parsed_data: with_variant (nullable)
- error_message: Text (nullable)
- _relations_: batch: DataImportBatch

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
- retry_count: Integer (default)
- next_retry_at: DateTime (nullable)
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

### PaymentAttempt
- invoice_id: UUID (index)
- billing_account_id: UUID (index)
- attempt_number: Integer (default)
- amount_minor: Integer
- currency: String (default)
- status: String (default)
- gateway_provider: String (nullable)
- gateway_attempt_ref: String (nullable)
- error_code: String (nullable)
- error_message: Text (nullable)
- attempted_at: DateTime (default)

### DunningPolicy
- name: String (default)
- grace_period_days: Integer (default)
- max_retry_attempts: Integer (default)
- retry_interval_days: Integer (default)
- block_access_on_failure: Boolean (default)
- is_active: Boolean (default)

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

### TenantOnboarding
- current_stage: String (default)
- step_data: with_variant
- is_completed: Boolean (default)
- completed_at: DateTime (nullable)

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

### DataRetentionPolicy
- data_category: String
- description: Text
- retention_days: Integer (nullable)
- deletion_method: String (default)
- legal_basis: String (nullable)
- is_active: Boolean (default)
- requires_legal_review: Boolean (default)

### Staff
- user_id: UUID (fk, index)
- location_id: unknown (nullable)
- role: String (default)

### Tenant
- name: String
- organization_id: UUID (fk)
- location_code: String (unique)
- status: String (default)
- suspended_at: DateTime (nullable)
- closed_at: DateTime (nullable)
- suspension_reason: Text (nullable)
- closure_reason: Text (nullable)
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

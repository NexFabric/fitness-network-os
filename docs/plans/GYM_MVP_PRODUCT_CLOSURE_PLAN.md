# Gym MVP Product Closure Plan

**Scope:** Gym operations MVP, excluding physical equipment and inventory management
**Status:** Reviewed target plan; current implementation and remaining work are separated explicitly
**Reviewed:** 2026-08-11
**Branch reviewed:** `feat/phase27-ui-production-closure`
**Baseline:** `b1a5f7b`
**Production verdict:** **NO-GO until the exit gates in Section 18 pass**

## 1. Executive Decision

Fitness Network OS does not need another foundational redesign for its gym MVP.
The repository already has a strong technical core: tenant isolation, RLS,
tenant-safe foreign keys, member and membership domains, entitlements, finance,
idempotency, authenticated access devices, QR replay protection, notification
delivery, audit, outbox/inbox mechanics, and CI/build gates.

The remaining risk is product closure. Several backend capabilities exist but
do not yet form a complete, low-friction daily operating workflow for a gym.
The work should therefore move from infrastructure expansion to end-to-end
business capabilities:

```text
Member
  -> Membership
  -> Billing and Collections
  -> Access Decision and Check-in
  -> Reception Operations
  -> Member Self-Service
  -> Notifications and Dashboard
  -> Tenant Onboarding and Import
  -> Production Operations and Evidence
```

The MVP is complete only when a real gym can be onboarded, migrate its member
data, sell and manage memberships, collect money, control entry, operate the
front desk, notify members, and recover from operational failures without
manual database intervention.

## 2. Scope Boundary

### Included

- member and membership lifecycle;
- plan versions and entitlements;
- invoicing, payments, refunds, balances, failed-payment handling, and dunning;
- QR-based access decisions and check-ins;
- staff roles and daily reception workflows;
- responsive member self-service;
- operational notifications and delivery tracking;
- day-one operational dashboard and drill-downs;
- tenant onboarding and validated CSV migration;
- support access, jobs visibility, audit, backup/restore, observability, and E2E
  evidence.

### Explicitly excluded

- physical gym equipment and inventory operations;
- asset QR labels, custody, maintenance, and equipment booking;
- workout programming and exercise libraries;
- body measurements, nutrition, AI coaching, and wearables;
- social/community, gamification, loyalty, and advanced marketing automation;
- a trainer marketplace;
- microservice, Kafka, or Kubernetes expansion.

Physical asset work is tracked separately in
[`SHELF_NU_ADAPTATION_REFERENCE.md`](./SHELF_NU_ADAPTATION_REFERENCE.md).

## 3. Truth Review of the Submitted Plan

The submitted plan is directionally correct, but several points were stale or
too broad when compared with the reviewed repository.

### 3.1 Already implemented; do not reopen as missing

- Member status has an allowlisted state machine in `MemberService`.
- Membership lifecycle supports start, freeze, unfreeze, cancel, renew, expire,
  scheduled activation, and past-due transitions.
- Plan versions, price/terms snapshots, membership periods, freezes,
  cancellations, and renewals exist.
- Finance includes billing accounts, invoices/items, payments, allocations,
  allocation reversals, refunds, credits, discounts, and reconciliation.
- Access validation checks signed QR credentials, replay, and entitlement,
  records `AccessAttempt`, and creates `Checkin` rows.
- Device provisioning and device sessions exist.
- `SELF` authorization compares actual resource ownership, and `/me/*` routes
  resolve the authenticated user's member binding.
- Notification templates/deliveries include retries, deduplication, terminal
  `DEAD`, provider metadata, and delivery state.
- Outbox retry exhaustion moves events to `DEAD`; the old crash-loop concern is
  closed and tested.
- Canonical versioned event registration exists and is enforced on enqueue.
- Browser E2E scaffolding exists for admin login and scanner loading.
- A restore-drill script exists.

### 3.2 Implemented but incomplete for a sellable MVP

- Member and membership lifecycle exist separately, but the product-level
  journey and staff UX do not yet cover every transition coherently.
- Finance core is strong, but payment-attempt history, configurable dunning,
  access-block policy, and complete collection workflows are absent.
- Access attempts exist, but they lack the complete decision snapshot needed to
  explain a historical allow/deny decision reliably.
- Admin Web supports basic members, locations, membership actions, and finance
  lists, but there is no dedicated reception workspace.
- Member Portal securely issues a self QR, but does not yet provide membership,
  entitlement, payment, check-in, or profile views already exposed by `/me/*`.
- Dashboard currently shows basic member/location counts and a finance link;
  it is not an operational KPI dashboard.
- Playwright tests are shallow smoke tests, not production closure evidence.
- Restore automation exists, but an actual dated drill result is still
  unverified.
- `/live`, `/ready`, and metrics endpoints exist, but monitoring, alerts, job
  health, and durable production evidence remain incomplete.

### 3.3 Still target work

- payment-attempt ledger and provider-attempt normalization;
- configurable dunning and grace/access policy;
- dedicated reception console;
- complete member self-service UI;
- operational KPI read models and dashboard;
- tenant onboarding workflow;
- validated preview/confirm/import pipeline;
- governed support sessions;
- job/outbox/notification operations console;
- classes/waitlist and PT appointment domains, if product scope requires them.

## 4. Capability Status Matrix

Legend: `IMPLEMENTED`, `PARTIAL`, `TARGET`, `DEFERRED`.

| Capability | Status | Current evidence | Closure decision |
|---|---|---|---|
| Tenant/RLS foundation | IMPLEMENTED | `TenantMixin`, RLS helpers, tenancy CI/tests | Preserve; no redesign |
| Member identity/profile | IMPLEMENTED | Member API, tags, notes, consent, user binding | Add unified profile UX |
| Member lifecycle | PARTIAL | Validated transitions exist | Add business semantics, history, UI actions |
| Membership lifecycle | IMPLEMENTED core | Full service transitions and history models | Close workflows and staff UX |
| Plan/entitlement engine | IMPLEMENTED core | Published plan versions, wallets, consumption | Add clear product projections |
| Invoice/payment/refund | IMPLEMENTED core | Mature finance model/services | Add collection workflows and attempt ledger |
| Dunning/past-due policy | TARGET | Membership can be marked past due | Add tenant policy and orchestration |
| Access/QR/check-in | IMPLEMENTED core | Device auth, signed QR, replay, entitlement | Add policy engine and richer decision record |
| Reception operations | TARGET | Generic admin pages only | Build task-focused reception workspace |
| Staff/RBAC | IMPLEMENTED core | Role/permission/scope model and staff API | Verify persona-specific UX and least privilege |
| Member self-service | PARTIAL | `/me/*` APIs plus QR-only portal | Build complete responsive member view |
| Notifications | IMPLEMENTED core | Template/delivery/retry/provider architecture | Wire business triggers and preferences |
| Operational dashboard | PARTIAL | Basic counts and links | Add trusted KPI queries and drill-downs |
| Tenant onboarding | TARGET | No complete wizard/workflow | Build resumable onboarding state machine |
| CSV migration | TARGET | Master spec only | Build validate/preview/confirm/import pipeline |
| Support/federation | PARTIAL | Federation reads and audited superuser tenant entry | Add governed support session lifecycle |
| Job operations | TARGET | Backend queues/outbox exist | Add safe operational visibility/actions |
| Backup/restore | PARTIAL | Script exists | Run and archive evidence; test failure paths |
| Observability | PARTIAL | Health/ready/metrics baseline | Add dependencies, alerts, runbooks, SLOs |
| Browser E2E | PARTIAL | Two smoke specs | Cover money/access/member failure paths |
| Classes/PT | DEFERRED | Trainer assignment only | MVP+1 unless a launch gym requires classes/PT |

## 5. Target Business Capability Architecture

```text
FITNESS NETWORK OS

USER SURFACES
  Member Web/PWA
  Reception Console
  Trainer Portal
  Manager/Owner Console
  Federation/Support Console
  Scanner PWA

BUSINESS CAPABILITIES
  Member Lifecycle
  Membership and Entitlements
  Billing and Collections
  Access Decision and Check-in
  Notifications
  Operational Dashboard
  Tenant Onboarding and Import
  Classes/PT (MVP+1 unless required)

PLATFORM SERVICES
  Tenant Context
  Identity and MFA
  RBAC and Scope
  Audit
  Idempotency
  Outbox/Inbox and Jobs
  Files and Reporting
  Observability

DATA AND SECURITY
  PostgreSQL
  RLS
  Immutable Finance Records
  Access Decision Evidence
  Backup/Restore
  KMS/Secret Manager target
```

The architecture report should show this capability layer above infrastructure
diagrams. It must mark every component as implemented, partial, or target.

## 6. Member and Membership Lifecycle Closure

### 6.1 Keep member and membership states separate

`Member` represents the person/customer relationship. `Membership` represents
one commercial access contract. One member can have multiple memberships over
time.

Recommended meanings:

```text
Member
  LEAD -> PROSPECT -> ACTIVE -> INACTIVE/SUSPENDED -> ARCHIVED

Membership
  DRAFT/PENDING/SCHEDULED -> ACTIVE
  ACTIVE -> FROZEN -> ACTIVE
  ACTIVE -> PAST_DUE -> ACTIVE
  ACTIVE -> CANCELLED
  ACTIVE -> EXPIRED
```

Do not add `FROZEN`, `PAST_DUE`, or `EXPIRED` to `Member.status`; those describe
a contract, not a person.

### 6.2 Remaining work

- Define business descriptions for every existing status and transition.
- Ensure all transitions append membership status history and audit context.
- Expose transition availability from the server, so the UI does not recreate
  lifecycle rules.
- Add scheduled cancellation, effective cancellation, and reactivation views.
- Show all historical memberships in the member timeline.
- Make concurrent freeze/renew/cancel operations deterministic.
- Publish appropriate domain events in the same transaction.

### 6.3 Required staff workflow

```text
Find/create member
  -> select published plan version
  -> show immutable price and terms snapshot
  -> choose start/end/renewal policy
  -> create membership
  -> create/issue invoice
  -> collect or record payment
  -> activate entitlement
  -> issue access eligibility
```

The workflow must support retry after a payment or notification failure without
creating duplicate memberships, invoices, or entitlements.

## 7. Billing, Payment Attempts, and Dunning

### 7.1 Preserve the current finance ledger

The current invoice/payment/allocation/refund/credit design is substantially
stronger than a simple `payments` table. Do not replace it.

### 7.2 Add payment attempts

A provider request is not the same as a successful payment. Introduce an
append-only `payment_attempts` concept linked to billing account, invoice,
member, and the resulting payment when successful.

Candidate fields:

- `tenant_id`, `billing_account_id`, `invoice_id`;
- provider, method, provider attempt reference;
- amount/currency in minor units;
- status: `PENDING`, `REQUIRES_ACTION`, `SUCCEEDED`, `FAILED`, `CANCELLED`;
- normalized failure category and private provider detail;
- `idempotency_key`, requested/completed timestamps;
- correlation/request ID.

Provider payloads and card data must not be stored or logged. The backend
recalculates totals and is the source of truth.

### 7.3 Configurable dunning

Candidate tenant-owned configuration:

```text
DunningPolicy
  grace_period_days
  retry_offsets_days
  reminder_offsets_days
  mark_past_due_after_days
  block_access_when_past_due
  suspend_after_days
  enabled
```

Candidate case lifecycle:

```text
PAYMENT_FAILED
  -> RETRY_SCHEDULED
  -> REMINDER_SENT
  -> GRACE_PERIOD
  -> PAST_DUE
  -> ACCESS_RESTRICTED (policy dependent)
  -> SUSPENDED (policy dependent)
  -> RECOVERED / CLOSED
```

Rules:

- policy changes do not silently rewrite historical cases;
- every retry and reminder is idempotent;
- access restriction is an explicit policy outcome, not inferred ad hoc;
- successful collection closes the case and can recover membership state;
- staff overrides require reason and audit evidence;
- failed background jobs move to terminal/dead state and become visible.

## 8. Access Policy and Decision Evidence

### 8.1 Current strength

The current access path verifies tenant-bound signed tokens, key status,
expiration, replay, and entitlement. It records an access attempt and creates a
check-in after grant.

### 8.2 Required policy layer

The decision service should evaluate a documented sequence:

```text
Authenticated device and tenant/location binding
  -> token signature/audience/expiry/replay
  -> member state
  -> active membership state
  -> tenant dunning/access policy
  -> entitlement and remaining quantity
  -> business hours/capacity policy when enabled
  -> duplicate-inside policy
  -> ALLOW or DENY
```

Do not allow UI clients to choose which security checks run. Any diagnostic or
admin bypass must be separately permissioned, reasoned, audited, and disabled
on public/device paths.

### 8.3 Decision reason taxonomy

Use stable developer-facing reason codes and map them to short Turkish UI copy.

Candidate codes:

```text
TOKEN_MALFORMED
TOKEN_EXPIRED
TOKEN_REPLAYED
DEVICE_REVOKED
MEMBER_INACTIVE
MEMBER_SUSPENDED
MEMBERSHIP_NOT_ACTIVE
MEMBERSHIP_FROZEN
MEMBERSHIP_EXPIRED
PAYMENT_POLICY_BLOCK
NO_ENTITLEMENT
ENTITLEMENT_EXHAUSTED
ACCESS_OUTSIDE_HOURS
CAPACITY_REACHED
ALREADY_INSIDE
```

The public/client response remains generic enough not to expose sensitive
policy details. Authorized reception users receive the actionable projection.

### 8.4 Decision snapshot

Extend the access decision evidence without storing secrets:

- membership ID and status at decision time;
- entitlement definition and remaining quantity before/after, if consumed;
- effective policy version/ID;
- normalized reason code;
- member/device/location IDs;
- correlation/request ID;
- decision timestamp and engine version.

Do not store the raw QR credential, signing key material, or full private
provider data. A historical dispute should be explainable from the snapshot
without recomputing the decision using today's rules.

### 8.5 Scanner failure behavior

- Offline is deny-by-default; no synthetic grant path.
- Double-submit of the same QR cannot consume twice.
- Timeout followed by retry returns the prior idempotent outcome where safe.
- Device revocation takes effect immediately for new validations.
- Network and server failure messages are Turkish, brief, and actionable.
- Physical relay integration remains target until runtime hardware evidence
  exists; UI success alone is not proof that a door opened.

## 9. Reception Console

Admin Web and a reception console serve different cognitive and permission
needs. Build a task-focused reception workspace, even if it shares the same
React application and components.

### 9.1 Day-one actions

```text
Search member
Create member
Open unified member profile
Check current access eligibility
View today's access attempts/check-ins
Create/renew/freeze/unfreeze/cancel membership
Create/issue invoice
Record payment/refund when permitted
See outstanding balance and dunning state
Record note/consent
Resolve a denied entry with an authorized workflow
```

### 9.2 Unified member profile

One page should combine:

- identity and contact information;
- member status;
- current and historical memberships;
- entitlement balance and usage;
- invoices, payments, refunds, and outstanding balance;
- recent access decisions and check-ins;
- notes, tags, consents, and audit timeline;
- available actions derived from server permissions and state.

### 9.3 UX rules

- keyboard-first member search and predictable focus management;
- explicit loading, empty, error, success, and conflict states;
- disable double-submit and show in-progress state;
- display money from integer minor units;
- show reason and effective date before destructive lifecycle actions;
- require confirmation for refunds, cancellation, suspension, and overrides;
- never expose internal stack traces or raw policy details;
- meet WCAG 2.2 AA.

## 10. Member Self-Service

The backend `/me/*` surface already provides session, profile, member,
memberships, entitlements, and check-ins. The current Member Portal uses only
the self-QR issuance path.

### MVP member views

- current membership and expiry date;
- freeze/past-due/cancellation status where relevant;
- remaining entitlements;
- invoices, payments, and outstanding balance through a safe self endpoint;
- recent check-ins;
- QR access credential;
- profile/contact details and consent preferences;
- notification preferences.

Responsive web/PWA is sufficient for MVP. A separate native app is not a
closure requirement.

Security rules:

- resolve member identity from authenticated user binding, never a client
  supplied member ID;
- use cookie/session security and CSRF controls already established;
- omit staff-only notes and internal audit detail;
- provide generic, reassuring Turkish errors;
- do not expose or copy raw QR tokens outside the rendering flow.

## 11. Notifications

Keep the existing event-to-delivery architecture:

```text
Domain event
  -> notification orchestration
  -> tenant template and locale
  -> consent/preference check
  -> provider adapter
  -> NotificationDelivery ledger
  -> retry/backoff
  -> SENT or DEAD
```

### MVP triggers

```text
member.created.v1
membership.activated.v1
membership.expiring.v1
membership.expired.v1
membership.cancelled.v1
membership.past_due.v1
payment.failed.v1
payment.received.v1
payment.refunded.v1
access.denied.v1                 (policy-controlled)
account.created.v1
```

Only events with real producers and validated schemas belong in the canonical
registry. Adding constants without producers/consumers/tests is not progress.

### Preferences and consent

- transactional and marketing purposes remain separate;
- channel permission and legal basis are explicit;
- unsubscribe/preference changes are audited;
- WhatsApp/SMS/email providers receive the minimum data required;
- raw member PII is not logged;
- duplicate delivery is prevented with tenant-scoped dedupe keys.

## 12. Operational Dashboard

Do not build a large reporting suite before the daily operating view works.

### MVP KPIs

1. active members;
2. new members in selected period;
3. cancelled memberships;
4. memberships expiring soon;
5. past-due members and outstanding minor units;
6. today's allowed/denied check-ins;
7. current occupancy, only when check-out/occupancy semantics are reliable;
8. collected revenue for selected period.

Each KPI needs:

- a written definition and timezone boundary;
- tenant scope and authorization;
- server-side aggregation, pagination, and query index review;
- data freshness indication;
- drill-down to the source rows;
- empty/error/partial states;
- reconciliation against source tables.

Never label a member list count as “active members” unless the query actually
filters the agreed active definition.

## 13. Tenant Onboarding

Onboarding must be a resumable workflow, not a sequence of manual database
commands.

```text
Organization created
  -> tenant/gym created
  -> branch/location configured
  -> timezone, currency, working hours, and access policy configured
  -> published plans created
  -> owner/staff invited
  -> payment configuration verified
  -> scanner/device provisioned
  -> optional data import completed
  -> readiness checks passed
  -> READY
```

Requirements:

- store step status and validation errors;
- allow safe resume;
- make every step idempotent;
- enforce tenant context at every write;
- do not mark ready if required configuration is missing;
- emit audit and versioned events;
- provide a final checklist and test member/access flow.

Candidate `TenantBusinessSettings` fields include timezone, currency, working
hours, default grace policy, occupancy behavior, and access rules. Do not place
secrets or provider credentials in the settings row.

## 14. CSV Import and Migration

The first real customer often needs migration more than advanced reporting.

### MVP import types

- members;
- memberships;
- opening balances/invoices where legally and financially appropriate;
- staff/trainers.

### Workflow

```text
Upload
  -> virus/content/type/size validation
  -> parse to staging
  -> schema and business validation
  -> preview valid/invalid rows
  -> confirm
  -> chunked import job
  -> reconciliation summary
  -> downloadable error report
```

Requirements:

- tenant-keyed storage and short-lived download URLs;
- no direct insert from uploaded rows;
- deterministic external/source key for idempotency;
- dry-run before mutation;
- row-level Turkish error messages safe for customers;
- original upload retention policy;
- chunked writes and bounded list queries;
- resumable jobs without duplicating completed rows;
- imported finance records use integer minor units and explicit opening-balance
  semantics;
- rollback means compensating/archiving imported data, not destructive deletes
  across unrelated tenant records.

## 15. Support, Federation, and Job Operations

### 15.1 Support sessions

Existing superuser tenant entry is audited, but a sellable SaaS needs a bounded
support-session concept:

- support actor;
- target tenant and optional target user/member;
- required reason/ticket reference;
- approved scopes;
- started/expires/ended timestamps;
- read-only by default;
- visible audit banner and immutable log;
- immediate revoke.

Avoid uncontrolled “login as user”. If impersonation is ever necessary, it
must use a separate short-lived support session and must never reveal existing
session tokens or MFA secrets.

### 15.2 Operations console

Provide read visibility for:

- outbox pending/processing/failed/dead counts;
- notification queued/failed/dead counts;
- report/import job state;
- oldest pending age;
- last successful worker heartbeat;
- dependency readiness;
- correlation/request IDs for investigation.

Any retry/replay action is state-changing and requires permission, reason,
idempotency, and audit. Do not offer arbitrary payload editing.

## 16. Production Operations and Evidence

### 16.1 Observability

- `/live` proves the process is alive;
- `/ready` verifies required dependencies and returns 503 when unavailable;
- metrics reflect real state, not placeholders;
- structured logs include `requestId` and `tenantId` where applicable;
- alerts cover error rate, access failures, payment webhook failures, outbox
  oldest age/dead count, notification failures, DB saturation, and restore/backup
  freshness;
- traces cover the critical membership-payment-access path;
- runbooks link each alert to an operator action.

Define practical SLOs before alert thresholds. Avoid alerts that cannot produce
an action.

### 16.2 Backup and restore

The script is not proof of recoverability. A closure drill must:

1. create a backup from an approved non-production source or sanitized fixture;
2. restore into an isolated database with an explicit `_dr_drill` name;
3. run migrations/status checks;
4. verify tenant/member/finance/access row counts and selected invariants;
5. run a minimal API read against the restored database;
6. record duration, RPO/RTO observation, checksums, operator, date, and result;
7. clean up safely;
8. archive evidence without credentials or PII.

Test failure cleanup as well as success. The script must not drop an ambiguous
database target.

### 16.3 Browser E2E

Expand beyond login/branding smoke tests. Required flows:

- owner/reception login and role gating;
- create member -> membership -> invoice -> payment -> access grant;
- frozen/expired/past-due access denial;
- QR replay and double-submit;
- member self-service data isolation;
- payment/refund retry idempotency;
- scanner offline/timeout recovery;
- cross-tenant negative checks;
- notification failure -> retry -> terminal/dead visibility.

At least the money and access paths remain in the fast required gate. Broader
browser coverage can run after merge/nightly only after flakiness is removed.

## 17. Delivery Sequence

### Wave A — Decision and daily-operations closure (P0)

1. Document member/membership state meanings and API transition capabilities.
2. Add access decision taxonomy and policy snapshot.
3. Build unified member profile and dedicated reception workspace.
4. Cover denied access explanations and retry/double-submit behavior.
5. Add full HTTP/browser vertical slice for member-to-entry.

Exit: reception can resolve a member's lifecycle, balance, and access issue
without database or developer access.

### Wave B — Collections closure (P0)

1. ADR and migration for payment attempts and dunning policy/case.
2. Provider attempt normalization and idempotent retry orchestration.
3. Past-due/grace/access-policy integration.
4. Reception collection, refund, and override UX with audit.
5. Failed-payment notification triggers.

Exit: repeated provider failures and recovery are visible, deterministic, and
do not duplicate money or access effects.

### Wave C — Member and operational visibility (P0)

1. Complete member self-service using `/me/*` plus safe finance/preferences
   endpoints.
2. Add the eight defined operational KPIs and drill-downs.
3. Wire membership/payment/access notification events.
4. Add job/delivery failure visibility.

Exit: member and operator can see the same authoritative contract/payment
state through appropriately filtered projections.

### Wave D — Customer onboarding and migration (P0 before first external gym)

1. Resumable onboarding workflow and business settings.
2. Member/membership CSV validate-preview-confirm import.
3. Staff and opening-balance migration where required.
4. Reconciliation, error report, and retry behavior.

Exit: a new gym can be configured and migrated without manual SQL.

### Wave E — Production evidence (P0 launch gate)

1. Run the actual restore drill and archive evidence.
2. Expand Playwright/API failure-path coverage.
3. Verify alerts, runbooks, worker health, and readiness behavior.
4. Close KMS, distributed rate limiting, signed artifact URL, pentest/ASVS, and
   independent human approval items tracked by the current production board.
5. Require a fully green CI run at the exact release SHA.

Exit: all Section 18 gates pass with dated evidence.

### MVP+1

- class types, sessions, capacity, booking, waitlist, attendance, and no-show;
- PT packages, credits, appointments, trainer calendar, and attendance;
- CRM lead pipeline, segmentation, retention/churn workflows;
- advanced finance and operational reports.

If the first launch customer sells group classes or PT as a primary service,
move only the required minimal vertical slice into P0 and document the scope
change explicitly.

## 18. MVP Exit Gates

### Business gates

- [ ] A gym can onboard without manual database work.
- [ ] Existing members/memberships can be imported with preview and errors.
- [ ] Reception can complete the full member/membership/payment/access journey.
- [ ] Failed payment and dunning recovery work end to end.
- [ ] Access decisions are explainable from immutable evidence.
- [ ] Member self-service shows authoritative membership, entitlement, finance,
      check-in, and QR information.
- [ ] Operational KPI definitions reconcile to source data.

### Security and data gates

- [ ] Every new tenant table has `tenant_id`, index, RLS, and negative tests.
- [ ] Composite tenant-safe foreign keys protect related rows.
- [ ] Money remains integer minor units and backend-calculated.
- [ ] State-changing external operations are idempotent.
- [ ] Support access is scoped, expiring, reasoned, and audited.
- [ ] QR credentials, secrets, card data, and PII are not logged.
- [ ] User-facing errors are Turkish, brief, and actionable.

### Reliability gates

- [ ] Real PostgreSQL tests pass at the release SHA.
- [ ] Browser E2E covers happy and failure paths for money and access.
- [ ] Scanner timeout/offline/double-submit/replay behavior is verified.
- [ ] Outbox, notifications, and import jobs expose failed/dead state.
- [ ] Backup/restore drill passes and dated evidence is archived.
- [ ] Health/readiness/metrics/alerts are verified in the actual runtime.
- [ ] CI required checks are fully green.

### Governance gates

- [ ] Architecture report distinguishes implemented, partial, and target.
- [ ] Required ADRs and migration reviews are complete.
- [ ] ASVS/pentest findings are closed or formally accepted.
- [ ] Independent human review approves the release.
- [ ] `PROGRESS_CHECKLIST.md`, remaining-work board, and release SHA agree.

## 19. Definition of Done for Every Slice

- test specification or pseudocode exists before implementation;
- existing services/components were searched before adding new abstractions;
- API inputs use Pydantic validation;
- authorization and resource scope are tested;
- database constraints back important concurrency invariants;
- services flush and the application owns the transaction boundary;
- mutation and outbox event commit atomically;
- event payloads use registered, versioned schemas;
- list endpoints are bounded and indexed;
- UI has loading, empty, error, success, permission, and conflict states;
- keyboard, focus, semantics, and contrast meet WCAG 2.2 AA;
- timeout, retry, duplicate, and out-of-order behavior is tested;
- browser console is clean in the real workflow;
- actual runtime evidence exists before claiming completion.

## 20. Immediate Next Action

Create one scoped ADR and test specification for **Access Decision Evidence and
Tenant Access Policy**. It should define:

1. the stable reason-code taxonomy;
2. the decision snapshot fields;
3. membership, dunning, hours, capacity, and duplicate-inside evaluation order;
4. public/scanner/reception response projections;
5. idempotency and replay behavior;
6. tenant/RLS/composite-FK constraints;
7. versioned event contracts;
8. migration and backward-compatibility plan.

This is the highest-leverage first slice because it connects the existing
membership, finance, entitlement, device, QR, check-in, audit, and reception
capabilities without reopening the platform foundation.

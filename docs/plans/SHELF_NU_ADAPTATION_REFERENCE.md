# Shelf.nu Reference and Fitness Network OS Adaptation Plan

**Status:** Reference / target design; not an implementation claim
**Reviewed:** 2026-08-11
**Fitness Network OS branch:** `feat/phase27-ui-production-closure`
**Fitness Network OS baseline:** `b1a5f7b`
**Upstream repository:** <https://github.com/Shelf-nu/shelf.nu>
**Upstream snapshot reviewed:** [`ac8fe408eef0663af02b02c322dfc3456f896dcc`](https://github.com/Shelf-nu/shelf.nu/tree/ac8fe408eef0663af02b02c322dfc3456f896dcc)
**Upstream license:** [AGPL-3.0](https://github.com/Shelf-nu/shelf.nu/blob/ac8fe408eef0663af02b02c322dfc3456f896dcc/LICENSE)

## 1. Decision

Shelf.nu is a strong product and domain reference for a future **Facility &
Equipment Operations** bounded context in Fitness Network OS.

It is **not** a reference for replacing the existing authentication, tenant
isolation, PostgreSQL RLS, membership, payment, entitlement, or access-control
security architecture. Those areas remain governed by this repository's
`MASTER_SPEC.md`, `PRODUCTION_READINESS.md`, and ADRs.

The recommended use is:

1. Study Shelf.nu's domain decomposition and workflows.
2. Re-express useful concepts in Fitness Network OS terminology and security
   constraints.
3. Implement original code against our Python/FastAPI/SQLAlchemy architecture.
4. Keep member access credentials and equipment identity QR codes in separate
   bounded contexts.
5. Deliver the capability incrementally, starting with locations, assets,
   identity labels, and immutable history.

## 2. Why Shelf.nu Is Relevant

Shelf.nu treats a physical asset as more than an inventory row. Its public
repository includes asset identity, hierarchical locations, QR and barcode
labels, scan records, custody, reservations, kits, custom fields, reminders,
quantity tracking, audit workflows, and search-oriented indexes.

The upstream README describes the same operational surface at product level:

- QR asset tags and batch printing;
- bookings and reservations;
- custody tracking;
- hierarchical locations;
- custom fields, categories, and tags;
- kits;
- CSV import/export;
- reminders and activity history;
- multi-workspace access;
- scanner workflows and bulk actions.

These capabilities map naturally to a gym operating system that must manage
equipment, rooms, zones, consumables, temporary loans, faults, inspections, and
maintenance in addition to members and entry access.

## 3. Source Map

Use the pinned links below when revisiting the reference. `main` can change;
the commit links preserve the evidence used by this document.

| Concern | Shelf.nu reference |
|---|---|
| Product scope and repository layout | [README](https://github.com/Shelf-nu/shelf.nu/blob/ac8fe408eef0663af02b02c322dfc3456f896dcc/README.md) |
| Core data model | [Prisma schema](https://github.com/Shelf-nu/shelf.nu/blob/ac8fe408eef0663af02b02c322dfc3456f896dcc/packages/database/prisma/schema.prisma) |
| Asset workflows | [`app/modules/asset`](https://github.com/Shelf-nu/shelf.nu/tree/ac8fe408eef0663af02b02c322dfc3456f896dcc/apps/webapp/app/modules/asset) |
| Booking workflows | [`app/modules/booking`](https://github.com/Shelf-nu/shelf.nu/tree/ac8fe408eef0663af02b02c322dfc3456f896dcc/apps/webapp/app/modules/booking) |
| Kit workflows | [`app/modules/kit`](https://github.com/Shelf-nu/shelf.nu/tree/ac8fe408eef0663af02b02c322dfc3456f896dcc/apps/webapp/app/modules/kit) |
| Companion scanner | [`apps/companion`](https://github.com/Shelf-nu/shelf.nu/tree/ac8fe408eef0663af02b02c322dfc3456f896dcc/apps/companion) |
| Booking conflict notes | [Booking conflict queries](https://github.com/Shelf-nu/shelf.nu/blob/ac8fe408eef0663af02b02c322dfc3456f896dcc/apps/docs/booking-conflict-queries.md) |
| License | [AGPL-3.0](https://github.com/Shelf-nu/shelf.nu/blob/ac8fe408eef0663af02b02c322dfc3456f896dcc/LICENSE) |

The most important upstream schema concepts are `Asset`, `AssetModel`,
`Location`, `Qr`, `Barcode`, `Scan`, `Custody`, `Booking`, `BookingAsset`,
`Kit`, `AssetKit`, `AssetLocation`, `CustomField`, `AssetCustomFieldValue`,
`ConsumptionLog`, and `AssetReminder`.

## 4. Current Fitness Network OS Reality

At the reviewed baseline, the repository already has:

- `Organization -> Tenant -> Location`, where a gym is a tenant and a branch is
  a location;
- tenant-scoped SQLAlchemy models through `TenantMixin`;
- PostgreSQL RLS and transaction-scoped tenant context;
- RBAC, scopes, and authorization services;
- member, membership, entitlement, finance, staff, and access domains;
- device identity and device-session bootstrap;
- short-lived signed member access QR credentials with replay protection;
- access attempts and check-ins;
- versioned domain-event contracts and a transactional outbox.

The repository does **not** yet contain the proposed equipment/facility domain.
The existing `Location` model is a branch-level tenant resource with name,
timezone, and address. It is not yet a nested facility hierarchy. Therefore,
everything in Sections 7–15 is a target plan unless a future implementation
changes its status explicitly.

## 5. Adopt, Adapt, or Reject

| Shelf.nu concept | Decision | Fitness Network OS interpretation |
|---|---|---|
| Asset aggregate | Adopt | `EquipmentAsset` for serialized gym equipment and operational devices represented as inventory |
| Asset model/type | Adopt | Shared manufacturer/model metadata without losing per-item identity |
| Hierarchical location | Adapt | Preserve branch `Location`; add nested `FacilityZone` beneath it |
| Static QR identity | Adopt | `AssetIdentityQr`; long-lived identifier, never a door credential |
| Barcode identity | Adopt later | Useful for vendor labels and bulk inventory workflows |
| Scan history | Adapt | Tenant-scoped, privacy-minimized, retention-controlled `AssetScanEvent` |
| Custody | Adopt | Temporary responsibility/loan to staff or member with due/return condition |
| Booking | Adapt | Reserve rooms, specialist equipment, courts, reformers, or recovery devices |
| Custom fields | Adopt later | Tenant-defined metadata with strict type and scope validation |
| Quantity-tracked assets | Adopt later | Towels, cleaning supplies, disposable stock, rental accessories |
| Kits | Adopt later | PT kit, maintenance kit, event kit, recovery kit |
| Reminders | Adapt | Maintenance schedules and inspection due dates, not only generic reminders |
| Audit/activity history | Adopt | Append-only business timeline plus existing security audit mechanisms |
| Shelf auth/roles | Reject as replacement | Keep Fitness Network OS sessions, RBAC, scopes, tenant context, and RLS |
| Shelf multi-workspace model | Reject as tenancy replacement | Gym remains `Tenant`; database hard fences remain mandatory |
| Direct code reuse | Reject by default | Upstream is AGPL-3.0; use concepts unless legal review approves code reuse |

## 6. Critical Domain Boundary: Two QR Systems

The member-entry QR and the equipment QR solve different problems and must not
share tokens, tables, verification services, or authorization rules.

### 6.1 Member access credential

```text
AccessCredentialQr
  short-lived (default 60 seconds)
  HMAC signed
  tenant/member/audience claims
  JTI replay protection
  validated by an authenticated access device
  may authorize a physical entry decision
```

This is a security credential. Existing controls remain unchanged.

### 6.2 Asset identity label

```text
AssetIdentityQr
  long-lived opaque public identifier
  resolves to tenant-scoped asset information
  may open fault-report, inspection, or inventory workflows
  never grants door access
  can be disabled, replaced, or re-linked
```

An asset identity QR must not contain a reusable member or device secret. A
public scan route should reveal only an allowlisted public projection and must
not expose tenant-private maintenance notes, member custody, serial numbers, or
internal identifiers.

### 6.3 Device versus asset

`AccessDevice` remains a machine identity in the access-control domain. A
turnstile, scanner, or tablet may also need an inventory record. Model that as
an optional cross-reference instead of merging the aggregates:

```text
AccessDevice.inventory_asset_id -> EquipmentAsset.id  (optional 1:1)
```

The relationship does not allow the asset domain to issue device sessions or
make access decisions.

## 7. Proposed Bounded Context

Recommended name: **Facility & Asset Operations**.

```text
Organization
  -> Tenant (gym)
      -> Location (branch)
          -> FacilityZone (floor / studio / room / operational zone)
              -> EquipmentAsset
                  -> AssetIdentityQr
                  -> AssetLocationHistory
                  -> AssetCustody
                  -> AssetEvent
                  -> FaultReport
                  -> MaintenanceSchedule
                  -> MaintenanceWorkOrder
                  -> Inspection
                  -> AssetCustomFieldValue

EquipmentAsset
  -> ResourceBooking
  -> AssetKitItem
  -> InventoryMovement (quantity-tracked assets only)
```

### 7.1 Ownership rules

- Every new business table is tenant-owned unless an ADR proves otherwise.
- Every tenant-owned row includes `tenant_id`, an index beginning with
  `tenant_id`, RLS policy coverage, and cross-tenant negative tests.
- Foreign keys between tenant-owned tables use composite tenant-safe
  references where appropriate: `(tenant_id, id)`.
- `location_id`, `zone_id`, `member_id`, `staff_id`, and related IDs must refer
  to rows in the same tenant.
- Organization-wide reads must use the established federation pattern; they
  must not weaken tenant RLS.

## 8. Proposed Domain Model

This is a conceptual model. Exact columns require an ADR and migration review.

### 8.1 `facility_zones`

Purpose: nested physical hierarchy below the existing branch-level `Location`.

Candidate fields:

- `id`, `tenant_id`, `location_id`;
- `parent_zone_id` nullable;
- `name`, `code`, `zone_type`;
- `is_bookable`, `is_active`;
- timestamps and optimistic version.

Invariants:

- parent and child belong to the same tenant and branch;
- no cycles;
- maximum supported depth is explicit;
- sibling code uniqueness is tenant/branch/parent scoped;
- inactive zones cannot receive new assets or reservations.

Example:

```text
Istanbul Levent Branch
  -> Floor 1
      -> Cardio Zone
      -> Free Weight Zone
  -> Floor 2
      -> Pilates Studio
      -> PT Room 1
```

### 8.2 `equipment_assets`

Candidate fields:

- identity: `id`, `tenant_id`, `asset_code`, `title`;
- classification: `category_id`, `asset_model_id`, `tracking_type`;
- lifecycle: `status`, `commissioned_at`, `retired_at`;
- placement: current branch/zone projection or relation;
- inventory: `quantity`, `minimum_quantity`, `unit_of_measure` where applicable;
- commercial metadata: `purchase_date`, `warranty_expires_at`;
- operational metadata: `last_inspected_at`, `next_maintenance_at`;
- timestamps and optimistic version.

Suggested tracking types:

- `SERIALIZED`: one row represents one physical item;
- `QUANTITY_TRACKED`: one row represents fungible units.

Suggested lifecycle:

```text
DRAFT -> ACTIVE -> OUT_OF_SERVICE -> ACTIVE
                  -> RETIRED
ACTIVE -> LOST
ACTIVE -> RETIRED
```

Do not derive maintenance state solely from a generic asset status. Keep work
orders and inspections as explicit records and project the current state.

### 8.3 `asset_identity_qrs`

Candidate fields:

- `id`, `tenant_id`, `asset_id`;
- random `public_id` with tenant-scoped uniqueness;
- `status`: `UNASSIGNED`, `ACTIVE`, `DISABLED`, `REPLACED`;
- `print_batch_id` nullable;
- `activated_at`, `disabled_at`, `replaced_by_id`;
- timestamps.

Use opaque random identifiers. Never encode raw tenant IDs, asset serial
numbers, member IDs, or authorization claims in the printed value.

### 8.4 `asset_location_history`

Record every placement transition:

- source and destination branch/zone;
- reason;
- actor;
- effective timestamp;
- correlation/request ID.

The current location may be stored as a projection for fast reads, but history
is append-only. Moving an asset is one transaction: validate tenant-safe
references, update the projection, append history, and enqueue the event.

### 8.5 `asset_custodies`

Candidate fields:

- `asset_id` and quantity;
- exactly one custodian type and ID (`member_id` or `staff_id` initially);
- `assigned_at`, `due_at`, `returned_at`;
- `condition_out`, `condition_in`;
- `status`, actor, and notes.

Invariants:

- a serialized asset has at most one active custody;
- allocated quantity never exceeds available quantity;
- a return is idempotent;
- custody cannot cross tenants;
- member-visible responses exclude internal staff notes.

### 8.6 Maintenance and faults

Use separate aggregates:

- `fault_reports`: observed problem and evidence;
- `maintenance_schedules`: recurrence or usage-based rule;
- `maintenance_work_orders`: owned unit of work and lifecycle;
- `inspections`: checklist outcome and evidence.

Suggested fault-to-recovery flow:

```text
FAULT_REPORTED
  -> TRIAGED
  -> OUT_OF_SERVICE
  -> WORK_ORDER_CREATED
  -> TECHNICIAN_ASSIGNED
  -> REPAIR_COMPLETED
  -> INSPECTION_PASSED
  -> ACTIVE
```

An inspection failure must not silently reactivate an asset.

### 8.7 Resource bookings

Bookings should be a later slice because conflict handling is a concurrency
problem, not only a calendar UI.

Candidate resources:

- equipment asset;
- facility zone/room;
- court or studio;
- asset kit.

Required rules:

- tenant-local time is converted and persisted safely;
- overlap checks are protected against concurrent writes at database level;
- cancelled/expired bookings do not block capacity;
- quantity bookings cannot exceed capacity;
- check-out/check-in mutations are idempotent;
- member eligibility is resolved server-side from membership/entitlements.

### 8.8 Custom fields

Custom fields are useful but should not become an ungoverned JSON escape hatch.

- definitions are tenant-scoped and typed;
- values are schema-validated at the API boundary;
- searchable fields have an intentional indexing strategy;
- sensitive fields receive data classification and retention metadata;
- reserved system field names cannot be shadowed;
- field deletion has explicit archival behavior.

## 9. Transaction and Event Model

Every state-changing operation follows existing Fitness Network OS rules:

```text
validate input and authorization
  -> lock/compare state
  -> mutate domain rows
  -> append immutable history
  -> enqueue versioned outbox event
  -> commit once
```

Candidate event contracts:

```text
facility.zone.created.v1
asset.created.v1
asset.status.changed.v1
asset.location.changed.v1
asset.custody.assigned.v1
asset.custody.returned.v1
asset.fault.reported.v1
asset.maintenance.due.v1
asset.maintenance.started.v1
asset.maintenance.completed.v1
asset.inspection.completed.v1
asset.retired.v1
asset.inventory.adjusted.v1
resource.booking.created.v1
resource.booking.cancelled.v1
```

Adding these strings to `backend/app/core/event_types.py` is not sufficient.
Each contract needs a documented payload, schema validation, producer tests,
idempotent consumer behavior, and backward-compatibility rules.

## 10. Authorization Surface

Candidate permissions:

```text
facility:read
facility:write
assets:read
assets:write
assets:custody
assets:maintenance
assets:audit
asset_qr:manage
resource_bookings:read
resource_bookings:write
inventory:adjust
```

Do not map upstream Shelf roles directly. Extend the existing permission
registry and assign permissions to Fitness Network OS roles deliberately.

Minimum policy expectations:

- members can view only explicitly member-visible resources;
- members can report a fault without seeing internal maintenance history;
- trainers see assets/zones within their authorized scope;
- technicians may update work orders without receiving finance/member access;
- federation operators use explicit organization scope and tenant entry;
- public QR scans never receive an authenticated internal asset projection.

## 11. Privacy, Security, and Retention

- Scan telemetry is personal data when combined with user/device/location
  context. Collect only what the workflow needs.
- Do not store GPS or raw user-agent data by default merely because the
  reference implementation can.
- Public asset QR endpoints require rate limiting and abuse monitoring.
- Uploaded fault/inspection media requires content-type validation, malware
  scanning, tenant-keyed object paths, and short-lived access URLs.
- Serial numbers, purchase data, technician notes, and custody identities are
  private projections.
- Asset history needs a retention policy; security audit evidence and ordinary
  operational activity may have different retention periods.
- All logs use structured logging with `requestId` and `tenantId`; secrets,
  raw QR contents, PII, and uploaded content are not logged.

## 12. Delivery Roadmap

### P0 — Foundation: branch/zone, serialized asset, identity, history

Deliverables:

1. ADR for the Facility & Asset Operations bounded context.
2. `FacilityZone`, `EquipmentAsset`, `AssetIdentityQr`, and append-only
   `AssetEvent`/location history.
3. Tenant-safe migrations, RLS, indexes, and permissions.
4. Admin list/detail/create/update flows with loading, empty, and error states.
5. Client-side QR label generation and public/private scan projections.
6. Fault report creation from an asset QR.
7. Transactional outbox events for asset creation, movement, status, and fault.
8. Cross-tenant, duplicate-scan, disabled-label, and retry tests.

Exit criteria:

- a staff user can create an asset, place it in a nested zone, print a label,
  scan it, move it, and inspect its history;
- a public/member scan cannot access another tenant or private fields;
- disabling/replacing a label invalidates the old resolution path;
- actual browser and real PostgreSQL verification pass.

### P1 — Custody, maintenance, inspection

Deliverables:

1. Staff/member custody with quantity and return condition.
2. Fault triage and maintenance work orders.
3. Scheduled and usage-triggered maintenance.
4. Inspection templates/results and explicit reactivation gate.
5. Notifications through domain events, not direct cross-domain calls.
6. Operational dashboards for due, overdue, and out-of-service assets.

Exit criteria:

- double assignment and over-allocation fail atomically;
- duplicate return/work-order requests are idempotent;
- out-of-order events do not reactivate unsafe equipment;
- tenant and permission negative tests pass.

### P2 — Booking, quantity inventory, kits, custom fields, analytics

Deliverables:

1. Conflict-safe resource booking.
2. Quantity-tracked inventory and immutable movements.
3. Kits and inherited custody/location behavior.
4. Typed custom fields.
5. CSV import/export with validation and dry-run reporting.
6. Inventory audits, saved filters, and operational analytics.

Exit criteria:

- concurrent booking and inventory races are covered by database invariants;
- import is idempotent and tenant-safe;
- kit operations preserve item history;
- analytics derive from trusted operational records, not mutable counters alone.

## 13. Explicit Non-Goals

- Replacing the existing user session or device-session design.
- Replacing RBAC, scopes, or PostgreSQL RLS with Shelf.nu workspace rules.
- Reusing the member access QR as an equipment label.
- Treating scanners/turnstiles as ordinary assets for authentication purposes.
- Copying the Shelf.nu schema or source into this repository.
- Delivering all Shelf.nu features in one phase.
- Introducing a new service, broker, or database only for this domain.

## 14. AGPL-3.0 Boundary

Shelf.nu is licensed under AGPL-3.0. This plan is a clean-room conceptual
reference, not approval to copy code, schema text, UI code, tests, or other
copyrightable implementation material.

Before any direct reuse or adaptation of upstream code:

1. obtain legal/license review;
2. record the decision and obligations;
3. preserve required notices and source-availability obligations;
4. verify compatibility with Fitness Network OS distribution and hosting.

Default engineering rule: reuse the **idea and domain lesson**, then write an
original implementation that conforms to this repository's architecture.

## 15. Implementation Checklist for Each Slice

- [ ] Pseudocode or test specification written before implementation.
- [ ] Existing models/services searched before adding a new abstraction.
- [ ] ADR accepted for architectural changes.
- [ ] Tenant ownership and composite foreign keys defined.
- [ ] Migration written manually and reviewed for rollback/data safety.
- [ ] RLS enabled and verified dynamically on real PostgreSQL.
- [ ] RBAC permission and scope behavior defined.
- [ ] API inputs validated at the boundary.
- [ ] List queries paginated and indexes matched to query shapes.
- [ ] State-changing requests idempotent where retries can duplicate effects.
- [ ] Outbox event and payload contract registered and tested.
- [ ] Loading, empty, error, and permission-denied UI states implemented.
- [ ] Turkish user-facing text is brief and actionable.
- [ ] Accessibility checked to WCAG 2.2 AA target.
- [ ] Cross-tenant and failure-mode tests pass.
- [ ] Browser console and real API/database runtime verified.

## 16. Recommended First Action

Start with a single ADR covering only:

```text
Location (existing branch)
  -> FacilityZone (new nested hierarchy)
      -> EquipmentAsset (serialized only)
          -> AssetIdentityQr
          -> AssetLocationHistory
          -> FaultReport
```

Defer custody, bookings, quantities, kits, and custom fields until this slice is
running end to end. This preserves a bounded delivery path while leaving clear
extension points for the later Shelf.nu-inspired capabilities.

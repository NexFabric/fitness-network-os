# ADR-031 — Federation-Scope Reads Without Weakening RLS

- **Status:** Accepted
- **Date:** 2026-08-11
- **Supersedes:** none
- **Related:** ADR-013 Hybrid Tenant Isolation, ADR-017 Authorization Abstraction
- **Driver:** Phase 27 — the SuperAdmin/Federation portal needs cross-tenant reads, and no cross-tenant HTTP surface exists yet.

## Context

The SuperAdmin portal (`/superadmin`) is specified to show a tenant directory,
per-tenant KPIs and federation-level aggregates. Today it shows hardcoded
numbers because the backend has no endpoint that can produce them.

The obstacle is deliberate. Tenant isolation is enforced by PostgreSQL RLS
(`backend/app/db/rls.py`): every tenant-owned table carries

```sql
USING (tenant_id = nullif(current_setting('app.current_tenant_id', true), '')::uuid)
```

plus `FORCE ROW LEVEL SECURITY`, so even the table owner cannot bypass it. The
GUC holds exactly one tenant, set transaction-scoped via `SET LOCAL`
(`backend/app/api/deps.py:87`) and re-armed after each commit by the
`after_begin` listener (`backend/app/db/session.py:20-27`). Unset context yields
`NULL` and therefore zero rows — fail-closed.

Consequence: **a single SQL statement can never see two tenants.** Roughly 57
tables are enrolled across 15 migrations.

Two facts shape the decision:

1. `tenants` and `organizations` have **no RLS** (verified against the running
   database: `relrowsecurity = false`). The tenant *directory* was never behind
   the tenant barrier.
2. `is_superuser` today merely lets a caller assert any `X-Tenant-ID`
   (`deps.py:85-88`) — a per-request impersonation flag, silently and without an
   audit trail. It is not a federation capability.

## Decision

Federation-scope reads are served **without changing any existing RLS policy and
without any RLS-bypassing database role.** Three separate paths, by data shape:

### 1. Directory data — read directly

`tenants` and `organizations` carry no tenant barrier. `GET /admin/tenants` and
`GET /admin/tenants/{id}` read them directly, gated only by RBAC
(`PLATFORM_SUPER_ADMIN`, `FEDERATION_*`). No RLS interaction at all.

### 2. Per-tenant aggregates — iterate, one tenant at a time

Counts and sums that live in RLS-protected tables (members, memberships,
revenue) are computed by **looping over an explicitly paged tenant list**,
issuing `SET LOCAL app.current_tenant_id` per tenant, and accumulating in
Python.

The isolation invariant is untouched: every statement still sees exactly one
tenant. What changes is only how many times we set the GUC within one request.

Constraints that make this safe rather than a loophole:

- The tenant list **must be paged** (`limit` capped server-side, default 50).
  No unbounded "all tenants" scan.
- The loop is **read-only**. Writes across tenants in one request are forbidden;
  a cross-tenant mutation must be modelled as per-tenant events via the outbox.
- The GUC is reset to `''` after the loop so no tenant context leaks into
  later work on the same connection.

Cost is N round-trips for N tenants on a page. At the scale this platform
targets (tens to low hundreds of clubs, one page at a time) this is the right
trade: correctness and an unmodified security boundary in exchange for latency
that is bounded and visible.

### 3. Heavy analytics — deferred to a rollup table

Time-series and high-cardinality analytics do **not** use path 2. When they are
needed, a platform-owned rollup table (e.g. `tenant_metrics_daily`) is written
by a per-tenant background job — each job run stays inside one tenant context —
and read by the federation surface without RLS, because it holds only
pre-aggregated, non-personal counters. **Out of scope for Phase 27**; recorded
here so path 2 is not later stretched to cover it.

### Access control and audit

- `audit_events` currently has **no RLS** and carries `tenant_id`. Because
  `GET /admin/audit` gives it an HTTP surface for the first time, it gets an RLS
  policy in the same change. The federation reader reaches it through path 2,
  not by exemption.
- Superuser tenant impersonation (`deps.py:85-88`) becomes **audited**: every
  request where a superuser asserts a tenant it holds no `UserRole` for writes
  an `AuditEvent`. Silent impersonation is the current behaviour and is treated
  as a defect closed by this ADR.

## Rejected alternatives

**Widen the RLS policy with a federation clause.** Adding
`OR tenant_id = ANY(current_setting('app.federation_tenant_ids'))` to every
policy means rewriting ~57 policies and moving the isolation guarantee from "one
tenant, structurally" to "one tenant, unless a second GUC says otherwise". A
single missed policy or an unreset GUC becomes a cross-tenant leak. The blast
radius of a mistake is the entire platform.

**A `BYPASSRLS` database role for federation queries.** Deletes the guarantee
rather than scoping it, and defeats `FORCE ROW LEVEL SECURITY` — the very thing
that stops the app's own owner role from reading everything. Any SQL bug or
injection under that role reads all tenants.

**Reuse `is_superuser` + `X-Tenant-ID` as the federation mechanism.** This is
what exists today. It cannot aggregate (it addresses one tenant per request),
it grants full write access where only reads are needed, and it is
indistinguishable in the logs from normal tenant traffic.

**A separate read-replica/warehouse without RLS.** Reasonable at a much larger
scale; here it adds an unsynchronised copy of every tenant's data, a second
place to get isolation wrong, and infrastructure this project explicitly defers
(AGENTS.md: no premature microservices/Kafka/K8s).

## Consequences

**Positive**

- The RLS boundary and all existing policies stay exactly as they are; no
  migration touches an existing policy.
- Federation reads are structurally read-only and structurally paged.
- Superuser tenant access stops being silent.
- `audit_events` gains the isolation it should have had.

**Negative / accepted**

- Federation endpoints cost N queries per page. Latency grows with page size,
  not with total tenant count. Mitigated by the server-side cap and, later, by
  path 3.
- Two code paths exist for reading tenant data (single-tenant handlers vs the
  federation loop). The loop lives in one service so the pattern is not copied
  around.

## Compliance

- Any new tenant-owned table still requires `tenant_id` + index + RLS policy +
  tenancy tests (AGENTS.md). This ADR grants no exemption.
- Tests must cover: a `FEDERATION_ANALYST` cannot read another organization's
  tenants; the GUC is empty after the aggregate loop; the loop refuses an
  unbounded limit.

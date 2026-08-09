# Phase 9: Entitlement & Resolution Engine (Wave 2 - Part 2)

## Goal
Phase 8 established the strict invariant-based `Membership` models, JSONB terms, and the lifecycle state machine. 
Phase 9 makes this actionable by:
1. **Resolution Engine:** Automatically applying time-based state transitions (e.g., SCHEDULED -> ACTIVE, processing future renewals, auto-expiring).
2. **Entitlement Engine:** Translating active memberships and their JSON terms into concrete "Yes/No" or "Count-based" access rights that gateways and clients can consume.

---

## Task 1: Resolution Engine (Lifecycle Worker)
**Owner:** Subagent 1 (Lifecycle Worker)
**Responsibility:** A scheduled job (or robust service method designed for cron) that handles temporal transitions.

### Requirements:
1. **Activate Scheduled Memberships:** Find memberships in `SCHEDULED` state where `start_date <= NOW()`. Transition them to `ACTIVE` using `activate_scheduled_membership`.
2. **Process Renewals:** Find `MembershipRenewal` records where `renewal_date <= NOW()` and `status = 'PENDING'`. 
   - Close the current `MembershipPeriod`.
   - Update `Membership.plan_version_id`, `end_date`, `terms_snapshot`, `price_snapshot` with the new plan details.
   - Open a new `MembershipPeriod`.
   - Mark the renewal as `APPLIED`.
3. **Process Expirations:** Find `ACTIVE` memberships where `end_date < NOW()`. Transition to `EXPIRED` (close the period, log the status change).
4. **Resilience:** Each transition MUST run in its own transaction (or atomic block). If one member's renewal fails, the worker must continue processing others.

---

## Task 2: Entitlement Engine & Access APIs
**Owner:** Subagent 2 (Entitlement Engine)
**Responsibility:** Providing the logic and APIs to answer "Can Member X do Y right now?"

### Requirements:
1. **Entitlement Service (`app/services/entitlement.py`):**
   - Read the active `Membership` and its `terms_snapshot` (JSONB).
   - Evaluate specific entitlements (e.g., `access_gym`, `book_class`, `bring_guest`).
2. **Offline TTL / Caching Strategy:**
   - Define a read-optimized projection or caching layer for rapid gateway access (e.g., returning `{ "status": "ACTIVE", "ttl": 3600, "entitlements": {...} }`).
3. **API Endpoint (`POST /api/v1/members/{member_id}/entitlements/consume`):**
   - Receives an action (e.g., `"gym_access"`).
   - Checks the service. 
   - Returns HTTP 200 with success status, or HTTP 403 with `last_known_state` and denial reason.

---

## Execution Plan
We will dispatch two parallel agents to branch off `main` (which will include the PR #13 merge) and implement these features simultaneously. 

Once both are complete, we will run the full CI suite and merge them via PR #14.

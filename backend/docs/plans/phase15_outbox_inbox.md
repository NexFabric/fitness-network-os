# Phase 15 — Outbox / Inbox / Job Engine

**Status:** 🟢 LOCKED (PR #22 merge `67b8214`; docs PR #23)  
**Depends on:** Phase 14 LOCKED  
**Migrations:** `l5e6f7a8b9c0` (expand) + `m6f7a8b9c0d1` (permissions) — **current alembic head**

## Design

```text
Domain write TX
  → OutboxService.enqueue (same TX, flush-only)
  → worker claim SKIP LOCKED → publisher → PUBLISHED | FAILED/DEAD

External webhook
  → receive_inbox UNIQUE(tenant_id, event_id)
  → process_pending_inbox handlers → PROCESSED
```

## Schema expand

- outbox: attempt_count, available_at, processed_at, aggregate_*, dedupe_key
- inbox: attempt_count, processed_at; UNIQUE(tenant_id, event_id)

## Deferred

- Real bus (Kafka/SQS) adapters
- Full job scheduler / cron envelope
- CloudEvents envelope normalization

## Exit

- Real PG tests: publish, dedupe, inbox exactly-once, retry
- CI green

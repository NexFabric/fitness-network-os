# Phase 15 — Outbox / Inbox / Job Engine

**Status:** IN PROGRESS (`feat/phase15-outbox-inbox-engine`)  
**Depends on:** Phase 14 LOCKED

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

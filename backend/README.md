# GymClubNex Backend API & Engine

> Next-Generation Multi-Tenant Fitness & Athletic Operations Engine powered by FastAPI, PostgreSQL (Row-Level Security), and Transactional Outbox Workers.

## Overview

GymClubNex Backend provides a robust, compliant, multi-tenant operations layer for gyms, fitness clubs, franchises, and national sports federations:
- **Tenancy Isolation:** PostgreSQL Row-Level Security (RLS) with transaction-scoped `set_config('app.current_tenant_id', :tid, true)`.
- **Dynamic Access Control:** Signed short-lived QR codes with replay protection, AES-256-GCM / HMAC-SHA256, and rotation.
- **Group Class & PT Booking Engine:** Pessimistic locking (`SELECT ... FOR UPDATE`), GiST overlap prevention constraints, and monotonic FIFO waitlist queue with automatic promotion.
- **Financial Architecture:** Integer minor currency storage (`amount_minor`), idempotency protection, and atomic invoices.
- **Transactional Outbox Engine:** Reliable asynchronous domain event processing with `SKIP LOCKED` and lease recovery.

---

## Quick Start

### 1. Environment & Dependencies

Requirements: Python 3.12+, `uv`, PostgreSQL 16+

```bash
cd backend
uv sync
```

### 2. Database Migrations

```bash
uv run alembic upgrade head
```

### 3. Running the Server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Static Invariant & Compliance Checks

Run the required repository gates:

```bash
uv run python scripts/check_tenancy.py --static
uv run python scripts/check_permissions.py
uv run python scripts/check_no_money_floats.py
uv run python scripts/check_release_truth.py
uv run ruff check .
```

---

## License & Security

Internal & proprietary to GymClubNex. For vulnerabilities, contact `hello@gymclubnex.com`.

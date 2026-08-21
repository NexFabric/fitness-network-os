# GymClubNex — Fitness Network OS

> Next-Generation Multi-Tenant Athletic Operations Platform & Federation Infrastructure.

[![Next.js](https://img.shields.io/badge/Next.js-16_App_Router-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_RLS-336791?logo=postgresql)](https://www.postgresql.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue?logo=typescript)](https://www.typescriptlang.org/)
[![WCAG](https://img.shields.io/badge/WCAG-2.2_AA_Compliant-success)](#)

---

## 🏛️ Architecture & Applications

```
GymClubNex/
├── backend/                # FastAPI 0.115 backend engine (PostgreSQL RLS, Outbox, Booking, QR Crypto)
├── frontend/
│   ├── admin-web/          # React 18 + Vite Multi-Portal (Reception, Members, Classes, Finance, HQ)
│   ├── scanner-pwa/        # React 18 + Vite PWA offline-resilient turnstile gate scanner
│   ├── public-site/        # Next.js 16 (Turbopack) marketing landing & legal portals
│   └── shared/             # Shared athletic engine calculations and TypeScript utilities
└── docs/                   # Hand-off guides, architecture decision records (ADRs), and campaign logs
```

---

## 🚀 Key Architectural Pillars

1. **Multi-Tenant Isolation:** PostgreSQL Row-Level Security (RLS) with transaction-scoped context (`app.current_tenant_id`).
2. **Access Control & Dynamic QR:** Encrypted, signed, short-lived QR codes with replay protection, clock-drift tolerance, and key rotation.
3. **High-Contention Booking Engine:** Pessimistic row locking (`SELECT FOR UPDATE`), exclusion constraints (`ex_pt_appointments_no_overlap`), and monotonic FIFO waitlist queues.
4. **Financial Safety:** Pure integer minor currency storage (`amount_minor`), idempotency locking, and zero Float math.
5. **Mobile & Touch Ergonomics:** 100dvh dynamic viewports, Apple HIG 44px touch targets, and iOS Safari 16px auto-zoom prevention.

---

## 🛠️ Verification & Quality Gates

```bash
# Backend Quality Gates
cd backend
uv run python scripts/check_tenancy.py --static
uv run python scripts/check_permissions.py
uv run python scripts/check_no_money_floats.py
uv run python scripts/check_release_truth.py
uv run ruff check .

# Frontend Production Builds
npm run build --prefix frontend/admin-web
npm run build --prefix frontend/scanner-pwa
npm run build --prefix frontend/public-site
```

---

## 📄 Documentation

For developers, see [`docs/HANDOFF.md`](docs/HANDOFF.md) and [`.codesight/wiki/index.md`](.codesight/wiki/index.md).

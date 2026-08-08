# FITNESS NETWORK OS - IMPLEMENTATION MASTER PLAN

This document outlines the breakdown of the foundational implementation phases into actionable sub-tasks.

## 01. Repository Bootstrap & Tooling
- **Git & Monorepo Setup**: Initialize Git, create `.gitignore`.
- **Backend Directory Structure**: `backend/app`, `backend/tests`, `scripts`.
- **Python Package Management**: Set up `pyproject.toml` using `uv` or `poetry`.
- **Linting & Formatting**: Configure `ruff`, `mypy`, `black`/`isort` (or `ruff` natively).
- **Test Infrastructure**: Configure `pytest`, `pytest-cov`, `pytest-asyncio`.
- **Pre-commit Hooks**: Setup pre-commit for formatting and linting.

## 02. Docker Development Environment
- **Dockerfiles**: Create `Dockerfile` for FastAPI backend.
- **Docker Compose**: Create `docker-compose.yml` with:
  - `backend` (FastAPI + Uvicorn with reload)
  - `postgres` (PostgreSQL 16+)
  - `redis` (Redis 7+)
- **Scripts**: Makefile or `scripts/` shell scripts for easy `up`, `down`, `test`, `migrate`.

## 03. FastAPI & Core Setup
- **App Factory**: Initialize FastAPI application with CORS, exception handlers.
- **Settings Management**: Use `pydantic-settings` for environment variables.
- **Observability Stub**: Setup OpenTelemetry middleware & logger configuration.

## 04. Database Foundation & SQLAlchemy
- **SQLAlchemy 2.0**: Setup async engine, sessionmaker, and Base declarative model.
- **Alembic**: Initialize Alembic for migrations, configured to run with async SQLAlchemy.
- **Tenancy Aware Mixins**: Create a base model mixin that includes `tenant_id` and composite primary/foreign key support.

## 05. Organizations & Tenants
- **Domain Models**: `Organization` and `Tenant` tables.
- **Tenant Context Resolver**: FastAPI dependency to extract `tenant_id` from headers/tokens and set it in contextvars.
- **Schema Linter**: Script to ensure all tenant-owned tables have `tenant_id` and RLS enabled.

## 06. Authentication, Sessions & MFA
- **User Identity Models**: `User`, `Session`, `Device`.
- **Token & Cookie Management**: Secure HttpOnly cookie handling for sessions.
- **MFA Enablers**: Stubs/tables for MFA configuration.

## 07. PostgreSQL RLS (Row Level Security)
- **Migration Helper**: Alembic macros to easily enable RLS on tables.
- **DB Connection Setup**: Middleware or SQLAlchemy event to execute `SET LOCAL app.current_tenant_id = '...'` for every transaction.
- **Isolation Tests**: `pytest` fixtures validating that Tenant A cannot query Tenant B's data.

## 08. Authorization & RBAC
- **Roles & Permissions Models**: Define RBAC structures.
- **Scopes**: API endpoint security scopes.
- **Permission Matrix Checker**: CI script to validate scopes against a YAML source-of-truth matrix.

## 09. Audit & Telemetry
- **Audit Logging**: `audit_events` table for tracking critical actions (immutable).
- **Idempotency Engine**: `idempotency_keys` table and middleware to prevent double execution.

## 10. CI / CD & Architecture Fitness
- **GitHub Actions**: Workflows for Lint, Test, Security Scan.
- **Architecture Fitness**: Tests (e.g., using `pytest-arch` or custom imports check) to ensure domain boundaries are respected.
- **Release Gates**: Enforcement of the 12 Gates defined in `PRODUCTION_READINESS.md`.

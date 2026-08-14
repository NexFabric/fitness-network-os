# Libraries

> **Navigation aid.** Library inventory extracted via AST. Read the source files listed here before modifying exported functions.

**64 library files** across 2 modules

## Backend (61 files)

- `backend/alembic/env.py` — include_object, run_migrations_offline, do_run_migrations, run_migrations_online, run_async_migrations
- `backend/scripts/check_no_money_floats.py` — scan_models, scan_source_ast, main
- `backend/scripts/check_release_truth.py` — require, forbid, main
- `backend/scripts/process_notification_due.py` — build_parser, main, process_due_for_tenant
- `backend/alembic/versions/0a561fd73793_update_rbac_models.py` — upgrade, downgrade
- `backend/alembic/versions/261bdee314d7_sync_usermfamethod.py` — upgrade, downgrade
- `backend/alembic/versions/32bea30c0ed8_add_federation_models.py` — upgrade, downgrade
- `backend/alembic/versions/332634d9dc20_phase_27_add_mfa_totp_fields.py` — upgrade, downgrade
- `backend/alembic/versions/45e716039e1c_add_phase_8_membership_domain_models.py` — upgrade, downgrade
- `backend/alembic/versions/62afa7f4b3b1_add_status_to_membership_renewals.py` — upgrade, downgrade
- `backend/alembic/versions/6590aca081d6_make_expected_end_date_nullable.py` — upgrade, downgrade
- `backend/alembic/versions/67eca287af30_add_operational_mvp_models.py` — upgrade, downgrade
- `backend/alembic/versions/7558a909338a_phase_27_add_audit_events_model.py` — upgrade, downgrade
- `backend/alembic/versions/8d4b31a89f92_add_growth_and_crm_models.py` — upgrade, downgrade
- `backend/alembic/versions/8d7e354b271c_composite_tenant_fks.py` — upgrade, downgrade
- `backend/alembic/versions/96b95a7a1de8_phase_27_add_device_auth_models.py` — upgrade, downgrade
- `backend/alembic/versions/9d407d31b6cb_seed_rbac_canonical_matrix.py` — upgrade, downgrade
- `backend/alembic/versions/a1b2c3d4e5f6_add_access_models.py` — upgrade, downgrade
- `backend/alembic/versions/b3655ea622c4_add_chk_user_roles_tenant_or_org.py` — upgrade, downgrade
- `backend/alembic/versions/b3e2852df357_add_entitlement_models.py` — upgrade, downgrade
- `backend/alembic/versions/b5994ffbd643_add_membership_cancellation_and_renewal_.py` — upgrade, downgrade
- `backend/alembic/versions/bc4033d03939_add_terms_json_fields.py` — upgrade, downgrade
- `backend/alembic/versions/c4f9a1b2e3d0_seed_entitlement_permissions.py` — upgrade, downgrade
- `backend/alembic/versions/c938894ffe0d_add_organization_and_tenant_models.py` — upgrade, downgrade
- `backend/alembic/versions/c938894ffe0e_add_wave_1_core_gym_models.py` — upgrade, downgrade
- _…and 36 more files_

## Frontend (3 files)

- `frontend/scanner-pwa/src/api/client.ts` — getBaseUrl, getTenantId, setAuth, clearAuth, getDeviceKey, authenticateDevice, …
- `frontend/admin-web/src/api/client.ts` — getBaseUrl, getTenantId, setAuth, clearAuth, isAuthenticated, ensureCsrf, …
- `frontend/admin-web/src/auth/roles.ts` — homeRouteFor, RoleName, ROLES, FEDERATION_ROLES, OPS_ROLES, TRAINER_ROLES, …

---
_Back to [overview.md](./overview.md)_
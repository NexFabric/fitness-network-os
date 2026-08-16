# Image CVE triage — python:3.12-slim (Debian 13.6)

**Date:** 2026-08-17  
**Image:** `backend/Dockerfile.prod` `python:3.12-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`  
**Scans:** Trivy 0.58.1 HIGH,CRITICAL — CI `31972654793` + `31972977020`  
**Language packages (`uv.lock`):** 0 HIGH/CRITICAL  
**Owner:** A-OPS · **Review by:** 2026-09-17

Debian 13.6 OS packages. Trivy status is `affected` or `fix_deferred` with an
empty **Fixed Version**. None of these are on the FastAPI / worker request path
(CPython + uvicorn; no `perl`, gzip, ncurses TTY, or libacl in the entrypoint).

| CVE | Sev | Package | Fix | Decision |
|---|---|---|---|---|
| CVE-2026-41992 | HIGH | gzip | none | accept until Debian ships a patch |
| CVE-2026-54369 | HIGH | libacl1 | none | accept until Debian ships a patch |
| CVE-2025-69720 | HIGH | ncurses (4 pkgs) | none | accept until Debian ships a patch |
| CVE-2026-13221 | CRITICAL | perl-base | none | accept until Debian ships a patch |
| CVE-2026-42496 | CRITICAL | perl-base | fix_deferred | accept until Debian ships a patch |
| CVE-2026-42497 | HIGH | perl-base | fix_deferred | accept until Debian ships a patch |
| CVE-2026-9538 | HIGH | perl-base | fix_deferred | accept until Debian ships a patch |
| CVE-2026-57433 | HIGH | perl-base | none | accept until Debian ships a patch |
| CVE-2026-8376 | HIGH | perl-base | none | accept until Debian ships a patch |
| CVE-2026-48962 | HIGH | perl-base | none | accept until Debian ships a patch |
| CVE-2026-57432 | HIGH | perl-base | none | accept until Debian ships a patch |
| CVE-2026-53615 | HIGH | util-linux, bsdutils | none | accept until Debian ships a patch |

Do **not** add new IDs without a row. When Debian publishes a fix, bump the
base digest and drop the ID from `.trivyignore`.

# Image CVE triage — python:3.12-slim (Debian 13.6)

**Date:** 2026-08-17  
**Image:** `backend/Dockerfile.prod` `python:3.12-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`  
**Scan:** Trivy 0.58.1 HIGH,CRITICAL on CI `31972654793`  
**Language packages (`uv.lock`):** 0 HIGH/CRITICAL  
**Owner:** A-OPS · **Review by:** 2026-09-17

These rows are Debian 13.6 OS packages. Trivy status is `affected` with an
empty **Fixed Version**. They are not FastAPI request-path code.

| CVE | Sev | Package | Fix | Runtime path | Decision |
|---|---|---|---|---|---|
| CVE-2026-41992 | HIGH | gzip 1.13-1 | none | image ships gzip; app does not invoke it on HTTP/worker loops | accept until Debian ships a patch |
| CVE-2026-54369 | HIGH | libacl1 2.3.2-2+b1 | none | ACL helpers unused by uvicorn/workers | accept until Debian ships a patch |
| CVE-2025-69720 | HIGH | ncurses (libncursesw6, libtinfo6, ncurses-base, ncurses-bin) | none | TTY library; no interactive TTY in prod CMD | accept until Debian ships a patch |
| CVE-2026-13221 | CRITICAL | perl-base 5.40.1-6 | none | slim leftover; app is CPython, no `perl` in entrypoint | accept until Debian ships a patch |

Do **not** add new IDs here without a row. When Debian publishes a fix, bump
the base digest and drop the ID from `.trivyignore`.

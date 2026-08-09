# Phase 20 — Scanner PWA MVP

**Status:** 🟠 **IMPLEMENTED on branch** — **not LOCKED**  
**Path:** `frontend/scanner-pwa/`  
**Branch:** `feat/phase16-notifications-reports`  
**Do not claim:** production-ready

---

## Goal

Minimal door-scanner UI: paste or enter QR token → call access validate → show GRANTED/DENIED.

## Landed

| Item | Detail |
|------|--------|
| Stack | Vite + React + TypeScript + Tailwind |
| Validate | `POST /api/v1/access/qr/validate` (`access:validate`) |
| Auth | Staff session token + tenant in localStorage |
| UI | Token textarea, optional location_id, consume flag, GRANTED/DENIED panel |
| PWA | `manifest.json`, shell `service-worker.js`, icons 192/512 |
| Docker | `Dockerfile` |
| README | `frontend/scanner-pwa/README.md` |

## Gaps / next

- No camera barcode decoder (paste/token only)
- No offline validate / device heartbeat
- Service worker caches shell only (no API offline)
- Needs staff `access:validate` credential provisioning path

## Verify

```bash
cd frontend/scanner-pwa
npm install
VITE_API_URL=http://localhost:8000 npm run build
npm run dev
```

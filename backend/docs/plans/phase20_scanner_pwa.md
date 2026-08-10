# Phase 20 — Scanner PWA MVP

**Status:** 🟠 **MERGED on main** — **not LOCKED**  
**Path:** `frontend/scanner-pwa/`  
**Main evidence:** PR #26 scaffold + #40 camera + #44 Access brand  
**Do not claim:** production-ready

---

## Goal

Door-scanner UI: camera or paste QR → `POST /api/v1/access/qr/validate` → GRANT/DENY.

## Landed (main)

| Item | Detail |
|------|--------|
| Stack | Vite + React + TypeScript + Tailwind |
| Validate | `POST /api/v1/access/qr/validate` (`access:validate`) |
| Auth | Staff session token + tenant in localStorage |
| Camera | `CameraQrScanner` — getUserMedia + BarcodeDetector / jsQR; paste fallback |
| Brand | GymClubNex · Access; dark door-device UI; no raw API path as hero copy |
| Result UX | Large GRANT/DENY with icon + text |
| PWA | `manifest.json`, shell service worker, icons |
| Docker | `Dockerfile` |
| CI | Scanner PWA Build job |

## Gaps / next

- Device auth / offline validate / heartbeat  
- Service worker caches shell only  
- Not LOCKED; not production-ready  

## Verify

```bash
cd frontend/scanner-pwa
npm install
VITE_API_URL=http://localhost:8000 npm run build
npm run dev -- --port 5174
```

# GymClubNex Scanner PWA (Phase 20 MVP)

Vite + React + TypeScript + Tailwind progressive web app for access QR validation.

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Dev server (port 3001) |
| `npm run build` | Typecheck (`tsc`) + production build |
| `npm run preview` | Preview production build |

## Environment

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | No | API base URL. Default: `http://localhost:8000` |

Example `.env` (do not commit secrets):

```bash
VITE_API_URL=http://localhost:8000
```

## Validate QR

- **Endpoint:** `POST /api/v1/access/qr/validate`
- **Auth:** `Authorization: Bearer <session>` + `X-Tenant-ID`
- **Permission:** `access:validate`
- **Body:** `{ token, location_id?, action?, consume? }`
- **UI:** shows **GRANTED** / **DENIED** and `reason`

Credentials are stored in `localStorage` (`fnos_scanner_token`, `fnos_scanner_tenant_id`).

## Camera QR capture

- **Scan with camera** uses `getUserMedia` (prefers `facingMode: environment` / back camera).
- Decode: native **BarcodeDetector** when available, otherwise **jsQR** on video frames.
- On successful decode: fills the QR token field and auto-validates if credentials are saved.
- Paste token + Validate remains the fallback if permission is denied, no camera, or insecure context.
- **Browser note:** camera access requires a [secure context](https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts) (HTTPS or `localhost`). Local HTTP on a LAN IP will block `getUserMedia`; use paste or tunnel/HTTPS.

## PWA

- `public/manifest.json` — name/theme for installability
- `public/service-worker.js` — caches app shell only (registered from `main.tsx`)

## Docker

```bash
docker build -t gymclubnex-scanner-pwa .
```

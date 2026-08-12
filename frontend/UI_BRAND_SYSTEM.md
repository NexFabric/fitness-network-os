# GymClubNex — UI Brand System

**Date:** 2026-08-10  
**Status:** ACTIVE design contract — dark-first across all surfaces  
**Not:** multi-tenant white-label (MASTER_SPEC “tenant branding” later)

---

## Reality check

| Surface | Stack | Path | Theme |
|---------|-------|------|-------|
| Public marketing | Next.js 16 + Tailwind v4 | `frontend/public-site/` | Dark |
| Admin Web | Vite + React + Tailwind v3 | `frontend/admin-web/` | Dark ops console |
| Scanner PWA | Vite + React + Tailwind v3 | `frontend/scanner-pwa/` | Dark door-desk |

---

## Brand direction

**Name lock:** GymClubNex (product) · Fitness Network OS (platform tagline)

**Personality:** athletic ops console — confident, calm, fast. Door-desk ready, not consumer fitness app fluff.

**Visual system (dark-first)**

| Token | Value | Use |
|-------|--------|-----|
| Ink | `#F8FAFC` | Primary text on dark |
| Ink muted | `#94A3B8` | Secondary text, labels |
| Surface | `#020617` | Page background (slate-950) |
| Surface raised | `#0B1220` / `#0F172A` | Sidebar, sticky chrome, panels |
| Card | `rgba(15, 23, 42, 0.55)` + border | Cards / elevated panels |
| Border | `rgba(51, 65, 85, 0.55)` | Hairlines |
| Brand | `#0D9488` (teal-600) | Primary actions, active nav |
| Brand deep | `#0F766E` | Hover |
| Brand light | `#14B8A6` | Focus chips, highlights |
| Accent | `#34D399` (emerald-400) | Success, live pulse |
| Warn | `#F59E0B` | Warnings / pending |
| Danger | `#DC2626` | Errors / DENIED |
| Font | `DM Sans` (+ system-ui stack) | All surfaces |
| Radius | `12px` cards, `8px` controls | Consistent |
| Shadow | soft teal glow on primary CTA only | Restraint |

**Do not use:** generic purple/indigo as brand; neon multi-glow stacks; fake social-proof logos; seed/API debug on default admin UI; dead nav anchors.

**Scanner** stays high-contrast dark with the same teal/emerald family so door devices feel distinct from office admin but share the brand mark.

---

## Surfaces in scope

1. **Public site** — marketing landing, product proof, pricing, CTA  
2. **Admin login** — branded full-bleed mesh  
3. **Admin shell** — sidebar + mobile drawer, logo mark, tenant chip  
4. **Admin pages** — Dashboard, Members, Locations, Finance  
5. **Scanner** — brand header, GRANT/DENY, camera + paste  

**Out of scope:** member mobile app, full white-label per gym, light-mode toggle (optional later).

---

## Accessibility (baseline)

- Visible focus rings on controls (`ring-brand`)  
- Labels on all inputs  
- Contrast ≥ WCAG AA for text on surfaces  
- Status never color-only (text + color; icons where helpful)  
- 44px touch targets on mobile primary actions  

---

## Implementation map

| App | Key paths |
|-----|-----------|
| Public | `frontend/public-site/src/app/*`, `src/components/*` |
| Admin | `frontend/admin-web/src/**`, `tailwind.config.js`, `index.html` |
| Scanner | `frontend/scanner-pwa/src/**`, `tailwind.config.js` |
| Doc | this file |

---

## Acceptance

- [x] Dark-first tokens documented and match code  
- [x] Public IA: all nav anchors resolve; mobile menu works  
- [x] Admin sidebar shell; no seed/API dump on default dashboard  
- [x] Scanner uses brand tokens (no indigo decorative primary)  
- [x] `npm run build` green on all three apps  

# GymClubNex — UI Brand System (MVP surface)

**Date:** 2026-08-10  
**Status:** ACTIVE design contract — **implemented on main** (Admin #45, Scanner #44)  
**Main SHA (when merged):** `325d93d`  
**Not:** full marketing site / multi-tenant white-label (MASTER_SPEC “tenant branding” later)  
**Production-ready claim:** NO

---

## Reality check

| Surface | On main now | Still open |
|---------|-------------|------------|
| Admin Web | Teal brand system, login/shell/dashboard/CRUD create | Cookie-only session, edit/ops depth |
| Scanner PWA | Access brand, camera + paste, GRANT/DENY UX | Device auth / offline |
| Landing / public site | **None** | Out of admin MVP scope |
| Formal Figma | **None** — this markdown is the contract | Optional later |
| MASTER_SPEC tenant branding | Not product white-label | Per-gym themes later |

---

## Brand direction

**Name lock:** GymClubNex (product) · Fitness Network OS (platform tagline)

**Personality:** athletic ops console — confident, calm, fast. Door-desk ready, not consumer fitness app fluff.

**Visual system**

| Token | Value | Use |
|-------|--------|-----|
| Ink | `#0B1220` | Text, dark panels |
| Surface | `#F4F6F8` | Admin page bg |
| Card | `#FFFFFF` | Cards |
| Brand | `#0D9488` (teal-600) | Primary actions, active nav |
| Brand deep | `#0F766E` | Hover |
| Accent | `#34D399` (emerald-400) | Scanner highlights, success |
| Warn | `#F59E0B` | Warnings |
| Danger | `#DC2626` | Errors / DENIED |
| Font display | `DM Sans` (or system-ui stack if offline) | Headings |
| Font body | `DM Sans` / system-ui | UI |
| Radius | `12px` cards, `8px` controls | Consistent |
| Shadow | soft `0 1px 2px rgb(0 0 0 / 0.05)` | Cards |

**Do not use:** generic purple indigo primary as brand (legacy admin indigo → replace with teal).

**Scanner** stays dark (`slate-950` / `slate-900`) with emerald accent so door devices feel different from office admin, but same brand mark and teal/emerald family.

---

## Surfaces in scope (this wave)

1. **Admin login** — branded full-bleed, not plain gray box  
2. **Admin shell** — logo mark, nav pills, tenant chip  
3. **Dashboard** — ops cards with counts/links, no raw “MVP shell” copy  
4. **Members / Locations** — same form/table language  
5. **Scanner** — hide raw endpoint paths; brand header; keep camera+paste  

**Out of scope now:** public marketing landing, member mobile app, full white-label per gym, dark mode toggle for admin.

---

## Accessibility (baseline)

- Visible focus rings on controls  
- Labels on all inputs  
- Contrast ≥ WCAG AA for text on surfaces  
- Don’t rely on color alone for GRANT/DENY  

---

## Implementation map

| App | Paths |
|-----|--------|
| Admin | `frontend/admin-web/` — `tailwind.config.js`, `index.css`, `Layout`, `Login`, `Dashboard`, `Members`, `Locations` |
| Scanner | `frontend/scanner-pwa/` — header, section titles, result states |
| Doc | this file |

---

## Acceptance

- [ ] Login feels branded GymClubNex (not generic template)  
- [ ] Admin nav uses brand color, not indigo  
- [ ] Dashboard useful for day-1 ops language  
- [ ] Scanner does not expose `POST /api/v1/...` as primary UI copy  
- [ ] `npm run build` both apps green  
- [ ] Live `:5173` / `:5174` after merge  

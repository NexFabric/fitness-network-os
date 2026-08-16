# Repository visibility and license

**Status:** **PUBLIC · LICENSE UNDECIDED (human)**

This file is a decision brief. **It is not a license.** It does not grant
rights, waive rights, or pick SPDX. An agent must not invent a `LICENSE`
file or claim this project is open source.

## Observed facts (2026-08-16)

| Fact | Value |
|---|---|
| GitHub | [`NexFabric/fitness-network-os`](https://github.com/NexFabric/fitness-network-os) |
| Visibility | **PUBLIC** (`isPrivate: false`) |
| GitHub `licenseInfo` | **`null`** |
| Tree | no `LICENSE`, `COPYING`, or `NOTICE` |
| Related legal copy | `docs/ops/LEGAL_APPROVAL.md` (KVKK / DPA — **different** decision) |
| Related inbound note | `docs/plans/SHELF_NU_ADAPTATION_REFERENCE.md` (Shelf.nu is AGPL-3.0; this repo is a clean-room conceptual reference, **not** a license for Fitness Network OS) |

GitHub currently shows this repository as **public** with `license = null`.
That is not a technical launch bug. Application security must not depend
on source secrecy (RLS, RBAC, signed QR, no raw PAN, no money floats).

It **is** a company decision that an agent must not invent.

Until a human writes a `LICENSE` file **and** records the choice in the
signature table below, do not treat the project as open source and do not
treat it as confidential source.

## Decision the human must make

Two product/legal postures are on the table. Visibility (public vs private)
is a separate lever and does not substitute for a license.

| Option | Meaning | What changes in the tree | What does **not** change |
|---|---|---|---|
| **A — Source-visible proprietary** | Stay (or become) public; source is readable; reuse is **not** granted | Human/counsel adds a proprietary / All Rights Reserved `LICENSE` + copyright holder | App security model, CI, tenancy. Public clones already taken stay taken. |
| **B — Open source** | Stay public; third parties receive the rights the chosen SPDX license grants | Human/counsel adds a **real** OSS `LICENSE` (MIT / Apache-2.0 / AGPL-3.0 / other SPDX) | Already-shipped copies cannot have the grant pulled back. Inbound dep licenses still apply. |
| **C — Private proprietary** | Flip GitHub visibility to **private**; source is no longer world-readable | Owner changes GitHub visibility. Optional proprietary `LICENSE` still needed for contractors / staff | Historical public clones, forks, and CI logs already published. Security still must not rely on secrecy. |
| **D — Status quo** (current) | Public, `license = null` | **Nothing.** This is not a decision. | Ambiguous to customers, contributors, and counsel. Must **not** be described as OSS. |

**Recommended default if the product is a commercial SaaS:** **A** or **C**.
That is a recommendation, not a grant. Counsel may reject it.

**Do not pick B (especially AGPL-3.0) because Shelf.nu is AGPL.** Shelf.nu
is an inbound reference only. Choosing AGPL for *this* repo would impose
network copyleft on the hosted product. That is a counsel call.

## Consequences

| Topic | A — public proprietary | B — public OSS | C — private | D — status quo |
|---|---|---|---|---|
| World can clone / fork | Yes (GitHub public) | Yes, **and** they have a reuse grant | No (new clones). Old clones may exist. | Yes, **without** a written grant |
| GitHub "License" badge | Custom / proprietary if recorded | SPDX license GitHub recognizes | Hidden with the repo | **None** (`license = null`) |
| Competitors reading architecture | Already true today | Same, plus they may reuse | Reduced going forward | Already true today |
| Contributors / PRs from strangers | Need a CLA / DCO if you accept them | Same, plus outbound license binds you | Invite-only | Unclear; risky to accept |
| Customers asking "is this OSS?" | Answer: **no** | Answer: **yes, under \<SPDX\>** | Answer: **no** | Answer: **undecided — do not say yes** |
| Hosted SaaS / AGPL risk | None from *this* repo's license | High if AGPL; low if MIT/Apache | None from *this* repo's license | None written; still not OSS |
| Patent grant | None unless you write one | Apache-2.0 includes one; MIT does not | None unless you write one | None |
| Secrets / keys in git | Forbidden regardless | Forbidden regardless | Forbidden regardless | Forbidden regardless |
| Phase 26 / production-ready | **Does not pass or fail** this gate | Same | Same | Same |
| Reversibility | Can go private later; text already published stays published | Grant on copies already taken is **not** retractable | Can go public later | Cheap to leave; expensive to explain |

## Who signs

An agent, CI job, or PR author **cannot** close this.

| Role | Signs? | Why |
|---|---|---|
| Company owner / repo owner (`NexFabric`) | **Yes — required** | Visibility flip and copyright holder |
| Counsel | **Yes — required for B;** recommended for A/C | Outbound license, inbound AGPL boundary, CLA |
| Engineering / agent | **No** | May draft this brief only. Must not write `LICENSE` or change visibility. |
| Dependabot / CI | **No** | Irrelevant to SPDX or GitHub visibility |

## Signature — human

Leave blank until the owner (and counsel, if option B) has decided.
Filling this table is the only way this item closes. Creating a `LICENSE`
without this table is not a close.

| Alan | Değer |
|---|---|
| Date | |
| Who (owner) | |
| Counsel (if any) | |
| Choice | A / B / C (not D) |
| If B: SPDX id | e.g. MIT / Apache-2.0 / AGPL-3.0 — **do not invent** |
| Visibility after decision | public / private |
| `LICENSE` path added | |
| Notes | |

## Agent rules

- Do **not** create or commit `LICENSE`, `COPYING`, or `NOTICE`.
- Do **not** set GitHub `license` metadata or change repository visibility.
- Do **not** call this repository open source, MIT, Apache, or AGPL.
- Do **not** treat public visibility as a security defect or as Phase 26 evidence.
- Do **not** copy Shelf.nu (or any other third-party) license text here.
- Point humans at this file: `docs/HANDOFF.md` → Public repo / lisans kararı.

Pickup: `docs/HANDOFF.md`. Checklist authority: `docs/PROGRESS_CHECKLIST.md`.
KVKK / DPA copy is `docs/ops/LEGAL_APPROVAL.md` and is **not** this decision.

# KVKK / legal approval checklist

**Status:** **UNVERIFIED** · HUMAN/LEGAL APPROVAL OPEN

Index: `docs/ops/EXTERNAL_GATES.md`. Technical controls (consent, DSAR
export/erasure, legal hold on open invoices, retention worker) are
landed in code. Those tests do **not** approve legal copy. Repository
visibility / LICENSE is a **different** decision
(`docs/ops/REPO_VISIBILITY.md`).

## Close this gate (checklist)

Owner: **human** (counsel, not an agent). There is no in-repo command.

Counsel reviews the shipped surfaces and signs the table below:

| # | Decision | Where to look (draft, not approved) | Counsel |
|---|---|---|---|
| 1 | Retention periods per data category | `data_retention_policies.retention_days` — engineering default is “requires legal review” | ☐ |
| 2 | KVKK aydınlatma metni | Public `/kvkk` (`frontend/public-site/src/app/kvkk/page.tsx`) | ☐ |
| 3 | Lawful bases for processing | Same page §3 + consent records | ☐ |
| 4 | DPA with the operating company | Off-tree contract | ☐ |
| 5 | Subprocessor list | Off-tree; include AWS (S3/KMS), SMTP, any PSP | ☐ |
| 6 | Deletion / anonymization vs finance retention | `POST /me/dsar/erasure` holds on OPEN/PARTIALLY_PAID/DRAFT invoices | ☐ |

Do not invent legal text in this repository to tick those boxes. The
`/kvkk` page is a **placeholder** until counsel approves replacement
copy.

## Technical controls that are not this gate

| Control | Code | What it does not do |
|---|---|---|
| DSAR export | `POST /me/dsar/...`, admin inbox | Does not set a lawful basis |
| DSAR erasure | anonymize + session revoke | Does not waive finance legal hold |
| Retention worker | `app/workers/retention.py` | Does not pick `retention_days` |
| Consent records | `/me` consents | Does not draft the lighting text |

## Signature — counsel

| Alan | Değer |
|---|---|
| Date | |
| Counsel | |
| Organisation | |
| `/kvkk` copy | APPROVE / REJECT |
| Retention periods | APPROVE / REJECT |
| DPA + subprocessors | APPROVE / REJECT |
| Notes | |

Leave this table empty until a human lawyer writes in it. An agent
must not sign.

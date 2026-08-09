# Standing Review Protocol (post-work)

After **every** implementation batch (agent or human), run an independent review before claiming done.

## Trigger

- Any commit series on a feature branch
- After Phase closeout (15.5, 15.6, 16, …)
- Before opening or updating a PR as “ready”

## Reviewer

Spawn / assign a **read-only review agent** with:

- Access to code, tests, docs
- Permission to run focused pytest (not to merge or change branch protection)

Prompt seed: use the same checklist as the latest  
`backend/docs/plans/STANDING_REVIEW_latest.md`  
and overwrite that file with a new dated review.

## Must verify (project-wide)

1. **Tenancy:** Gym = tenant; queries filter `tenant_id`; RLS not undermined  
2. **Authz:** no BOLA; `*:self` requires owner; staff vs member surfaces  
3. **Money:** `amount_minor` int only; no float money fields  
4. **Events:** no public generic outbox/inbox inject; registered `event_type`  
5. **Domain boundaries:** Membership ↛ WhatsApp/providers; Domain → Outbox → Adapter  
6. **Docs truth:** no LOCKED / production-ready without merge + main CI  
7. **Tests:** each security/reliability claim has a real test path  

## Output

Write/update: `backend/docs/plans/STANDING_REVIEW_latest.md`

| Verdict | Meaning |
|---------|---------|
| PASS | Safe to proceed to next batch / PR CI |
| PASS_WITH_P2 | Proceed; log P2 follow-ups |
| NEEDS_WORK | Fix before next phase |
| BLOCKED | P0/P1 open — stop |

## Orchestrator rule

```text
Implement → focused tests → Standing Review → fix if NEEDS_WORK/BLOCKED → commit/push
```

Do **not** skip Standing Review to “save time.”

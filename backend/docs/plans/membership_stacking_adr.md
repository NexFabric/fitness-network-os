# Membership Stacking Policy (GLOBAL_EXCLUSIVE_V1)

## Context
In GymClubNex, a member can have one or multiple memberships. In Phase 8, we needed to define how multiple memberships for a single member behave.
Should a member be allowed to have multiple active memberships simultaneously (e.g. standard gym access + pool access)? Or should they be globally exclusive?

## Decision
For MVP Phase 8, we have adopted the **GLOBAL_EXCLUSIVE_V1** policy.

This means:
- A single member can only have **one active or scheduled membership at a time** globally across the tenant.
- If a member has a membership in `ACTIVE`, `FROZEN`, `PAST_DUE`, `SCHEDULED`, or `PENDING` state, they cannot start a new membership. The system explicitly blocks this in `MembershipService.start_membership`.

## Rationale
- Simplifies access control and scheduling logic for MVP.
- A single member can upgrade or downgrade their membership via renewals, instead of purchasing an overlapping membership.
- True stackable memberships (e.g., base plan + add-on packages like personal training) require more complex entitlement merging and billing semantics, which is deferred to a future phase.

## Enforcement
Implemented at the application service level inside `start_membership` with an explicit status guard:

```python
stmt = select(Membership).where(
    Membership.member_id == member_id,
    Membership.status.in_({"ACTIVE", "FROZEN", "PAST_DUE", "SCHEDULED", "PENDING"})
)
```

If this returns any records, the operation is rejected.

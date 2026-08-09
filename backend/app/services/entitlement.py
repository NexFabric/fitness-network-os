from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entitlement import (
    EntitlementDefinition,
    EntitlementTransaction,
    EntitlementTransactionType,
    EntitlementType,
    EntitlementWallet,
    MembershipEntitlement,
    MembershipEntitlementStatus,
    PlanEntitlement,
)
from app.models.membership import Membership


class EntitlementService:
    """Wallet/ledger entitlement engine."""

    CONSUMABLE_MEMBERSHIP_STATUSES = frozenset({"ACTIVE", "PAST_DUE"})

    @staticmethod
    def _result(
        *,
        granted: bool,
        reason: str | None,
        last_known_state: str = "ACTIVE",
        remaining: int | None = None,
        offline_ttl_hours: int | None = None,
    ) -> dict:
        out: dict = {
            "granted": granted,
            "reason": reason,
            "last_known_state": last_known_state,
            "remaining": remaining,
        }
        if offline_ttl_hours is not None:
            out["offline_ttl_hours"] = offline_ttl_hours
        return out

    @staticmethod
    async def _get_definition(
        db: AsyncSession, tenant_id: UUID, code: str
    ) -> EntitlementDefinition | None:
        result = await db.execute(
            select(EntitlementDefinition).where(
                EntitlementDefinition.tenant_id == tenant_id,
                EntitlementDefinition.code == code,
                EntitlementDefinition.is_active.is_(True),
            )
        )
        return result.scalars().first()

    @staticmethod
    async def _get_active_membership(
        db: AsyncSession, tenant_id: UUID, member_id: UUID, *, for_update: bool = False
    ) -> Membership | None:
        stmt = select(Membership).where(
            Membership.tenant_id == tenant_id,
            Membership.member_id == member_id,
            Membership.status.in_(list(EntitlementService.CONSUMABLE_MEMBERSHIP_STATUSES)),
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def _get_wallet_for_membership(
        db: AsyncSession,
        tenant_id: UUID,
        membership_id: UUID,
        entitlement_id: UUID,
        *,
        for_update: bool = False,
    ) -> EntitlementWallet | None:
        stmt = select(EntitlementWallet).where(
            EntitlementWallet.tenant_id == tenant_id,
            EntitlementWallet.membership_id == membership_id,
            EntitlementWallet.entitlement_id == entitlement_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def _find_tx_by_idempotency(
        db: AsyncSession, tenant_id: UUID, idempotency_key: str
    ) -> EntitlementTransaction | None:
        result = await db.execute(
            select(EntitlementTransaction).where(
                EntitlementTransaction.tenant_id == tenant_id,
                EntitlementTransaction.idempotency_key == idempotency_key,
            )
        )
        return result.scalars().first()

    @staticmethod
    def _wallet_expired(wallet: EntitlementWallet, now: datetime) -> bool:
        if wallet.expires_at is None:
            return False
        expires = wallet.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        return expires < now

    @classmethod
    async def check_access(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        member_id: UUID,
        action: str,
        quantity: int = 1,
    ) -> dict:
        if quantity <= 0:
            return cls._result(
                granted=False, reason="INVALID_QUANTITY", last_known_state="INACTIVE"
            )

        membership = await cls._get_active_membership(db, tenant_id, member_id)
        if not membership:
            return cls._result(
                granted=False, reason="NO_ACTIVE_MEMBERSHIP", last_known_state="INACTIVE"
            )

        ent_def = await cls._get_definition(db, tenant_id, action)
        if not ent_def:
            return cls._result(
                granted=False,
                reason="UNKNOWN_ACTION",
                last_known_state=membership.status,
            )

        wallet = await cls._get_wallet_for_membership(
            db, tenant_id, membership.id, ent_def.id
        )
        if not wallet:
            return cls._result(
                granted=False,
                reason="NO_WALLET",
                last_known_state=membership.status,
            )

        now = datetime.now(UTC)
        if cls._wallet_expired(wallet, now):
            return cls._result(
                granted=False,
                reason="WALLET_EXPIRED",
                last_known_state=membership.status,
                remaining=wallet.remaining,
            )

        if ent_def.type == EntitlementType.COUNT:
            if wallet.remaining < quantity:
                return cls._result(
                    granted=False,
                    reason="ZERO_BALANCE" if wallet.remaining <= 0 else "INSUFFICIENT_BALANCE",
                    last_known_state=membership.status,
                    remaining=wallet.remaining,
                )
            return cls._result(
                granted=True,
                reason=None,
                last_known_state=membership.status,
                remaining=wallet.remaining,
            )

        # BOOLEAN: grant if wallet exists and remaining > 0 (allocated grant flag)
        if wallet.remaining <= 0 and wallet.allocated <= 0:
            return cls._result(
                granted=False,
                reason="NOT_ENTITLED",
                last_known_state=membership.status,
                remaining=wallet.remaining,
            )
        return cls._result(
            granted=True,
            reason=None,
            last_known_state=membership.status,
            remaining=wallet.remaining,
        )

    @classmethod
    async def consume_access(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        member_id: UUID,
        action: str,
        idempotency_key: str,
        quantity: int = 1,
        actor_id: UUID | None = None,
    ) -> dict:
        if not idempotency_key:
            return cls._result(
                granted=False, reason="MISSING_IDEMPOTENCY_KEY", last_known_state="INACTIVE"
            )
        if quantity <= 0:
            return cls._result(
                granted=False, reason="INVALID_QUANTITY", last_known_state="INACTIVE"
            )

        existing = await cls._find_tx_by_idempotency(db, tenant_id, idempotency_key)
        if existing:
            return cls._result(
                granted=existing.transaction_type
                == EntitlementTransactionType.CONSUME.value,
                reason="IDEMPOTENT",
                last_known_state="ACTIVE",
                remaining=existing.balance_after,
                offline_ttl_hours=24
                if existing.transaction_type == EntitlementTransactionType.CONSUME.value
                else None,
            )

        membership = await cls._get_active_membership(
            db, tenant_id, member_id, for_update=True
        )
        if not membership:
            return cls._result(
                granted=False, reason="NO_ACTIVE_MEMBERSHIP", last_known_state="INACTIVE"
            )

        ent_def = await cls._get_definition(db, tenant_id, action)
        if not ent_def:
            return cls._result(
                granted=False,
                reason="UNKNOWN_ACTION",
                last_known_state=membership.status,
            )

        try:
            wallet = await cls._get_wallet_for_membership(
                db, tenant_id, membership.id, ent_def.id, for_update=True
            )
            if not wallet:
                return cls._result(
                    granted=False,
                    reason="NO_WALLET",
                    last_known_state=membership.status,
                )

            now = datetime.now(UTC)
            if cls._wallet_expired(wallet, now):
                return cls._result(
                    granted=False,
                    reason="WALLET_EXPIRED",
                    last_known_state=membership.status,
                    remaining=wallet.remaining,
                )

            balance_before = wallet.remaining

            if ent_def.type == EntitlementType.COUNT:
                if wallet.remaining < quantity:
                    return cls._result(
                        granted=False,
                        reason="ZERO_BALANCE"
                        if wallet.remaining <= 0
                        else "INSUFFICIENT_BALANCE",
                        last_known_state=membership.status,
                        remaining=wallet.remaining,
                    )
                wallet.remaining -= quantity
                wallet.consumed += quantity
            else:
                # BOOLEAN: consume is authorization proof; do not double-spend counters
                if wallet.remaining <= 0 and wallet.allocated <= 0:
                    return cls._result(
                        granted=False,
                        reason="NOT_ENTITLED",
                        last_known_state=membership.status,
                        remaining=wallet.remaining,
                    )

            tx = EntitlementTransaction(
                tenant_id=tenant_id,
                wallet_id=wallet.id,
                membership_id=membership.id,
                entitlement_id=ent_def.id,
                transaction_type=EntitlementTransactionType.CONSUME.value,
                quantity=quantity if ent_def.type == EntitlementType.COUNT else 0,
                balance_before=balance_before,
                balance_after=wallet.remaining,
                idempotency_key=idempotency_key,
                actor_id=actor_id,
                reason=action,
            )
            db.add(tx)
            await db.commit()

            return cls._result(
                granted=True,
                reason=None,
                last_known_state=membership.status,
                remaining=wallet.remaining,
                offline_ttl_hours=24,
            )
        except IntegrityError:
            await db.rollback()
            # Race on unique idempotency key — return original outcome
            raced = await cls._find_tx_by_idempotency(db, tenant_id, idempotency_key)
            if raced:
                return cls._result(
                    granted=raced.transaction_type
                    == EntitlementTransactionType.CONSUME.value,
                    reason="IDEMPOTENT",
                    last_known_state="ACTIVE",
                    remaining=raced.balance_after,
                    offline_ttl_hours=24
                    if raced.transaction_type
                    == EntitlementTransactionType.CONSUME.value
                    else None,
                )
            return cls._result(
                granted=False,
                reason="CONCURRENCY_ERROR",
                last_known_state="ACTIVE",
            )
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def grant_from_plan_version(
        cls,
        db: AsyncSession,
        membership: Membership,
        plan_version_id: UUID,
        *,
        actor_id: UUID | None = None,
        reason: str = "plan_grant",
    ) -> list[EntitlementWallet]:
        """Snapshot PlanEntitlements into MembershipEntitlement + allocate wallets."""
        pe_result = await db.execute(
            select(PlanEntitlement).where(
                PlanEntitlement.tenant_id == membership.tenant_id,
                PlanEntitlement.plan_version_id == plan_version_id,
            )
        )
        plan_ents = list(pe_result.scalars().all())
        wallets: list[EntitlementWallet] = []
        now = datetime.now(UTC)

        for pe in plan_ents:
            me_result = await db.execute(
                select(MembershipEntitlement).where(
                    MembershipEntitlement.tenant_id == membership.tenant_id,
                    MembershipEntitlement.membership_id == membership.id,
                    MembershipEntitlement.entitlement_id == pe.entitlement_id,
                )
            )
            me = me_result.scalars().first()
            if me is None:
                me = MembershipEntitlement(
                    tenant_id=membership.tenant_id,
                    membership_id=membership.id,
                    entitlement_id=pe.entitlement_id,
                    source_plan_version_id=plan_version_id,
                    granted_quantity=pe.quantity,
                    unlimited=pe.unlimited,
                    valid_from=membership.start_date,
                    valid_until=membership.end_date,
                    status=MembershipEntitlementStatus.ACTIVE.value,
                )
                db.add(me)
                await db.flush()
            else:
                me.source_plan_version_id = plan_version_id
                me.granted_quantity = pe.quantity
                me.unlimited = pe.unlimited
                me.valid_from = membership.start_date
                me.valid_until = membership.end_date
                me.status = MembershipEntitlementStatus.ACTIVE.value
                await db.flush()

            wallet = await cls.allocate_for_membership_entitlement(
                db,
                membership=membership,
                membership_entitlement=me,
                actor_id=actor_id,
                reason=reason,
                at=now,
            )
            wallets.append(wallet)

        await db.flush()
        return wallets

    @classmethod
    async def allocate_for_membership_entitlement(
        cls,
        db: AsyncSession,
        *,
        membership: Membership,
        membership_entitlement: MembershipEntitlement,
        actor_id: UUID | None = None,
        reason: str = "allocate",
        at: datetime | None = None,
    ) -> EntitlementWallet:
        now = at or datetime.now(UTC)
        result = await db.execute(
            select(EntitlementWallet)
            .where(
                EntitlementWallet.tenant_id == membership.tenant_id,
                EntitlementWallet.membership_entitlement_id == membership_entitlement.id,
            )
            .with_for_update()
        )
        wallet = result.scalars().first()

        # BOOLEAN grants use remaining=1 as "entitled" flag if unlimited or quantity>0
        if membership_entitlement.unlimited:
            target_remaining = max(membership_entitlement.granted_quantity, 1)
            allocate_qty = target_remaining
        else:
            allocate_qty = membership_entitlement.granted_quantity

        if wallet is None:
            wallet = EntitlementWallet(
                tenant_id=membership.tenant_id,
                member_id=membership.member_id,
                membership_id=membership.id,
                membership_entitlement_id=membership_entitlement.id,
                entitlement_id=membership_entitlement.entitlement_id,
                allocated=allocate_qty,
                reserved=0,
                consumed=0,
                remaining=allocate_qty,
                expires_at=membership_entitlement.valid_until or membership.end_date,
            )
            db.add(wallet)
            await db.flush()
            balance_before = 0
            balance_after = wallet.remaining
            qty = allocate_qty
        else:
            # Top-up remaining to new grant for renewals (simple Phase 9 policy)
            balance_before = wallet.remaining
            delta = allocate_qty - wallet.remaining
            if delta > 0:
                wallet.allocated += delta
                wallet.remaining += delta
                qty = delta
            else:
                qty = 0
            wallet.expires_at = membership_entitlement.valid_until or membership.end_date
            balance_after = wallet.remaining
            await db.flush()

        if qty > 0 or wallet is not None:
            tx = EntitlementTransaction(
                tenant_id=membership.tenant_id,
                wallet_id=wallet.id,
                membership_id=membership.id,
                entitlement_id=membership_entitlement.entitlement_id,
                transaction_type=EntitlementTransactionType.ALLOCATE.value,
                quantity=max(0, qty),
                balance_before=balance_before,
                balance_after=balance_after,
                idempotency_key=f"alloc:{membership.id}:{membership_entitlement.entitlement_id}:{uuid4()}",
                actor_id=actor_id,
                reason=reason,
            )
            db.add(tx)
            await db.flush()

        return wallet

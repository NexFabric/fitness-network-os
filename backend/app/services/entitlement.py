from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entitlement import (
    EntitlementDefinition,
    EntitlementTransaction,
    EntitlementWallet,
)


class EntitlementService:
    @staticmethod
    async def consume_access(db: AsyncSession, tenant_id: UUID, member_id: UUID, action: str, idempotency_key: str) -> dict:
        try:
            # Check for idempotency
            tx_check = await db.execute(
                select(EntitlementTransaction).where(
                    EntitlementTransaction.tenant_id == tenant_id,
                    EntitlementTransaction.idempotency_key == idempotency_key
                )
            )
            if tx_check.scalars().first():
                return {"granted": True, "last_known_state": "ACTIVE", "reason": "IDEMPOTENT"}

            # Get the definition
            def_result = await db.execute(
                select(EntitlementDefinition).where(
                    EntitlementDefinition.tenant_id == tenant_id,
                    EntitlementDefinition.code == action
                )
            )
            ent_def = def_result.scalars().first()
            if not ent_def:
                return {"granted": False, "reason": "UNKNOWN_ACTION", "last_known_state": "ACTIVE"}

            # Get wallet with row lock
            wallet_result = await db.execute(
                select(EntitlementWallet).where(
                    EntitlementWallet.tenant_id == tenant_id,
                    EntitlementWallet.member_id == member_id,
                    EntitlementWallet.entitlement_id == ent_def.id
                ).with_for_update()
            )
            wallet = wallet_result.scalars().first()

            if not wallet:
                return {"granted": False, "reason": "NO_WALLET", "last_known_state": "INACTIVE"}

            if ent_def.type == "COUNT":
                if wallet.remaining <= 0:
                    return {"granted": False, "reason": "ZERO_BALANCE", "last_known_state": "ACTIVE"}
                wallet.remaining -= 1
                wallet.consumed += 1

            # Log transaction
            tx = EntitlementTransaction(
                tenant_id=tenant_id,
                wallet_id=wallet.id,
                idempotency_key=idempotency_key,
                amount=1,
                action=action
            )
            db.add(tx)
            await db.commit()

            return {"granted": True, "last_known_state": "ACTIVE", "reason": None, "offline_ttl_hours": 24}

        except IntegrityError:
            await db.rollback()
            return {"granted": False, "reason": "CONCURRENCY_ERROR", "last_known_state": "ACTIVE"}
        except Exception:
            await db.rollback()
            raise

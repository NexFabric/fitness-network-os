import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access import AccessAttempt
from app.models.audit import AuditEvent
from app.models.retention import DataRetentionPolicy, DeletionMethod

logger = logging.getLogger("retention-service")


class DataRetentionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_policies_for_tenant(
        self, tenant_id: UUID
    ) -> list[DataRetentionPolicy]:
        """Fetch active data retention policies for a tenant."""
        result = await self.db.execute(
            select(DataRetentionPolicy).where(
                DataRetentionPolicy.tenant_id == tenant_id,
                DataRetentionPolicy.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def enforce_policies_for_tenant(self, tenant_id: UUID) -> dict[str, int]:
        """Enforce retention policies on tenant datasets according to legal policy rules."""
        policies = await self.get_policies_for_tenant(tenant_id)
        stats: dict[str, int] = {}
        now = datetime.now(UTC)

        for policy in policies:
            if not policy.retention_days or policy.retention_days <= 0:
                continue  # Indefinite retention requires explicit legal basis

            cutoff = now - timedelta(days=policy.retention_days)
            category = policy.data_category.lower().strip()
            affected = 0

            if category in {"access_attempts", "access_logs", "qr_scans"}:
                if policy.deletion_method == DeletionMethod.ANONYMIZE.value:
                    res = await self.db.execute(
                        update(AccessAttempt)
                        .where(
                            AccessAttempt.tenant_id == tenant_id,
                            AccessAttempt.timestamp < cutoff,
                            AccessAttempt.snapshot_data.is_not(None),
                        )
                        .values(snapshot_data=None, jti=None)
                    )
                    affected = int(getattr(res, "rowcount", 0))
                elif policy.deletion_method == DeletionMethod.DELETE.value:
                    res = await self.db.execute(
                        delete(AccessAttempt).where(
                            AccessAttempt.tenant_id == tenant_id,
                            AccessAttempt.timestamp < cutoff,
                        )
                    )
                    affected = int(getattr(res, "rowcount", 0))

            elif category in {"audit_logs", "audit_events"}:
                if policy.deletion_method == DeletionMethod.ANONYMIZE.value:
                    res = await self.db.execute(
                        update(AuditEvent)
                        .where(
                            AuditEvent.tenant_id == tenant_id,
                            AuditEvent.created_at < cutoff,
                            AuditEvent.new_state.is_not(None),
                        )
                        .values(new_state=None, old_state=None)
                    )
                    affected = int(getattr(res, "rowcount", 0))

            if affected > 0:
                logger.info(
                    f"Retention policy [{category}] enforced on tenant {tenant_id}: {affected} records {policy.deletion_method}"
                )
                stats[category] = affected

        if stats:
            audit = AuditEvent(
                tenant_id=tenant_id,
                action="data_retention.enforced",
                resource_type="data_retention_policy",
                resource_id=tenant_id,
                new_state=stats,
            )
            self.db.add(audit)
            await self.db.flush()

        return stats

import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.break_glass import BreakGlassSession, BreakGlassStatus


class BreakGlassService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        actor_id: UUID,
        target_tenant_id: UUID,
        reason: str,
        ticket_reference: str,
        duration_minutes: int = 30,
    ) -> BreakGlassSession:
        # Duration capped between 5 and 60 minutes
        duration_minutes = max(5, min(60, duration_minutes))
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=duration_minutes)

        session = BreakGlassSession(
            id=uuid.uuid4(),
            actor_id=actor_id,
            target_tenant_id=target_tenant_id,
            reason=reason,
            ticket_reference=ticket_reference,
            status=BreakGlassStatus.ACTIVE.value,
            granted_at=now,
            expires_at=expires_at,
        )
        self.db.add(session)

        audit = AuditEvent(
            id=uuid.uuid4(),
            tenant_id=target_tenant_id,
            user_id=actor_id,
            action="break_glass.session_created",
            resource_type="tenant",
            resource_id=target_tenant_id,
            new_state={
                "reason": reason,
                "ticket_reference": ticket_reference,
                "expires_at": expires_at.isoformat(),
            },
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def check_active_session(
        self, actor_id: UUID, tenant_id: UUID
    ) -> BreakGlassSession | None:
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(BreakGlassSession).where(
                BreakGlassSession.actor_id == actor_id,
                BreakGlassSession.target_tenant_id == tenant_id,
                BreakGlassSession.status == BreakGlassStatus.ACTIVE.value,
            )
        )
        session = result.scalars().first()

        if not session:
            return None

        if session.expires_at < now:
            session.status = BreakGlassStatus.EXPIRED.value
            await self.db.commit()
            return None

        return session

    async def revoke_session(
        self, session_id: UUID, actor_id: UUID
    ) -> BreakGlassSession | None:
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(BreakGlassSession).where(BreakGlassSession.id == session_id)
        )
        session = result.scalars().first()

        if session and session.status == BreakGlassStatus.ACTIVE.value:
            session.status = BreakGlassStatus.REVOKED.value
            session.revoked_at = now

            audit = AuditEvent(
                id=uuid.uuid4(),
                tenant_id=session.target_tenant_id,
                user_id=actor_id,
                action="break_glass.session_revoked",
                resource_type="break_glass_session",
                resource_id=session.id,
                new_state={"status": BreakGlassStatus.REVOKED.value},
            )
            self.db.add(audit)

            await self.db.commit()
            await self.db.refresh(session)

        return session

    async def expire_stale_sessions(self) -> int:
        now = datetime.now(UTC)

        result = await self.db.execute(
            update(BreakGlassSession)
            .where(
                BreakGlassSession.status == BreakGlassStatus.ACTIVE.value,
                BreakGlassSession.expires_at < now,
            )
            .values(status=BreakGlassStatus.EXPIRED.value)
        )
        await self.db.commit()
        return int(getattr(result, "rowcount", 0))

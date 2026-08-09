from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.membership import Membership

class EntitlementService:
    @staticmethod
    async def check_access(db: AsyncSession, member_id: UUID, action: str = "gym_access") -> dict:
        """
        Check if the member has access to the specified action based on their active membership's terms_snapshot.
        Includes logic for Offline TTL caching projection.
        """
        result = await db.execute(
            select(Membership).where(
                Membership.member_id == member_id,
                Membership.status == "ACTIVE"
            )
        )
        membership = result.scalars().first()

        if not membership:
            return {
                "granted": False,
                "reason": "NO_ACTIVE_MEMBERSHIP",
                "last_known_state": "INACTIVE"
            }

        terms = membership.terms_snapshot or {}
        
        # Determine if the specific action is allowed by terms
        action_allowed = terms.get(action, False)
        if not action_allowed:
            return {
                "granted": False,
                "reason": f"ACTION_DENIED_BY_TERMS",
                "last_known_state": "ACTIVE"
            }
            
        # Offline TTL projection
        offline_ttl = terms.get("offline_ttl_hours", 24)

        return {
            "granted": True,
            "reason": None,
            "last_known_state": "ACTIVE",
            "offline_ttl_hours": offline_ttl
        }

"""Phase 14 member core — profiles, tags, notes, consent (flush-only)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consent import ConsentDefinition, ConsentRecord
from app.models.member import Member, Note, Tag

ALLOWED_STATUSES = frozenset(
    {"LEAD", "PROSPECT", "ACTIVE", "INACTIVE", "SUSPENDED", "ARCHIVED"}
)
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "LEAD": frozenset({"PROSPECT", "ACTIVE", "ARCHIVED"}),
    "PROSPECT": frozenset({"ACTIVE", "INACTIVE", "ARCHIVED"}),
    "ACTIVE": frozenset({"INACTIVE", "SUSPENDED", "ARCHIVED"}),
    "INACTIVE": frozenset({"ACTIVE", "ARCHIVED"}),
    "SUSPENDED": frozenset({"ACTIVE", "INACTIVE", "ARCHIVED"}),
    "ARCHIVED": frozenset(),
}


class MemberService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_member(
        self,
        tenant_id: UUID,
        *,
        member_number: str,
        first_name: str,
        last_name: str,
        email: str | None = None,
        phone: str | None = None,
        status: str = "LEAD",
    ) -> Member:
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"invalid_status:{status}")
        member_number = member_number.strip()
        if not member_number:
            raise ValueError("member_number_required")
        if not first_name.strip() or not last_name.strip():
            raise ValueError("name_required")

        member = Member(
            id=uuid4(),
            tenant_id=tenant_id,
            member_number=member_number,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.strip().lower() if email else None,
            phone=phone.strip() if phone else None,
            status=status,
        )
        try:
            async with self.db.begin_nested():
                self.db.add(member)
                await self.db.flush()
        except IntegrityError as e:
            raise ValueError("member_number_conflict") from e
        return member

    async def get_member(self, tenant_id: UUID, member_id: UUID) -> Member | None:
        result = await self.db.execute(
            select(Member).where(Member.tenant_id == tenant_id, Member.id == member_id)
        )
        return result.scalars().first()

    async def list_members(
        self,
        tenant_id: UUID,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Member]:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        stmt = select(Member).where(Member.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(Member.status == status)
        stmt = stmt.order_by(Member.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_member(
        self,
        tenant_id: UUID,
        member_id: UUID,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> Member:
        member = await self.get_member(tenant_id, member_id)
        if member is None:
            raise ValueError("member_not_found")
        if first_name is not None:
            member.first_name = first_name.strip()
        if last_name is not None:
            member.last_name = last_name.strip()
        if email is not None:
            member.email = email.strip().lower() if email else None
        if phone is not None:
            member.phone = phone.strip() if phone else None
        await self.db.flush()
        return member

    async def set_status(
        self, tenant_id: UUID, member_id: UUID, new_status: str
    ) -> Member:
        if new_status not in ALLOWED_STATUSES:
            raise ValueError(f"invalid_status:{new_status}")
        member = await self.get_member(tenant_id, member_id)
        if member is None:
            raise ValueError("member_not_found")
        allowed = ALLOWED_TRANSITIONS.get(member.status, frozenset())
        if new_status != member.status and new_status not in allowed:
            raise ValueError(f"invalid_transition:{member.status}->{new_status}")
        member.status = new_status
        await self.db.flush()
        return member

    # ----- tags / notes -----
    async def add_tag(self, tenant_id: UUID, member_id: UUID, name: str) -> Tag:
        member = await self.get_member(tenant_id, member_id)
        if member is None:
            raise ValueError("member_not_found")
        name = name.strip()
        if not name:
            raise ValueError("tag_name_required")
        existing = await self.db.execute(
            select(Tag).where(
                Tag.tenant_id == tenant_id,
                Tag.member_id == member_id,
                Tag.name == name,
            )
        )
        tag = existing.scalars().first()
        if tag:
            return tag
        tag = Tag(tenant_id=tenant_id, member_id=member_id, name=name)
        self.db.add(tag)
        await self.db.flush()
        return tag

    async def list_tags(self, tenant_id: UUID, member_id: UUID) -> list[Tag]:
        result = await self.db.execute(
            select(Tag).where(Tag.tenant_id == tenant_id, Tag.member_id == member_id)
        )
        return list(result.scalars().all())

    async def add_note(self, tenant_id: UUID, member_id: UUID, content: str) -> Note:
        member = await self.get_member(tenant_id, member_id)
        if member is None:
            raise ValueError("member_not_found")
        content = content.strip()
        if not content:
            raise ValueError("note_content_required")
        note = Note(tenant_id=tenant_id, member_id=member_id, content=content)
        self.db.add(note)
        await self.db.flush()
        return note

    async def list_notes(self, tenant_id: UUID, member_id: UUID) -> list[Note]:
        result = await self.db.execute(
            select(Note)
            .where(Note.tenant_id == tenant_id, Note.member_id == member_id)
            .order_by(Note.created_at.desc())
        )
        return list(result.scalars().all())

    # ----- consent -----
    async def ensure_consent_definition(
        self,
        tenant_id: UUID,
        *,
        name: str,
        consent_type: str,
        description: str | None = None,
    ) -> ConsentDefinition:
        result = await self.db.execute(
            select(ConsentDefinition).where(
                ConsentDefinition.tenant_id == tenant_id,
                ConsentDefinition.consent_type == consent_type,
            )
        )
        existing = result.scalars().first()
        if existing:
            return existing
        definition = ConsentDefinition(
            tenant_id=tenant_id,
            name=name,
            consent_type=consent_type,
            description=description,
        )
        self.db.add(definition)
        await self.db.flush()
        return definition

    async def record_consent(
        self,
        tenant_id: UUID,
        member_id: UUID,
        *,
        consent_type: str,
        document_version: str,
        status: str = "GIVEN",
        source: str | None = None,
        ip_address: str | None = None,
    ) -> ConsentRecord:
        member = await self.get_member(tenant_id, member_id)
        if member is None:
            raise ValueError("member_not_found")
        if status not in {"GIVEN", "WITHDRAWN", "DENIED"}:
            raise ValueError("invalid_consent_status")
        now = datetime.now(UTC)
        record = ConsentRecord(
            tenant_id=tenant_id,
            member_id=member_id,
            consent_type=consent_type,
            document_version=document_version,
            status=status,
            given_at=now if status == "GIVEN" else None,
            withdrawn_at=now if status == "WITHDRAWN" else None,
            source=source,
            ip_address=ip_address,
        )
        self.db.add(record)
        await self.db.flush()
        return record

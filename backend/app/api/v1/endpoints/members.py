from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_tenant_id
from app.core.authorization import AuthorizationService, SecurityException
from app.models.user import User
from app.services.member import MemberService

router = APIRouter()


def _require(user: User, tenant_id: UUID, permission: str) -> None:
    if not AuthorizationService.is_authorized(
        user=user, permission=permission, resource_tenant_id=tenant_id
    ):
        raise SecurityException()


class MemberCreate(BaseModel):
    member_number: str = Field(min_length=1, max_length=64)
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    email: str | None = None
    phone: str | None = None
    status: str = "LEAD"


class MemberUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None


class MemberStatusUpdate(BaseModel):
    status: str


class MemberResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    member_number: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    status: str
    user_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class TagResponse(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class NoteResponse(BaseModel):
    id: UUID
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConsentCreate(BaseModel):
    consent_type: str
    document_version: str
    status: str = "GIVEN"
    source: str | None = None


class ConsentResponse(BaseModel):
    id: UUID
    consent_type: str
    document_version: str
    status: str
    given_at: datetime | None
    withdrawn_at: datetime | None

    model_config = {"from_attributes": True}


@router.post("", response_model=MemberResponse, status_code=201)
async def create_member(
    body: MemberCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:write")
    svc = MemberService(db)
    try:
        member = await svc.create_member(
            tenant_id,
            member_number=body.member_number,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            phone=body.phone,
            status=body.status,
        )
        await db.commit()
        await db.refresh(member)
        return member
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_model=list[MemberResponse])
async def list_members(
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:read")
    svc = MemberService(db)
    return await svc.list_members(
        tenant_id, status=status, limit=limit, offset=offset
    )


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:read")
    svc = MemberService(db)
    member = await svc.get_member(tenant_id, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="member_not_found")
    return member


@router.patch("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: UUID,
    body: MemberUpdate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:write")
    svc = MemberService(db)
    try:
        member = await svc.update_member(
            tenant_id,
            member_id,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            phone=body.phone,
        )
        await db.commit()
        await db.refresh(member)
        return member
    except ValueError as e:
        code = 404 if str(e) == "member_not_found" else 400
        raise HTTPException(status_code=code, detail=str(e)) from e


@router.post("/{member_id}/status", response_model=MemberResponse)
async def set_member_status(
    member_id: UUID,
    body: MemberStatusUpdate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:write")
    svc = MemberService(db)
    try:
        member = await svc.set_status(tenant_id, member_id, body.status)
        await db.commit()
        await db.refresh(member)
        return member
    except ValueError as e:
        code = 404 if str(e) == "member_not_found" else 400
        raise HTTPException(status_code=code, detail=str(e)) from e


@router.post("/{member_id}/tags", response_model=TagResponse, status_code=201)
async def add_tag(
    member_id: UUID,
    body: TagCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:write")
    svc = MemberService(db)
    try:
        tag = await svc.add_tag(tenant_id, member_id, body.name)
        await db.commit()
        await db.refresh(tag)
        return tag
    except ValueError as e:
        code = 404 if str(e) == "member_not_found" else 400
        raise HTTPException(status_code=code, detail=str(e)) from e


@router.get("/{member_id}/tags", response_model=list[TagResponse])
async def list_tags(
    member_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:read")
    return await MemberService(db).list_tags(tenant_id, member_id)


@router.post("/{member_id}/notes", response_model=NoteResponse, status_code=201)
async def add_note(
    member_id: UUID,
    body: NoteCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:write")
    svc = MemberService(db)
    try:
        note = await svc.add_note(tenant_id, member_id, body.content)
        await db.commit()
        await db.refresh(note)
        return note
    except ValueError as e:
        code = 404 if str(e) == "member_not_found" else 400
        raise HTTPException(status_code=code, detail=str(e)) from e


@router.get("/{member_id}/notes", response_model=list[NoteResponse])
async def list_notes(
    member_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:read")
    return await MemberService(db).list_notes(tenant_id, member_id)


@router.post(
    "/{member_id}/consents", response_model=ConsentResponse, status_code=201
)
async def record_consent(
    member_id: UUID,
    body: ConsentCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _require(current_user, tenant_id, "members:write")
    svc = MemberService(db)
    try:
        await svc.ensure_consent_definition(
            tenant_id, name=body.consent_type, consent_type=body.consent_type
        )
        record = await svc.record_consent(
            tenant_id,
            member_id,
            consent_type=body.consent_type,
            document_version=body.document_version,
            status=body.status,
            source=body.source,
        )
        await db.commit()
        await db.refresh(record)
        return record
    except ValueError as e:
        code = 404 if str(e) == "member_not_found" else 400
        raise HTTPException(status_code=code, detail=str(e)) from e

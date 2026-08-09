from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.entitlement import EntitlementService


@pytest.mark.asyncio
async def test_check_access_granted():
    member_id = uuid4()
    mock_db = AsyncMock()
    
    mock_membership = AsyncMock()
    mock_membership.member_id = member_id
    mock_membership.status = "ACTIVE"
    mock_membership.terms_snapshot = {"gym_access": True, "offline_ttl_hours": 12}
    
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = mock_membership
    
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    
    mock_db.execute.return_value = mock_result
    
    res = await EntitlementService.check_access(mock_db, member_id, action="gym_access")
    assert res["granted"] is True
    assert res["offline_ttl_hours"] == 12

@pytest.mark.asyncio
async def test_check_access_denied_no_membership():
    member_id = uuid4()
    mock_db = AsyncMock()
    
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    
    mock_db.execute.return_value = mock_result
    
    res = await EntitlementService.check_access(mock_db, member_id, action="gym_access")
    assert res["granted"] is False
    assert res["reason"] == "NO_ACTIVE_MEMBERSHIP"
    
@pytest.mark.asyncio
async def test_check_access_denied_by_terms():
    member_id = uuid4()
    mock_db = AsyncMock()
    
    mock_membership = AsyncMock()
    mock_membership.member_id = member_id
    mock_membership.status = "ACTIVE"
    mock_membership.terms_snapshot = {"gym_access": False}
    
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = mock_membership
    
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    
    mock_db.execute.return_value = mock_result
    
    res = await EntitlementService.check_access(mock_db, member_id, action="gym_access")
    assert res["granted"] is False
    assert res["reason"] == "ACTION_DENIED_BY_TERMS"

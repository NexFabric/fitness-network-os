"""Phase 15.5B — RBAC least-privilege matrix (YAML + AuthorizationService)."""

from pathlib import Path
from uuid import uuid4

import yaml

from app.core.authorization import AuthorizationService
from app.models.rbac import Permission, Role, UserRole
from app.models.user import User


def _load_matrix() -> dict:
    path = Path(__file__).resolve().parents[2] / "permissions.yml"
    return yaml.safe_load(path.read_text())


def test_yaml_member_lacks_staff_directory_and_staff_issue():
    data = _load_matrix()
    member_perms = set(data["roles"]["MEMBER"]["permissions"])
    assert "members:read" not in member_perms
    assert "access:issue" not in member_perms
    assert "access:issue:self" in member_perms
    # Phase 15.5C: no tenant-wide self-domain grants (BOLA)
    assert "memberships:read" not in member_perms
    assert "checkins:read" not in member_perms
    assert "checkins:write" not in member_perms
    assert "entitlements:read" not in member_perms
    assert "entitlements:check" not in member_perms
    assert "memberships:read:self" in member_perms
    assert "entitlements:read:self" in member_perms
    assert "entitlements:check:self" in member_perms
    assert "checkins:read:self" in member_perms
    assert "checkins:write:self" in member_perms
    assert "profile:read" in member_perms


def test_yaml_staff_keep_members_read_and_access_issue():
    data = _load_matrix()
    for role in ("TRAINER", "FRONT_DESK", "GYM_MANAGER", "GYM_ADMIN", "GYM_OWNER"):
        perms = set(data["roles"][role]["permissions"])
        assert "members:read" in perms, role
    for role in ("FRONT_DESK", "GYM_MANAGER", "GYM_ADMIN", "GYM_OWNER"):
        perms = set(data["roles"][role]["permissions"])
        assert "access:issue" in perms, role


def test_yaml_tenant_roles_lack_outbox_dispatch():
    data = _load_matrix()
    tenant_roles = (
        "GYM_OWNER",
        "GYM_ADMIN",
        "GYM_MANAGER",
        "ACCOUNTANT",
        "FRONT_DESK",
        "TRAINER",
        "MEMBER",
    )
    for role in tenant_roles:
        perms = set(data["roles"][role]["permissions"])
        assert "outbox:dispatch" not in perms, role
        # Phase 15.5C: no tenant generic event ingress
        assert "outbox:write" not in perms, role
        assert "inbox:write" not in perms, role
    # Permission still defined for platform/worker / future service principals
    perm_ids = {p["id"] for p in data["permissions"]}
    assert "outbox:dispatch" in perm_ids
    assert "outbox:write" in perm_ids
    assert "access:issue:self" in perm_ids
    assert "entitlements:check:self" in perm_ids


def _user_with_role(role_name: str, perm_names: list[str], tenant_id):
    user = User(
        id=uuid4(),
        email=f"{role_name.lower()}@test.com",
        hashed_password="x",
        is_superuser=False,
    )
    perms = [Permission(id=uuid4(), name=n) for n in perm_names]
    role = Role(id=uuid4(), name=role_name, permissions=perms)
    user.user_roles = [
        UserRole(
            id=uuid4(),
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_id,
            role=role,
        )
    ]
    return user


def test_authorization_member_denied_members_read_and_access_issue():
    tenant_id = uuid4()
    data = _load_matrix()
    member_perms = list(data["roles"]["MEMBER"]["permissions"])
    user = _user_with_role("MEMBER", member_perms, tenant_id)

    assert (
        AuthorizationService.evaluate_permissions(
            user, ["members:read"], tenant_id=tenant_id
        )
        is False
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["access:issue"], tenant_id=tenant_id
        )
        is False
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["access:issue:self"], tenant_id=tenant_id
        )
        is True
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["memberships:read"], tenant_id=tenant_id
        )
        is False
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["entitlements:check"], tenant_id=tenant_id
        )
        is False
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["entitlements:check:self"], tenant_id=tenant_id
        )
        is True
    )


def test_authorization_member_is_authorized_negative_for_members_read():
    tenant_id = uuid4()
    data = _load_matrix()
    user = _user_with_role(
        "MEMBER", list(data["roles"]["MEMBER"]["permissions"]), tenant_id
    )
    assert (
        AuthorizationService.is_authorized(
            user, permission="members:read", resource_tenant_id=tenant_id
        )
        is False
    )


def test_authorization_gym_owner_denied_outbox_dispatch():
    tenant_id = uuid4()
    data = _load_matrix()
    user = _user_with_role(
        "GYM_OWNER", list(data["roles"]["GYM_OWNER"]["permissions"]), tenant_id
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["outbox:dispatch"], tenant_id=tenant_id
        )
        is False
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["outbox:write"], tenant_id=tenant_id
        )
        is False
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["inbox:write"], tenant_id=tenant_id
        )
        is False
    )


def test_authorization_front_desk_keeps_access_issue():
    tenant_id = uuid4()
    data = _load_matrix()
    user = _user_with_role(
        "FRONT_DESK", list(data["roles"]["FRONT_DESK"]["permissions"]), tenant_id
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["access:issue"], tenant_id=tenant_id
        )
        is True
    )
    assert (
        AuthorizationService.evaluate_permissions(
            user, ["members:read"], tenant_id=tenant_id
        )
        is True
    )


def test_yaml_role_permissions_all_defined():
    data = _load_matrix()
    valid = {p["id"] for p in data["permissions"]}
    for role_name, role_data in data["roles"].items():
        for perm in role_data.get("permissions") or []:
            assert perm in valid, f"{role_name} has invalid {perm}"

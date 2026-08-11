from uuid import uuid4

from app.core.authorization import AuthorizationService, Scope
from app.models.rbac import Permission, Role, UserRole
from app.models.user import User


def test_authorization_superuser():
    user = User(id=uuid4(), email="admin@test.com", is_superuser=True)
    assert AuthorizationService.evaluate_permissions(user, ["some:permission"]) == True
    assert AuthorizationService.evaluate_scope(user, Scope.PLATFORM) == True

def test_authorization_evaluate_permissions():
    user = User(id=uuid4(), email="user@test.com", is_superuser=False)
    tenant_id = uuid4()
    
    perm_read = Permission(id=uuid4(), name="users:read")
    perm_write = Permission(id=uuid4(), name="users:write")
    
    role = Role(id=uuid4(), name="admin", permissions=[perm_read, perm_write])
    
    user_role = UserRole(id=uuid4(), user_id=user.id, role_id=role.id, tenant_id=tenant_id, role=role)
    user.user_roles = [user_role]
    
    assert AuthorizationService.evaluate_permissions(user, ["users:read"], tenant_id=tenant_id) == True
    assert AuthorizationService.evaluate_permissions(user, ["users:read", "users:write"], tenant_id=tenant_id) == True
    
    other_tenant_id = uuid4()
    assert AuthorizationService.evaluate_permissions(user, ["users:read"], tenant_id=other_tenant_id) == False
    
    assert AuthorizationService.evaluate_permissions(user, ["users:delete"], tenant_id=tenant_id) == False

def test_authorization_evaluate_scope_self():
    user = User(id=uuid4(), email="user@test.com", is_superuser=False)
    
    assert AuthorizationService.evaluate_scope(user, Scope.SELF, resource_owner_id=user.id) == True
    assert AuthorizationService.evaluate_scope(user, Scope.SELF, resource_owner_id=uuid4()) == False

def test_authorization_evaluate_scope_assigned():
    user = User(id=uuid4(), email="user@test.com", is_superuser=False)
    client1_id = uuid4()
    client2_id = uuid4()
    
    assert AuthorizationService.evaluate_scope(user, Scope.ASSIGNED, assigned_user_ids=[user.id, client1_id]) == True
    assert AuthorizationService.evaluate_scope(user, Scope.ASSIGNED, assigned_user_ids=[client1_id, client2_id]) == False

def test_authorization_evaluate_scope_tenant():
    user = User(id=uuid4(), email="user@test.com", is_superuser=False)
    tenant_id = uuid4()
    
    user_role = UserRole(id=uuid4(), user_id=user.id, role_id=uuid4(), tenant_id=tenant_id)
    user.user_roles = [user_role]
    
    assert AuthorizationService.evaluate_scope(user, Scope.TENANT, resource_tenant_id=tenant_id) == True
    assert AuthorizationService.evaluate_scope(user, Scope.TENANT, resource_tenant_id=uuid4()) == False

def test_authorization_evaluate_scope_platform():
    user = User(id=uuid4(), email="user@test.com", is_superuser=False)
    
    role = Role(id=uuid4(), name="PLATFORM_SUPER_ADMIN")
    user_role = UserRole(id=uuid4(), user_id=user.id, role_id=role.id, tenant_id=None, organization_id=None, role=role)
    user.user_roles = [user_role]
    
    assert AuthorizationService.evaluate_scope(user, Scope.PLATFORM) == True

def test_authorization_evaluate_scope_location():
    user = User(id=uuid4(), email="user@test.com", is_superuser=False)
    tenant_id = uuid4()
    
    user_role = UserRole(id=uuid4(), user_id=user.id, role_id=uuid4(), tenant_id=tenant_id)
    user.user_roles = [user_role]
    
    assert AuthorizationService.evaluate_scope(user, Scope.LOCATION, resource_tenant_id=tenant_id) == True
    assert AuthorizationService.evaluate_scope(user, Scope.LOCATION, resource_tenant_id=uuid4()) == False

def test_authorization_evaluate_scope_federation_aggregate():
    user = User(id=uuid4(), email="user@test.com", is_superuser=False)
    org_id = uuid4()
    
    role = Role(id=uuid4(), name="FEDERATION_ADMIN")
    user_role = UserRole(id=uuid4(), user_id=user.id, role_id=role.id, tenant_id=None, organization_id=org_id, role=role)
    user.user_roles = [user_role]
    
    assert AuthorizationService.evaluate_scope(user, Scope.FEDERATION_AGGREGATE, resource_organization_id=org_id) == True
    assert AuthorizationService.evaluate_scope(user, Scope.FEDERATION_AGGREGATE, resource_organization_id=uuid4()) == False


def test_member_role_cannot_cross_tenant_on_own_resources():
    """A MEMBER grant in tenant A must not authorize the same user in tenant B.

    Regression: is_authorized had a MEMBER fallback that returned True on
    resource_owner_id == user.id alone, skipping the tenant check entirely.
    """
    user = User(id=uuid4(), email="member@test.com", is_superuser=False)
    tenant_a = uuid4()
    tenant_b = uuid4()

    perm = Permission(id=uuid4(), name="profile:read")
    role = Role(id=uuid4(), name="MEMBER", permissions=[perm])
    user.user_roles = [
        UserRole(
            id=uuid4(),
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_a,
            role=role,
        )
    ]

    assert (
        AuthorizationService.is_authorized(
            user=user,
            permission="profile:read",
            resource_tenant_id=tenant_a,
            resource_owner_id=user.id,
        )
        is True
    )

    assert (
        AuthorizationService.is_authorized(
            user=user,
            permission="profile:read",
            resource_tenant_id=tenant_b,
            resource_owner_id=user.id,
        )
        is False
    )

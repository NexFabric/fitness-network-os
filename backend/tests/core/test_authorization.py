import pytest
from uuid import uuid4
from app.models.user import User
from app.models.rbac import UserRole, Role, Permission
from app.core.authorization import AuthorizationService, Scope

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
    
    user_role = UserRole(id=uuid4(), user_id=user.id, role_id=uuid4(), tenant_id=None)
    user.user_roles = [user_role]
    
    assert AuthorizationService.evaluate_scope(user, Scope.PLATFORM) == True

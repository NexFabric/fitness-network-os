from enum import Enum
from uuid import UUID

from fastapi import HTTPException, status

from app.models.user import User


class SecurityException(HTTPException):
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class Scope(Enum):
    SELF = "SELF"             # Access to own resources
    ASSIGNED = "ASSIGNED"     # Access to resources assigned to user (e.g. trainer's clients)
    LOCATION = "LOCATION"     # Access to all resources in a specific branch/location (tenant)
    TENANT = "TENANT"         # Access to all resources in the organization/tenant
    FEDERATION_AGGREGATE = "FEDERATION_AGGREGATE"  # Access across federated tenants
    PLATFORM = "PLATFORM"     # Access to all resources across the platform

class DefaultRole(Enum):
    PLATFORM_SUPER_ADMIN = "PLATFORM_SUPER_ADMIN"
    FEDERATION_ADMIN = "FEDERATION_ADMIN"
    FEDERATION_ANALYST = "FEDERATION_ANALYST"
    FEDERATION_SUPPORT = "FEDERATION_SUPPORT"
    GYM_OWNER = "GYM_OWNER"
    GYM_ADMIN = "GYM_ADMIN"
    GYM_MANAGER = "GYM_MANAGER"
    ACCOUNTANT = "ACCOUNTANT"
    FRONT_DESK = "FRONT_DESK"
    TRAINER = "TRAINER"
    MEMBER = "MEMBER"

class DefaultPermission(Enum):
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    MEMBERSHIPS_READ = "memberships:read"
    MEMBERSHIPS_WRITE = "memberships:write"
    TENANT_READ = "tenant:read"
    TENANT_WRITE = "tenant:write"

class AuthorizationService:
    @staticmethod
    def evaluate_permissions(
        user: User, 
        required_permissions: list[str], 
        tenant_id: UUID | None = None
    ) -> bool:
        if user.is_superuser:
            return True
            
        user_permissions = set()
        
        for user_role in user.user_roles:
            # If a tenant_id is requested, ONLY consider roles assigned to that specific tenant
            if tenant_id is not None:
                if user_role.tenant_id != tenant_id:
                    continue
            else:
                # If no tenant is requested, we might be checking global permissions, but we shouldn't
                # leak tenant-scoped roles into global evaluation. (We'll handle this in a combined method).
                pass
                
            if user_role.role and user_role.role.permissions:
                for permission in user_role.role.permissions:
                    user_permissions.add(permission.name)
                    
        for req_perm in required_permissions:
            if req_perm not in user_permissions:
                return False
                
        return True

    @staticmethod
    def evaluate_scope(
        user: User, 
        scope: Scope, 
        resource_owner_id: UUID | None = None, 
        resource_tenant_id: UUID | None = None, 
        current_tenant_id: UUID | None = None,
        assigned_user_ids: list[UUID] | None = None,
        resource_organization_id: UUID | None = None,
    ) -> bool:
        if user.is_superuser:
            return True
            
        if scope == Scope.SELF:
            if resource_owner_id is not None and resource_owner_id == user.id:
                return True
            return False
            
        elif scope == Scope.ASSIGNED:
            if assigned_user_ids is not None and user.id in assigned_user_ids:
                return True
            return False
            
        elif scope in (Scope.LOCATION, Scope.TENANT):
            target_tenant = resource_tenant_id or current_tenant_id
            if target_tenant is not None:
                has_tenant_access = any(
                    ur.tenant_id == target_tenant for ur in user.user_roles
                )
                if has_tenant_access:
                    return True
            return False
            
        elif scope == Scope.FEDERATION_AGGREGATE:
            if resource_organization_id is not None:
                has_org_access = any(
                    ur.organization_id == resource_organization_id 
                    and ur.role.name in [DefaultRole.FEDERATION_ADMIN.value, DefaultRole.FEDERATION_ANALYST.value, DefaultRole.FEDERATION_SUPPORT.value]
                    for ur in user.user_roles
                )
                if has_org_access:
                    return True
            return False
            
        elif scope == Scope.PLATFORM:
            has_platform_access = any(
                ur.tenant_id is None and ur.organization_id is None
                and ur.role.name == DefaultRole.PLATFORM_SUPER_ADMIN.value
                for ur in user.user_roles
            )
            return has_platform_access
            
        return False

    @staticmethod
    def is_authorized(
        user: User,
        permission: str,
        resource_tenant_id: UUID | None = None,
        resource_organization_id: UUID | None = None,
        resource_owner_id: UUID | None = None,
    ) -> bool:
        """
        Unified authorization check. 
        Evaluates permission, assignment scope, and resource context together.
        """
        if user.is_superuser:
            return True
            
        for ur in user.user_roles:
            role = ur.role
            if not role or not role.permissions:
                continue
                
            has_perm = any(p.name == permission or p.name == "*" for p in role.permissions)
            if not has_perm:
                continue
                
            # If the role has the permission, check if the scope of the assignment covers the resource
            
            # 1. Platform-level assignment
            if ur.tenant_id is None and ur.organization_id is None:
                if role.name == DefaultRole.PLATFORM_SUPER_ADMIN.value:
                    return True # Platform super admin can do anything anywhere
                    
            # 2. Federation-level assignment
            elif ur.organization_id is not None and ur.tenant_id is None:
                if role.name in [DefaultRole.FEDERATION_ADMIN.value, DefaultRole.FEDERATION_ANALYST.value, DefaultRole.FEDERATION_SUPPORT.value]:
                    if resource_organization_id and ur.organization_id == resource_organization_id:
                        return True
                    # If checking a tenant, does the tenant belong to this org? 
                    # We would need tenant.organization_id here, but without it, we assume 
                    # caller passes resource_organization_id if they want federation check.
                        
            # 3. Tenant-level assignment
            elif ur.tenant_id is not None:
                if resource_tenant_id and ur.tenant_id == resource_tenant_id:
                    return True
                    
                # Self access (e.g. Member accessing own profile)
                if role.name == DefaultRole.MEMBER.value and resource_owner_id == user.id:
                    return True

        return False

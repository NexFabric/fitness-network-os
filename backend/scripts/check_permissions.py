#!/usr/bin/env python3
import sys
from pathlib import Path

import yaml

# A basic script to validate that all permissions listed under roles
# actually exist in the permissions list.

def main():
    root_dir = Path(__file__).resolve().parent.parent
    yaml_path = root_dir / "permissions.yml"

    if not yaml_path.exists():
        print(f"Error: permissions.yml not found at {yaml_path}", file=sys.stderr)
        sys.exit(1)

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    permissions_list = data.get("permissions", [])
    valid_permission_ids = {p["id"] for p in permissions_list}
    
    roles_dict = data.get("roles", {})
    
    REQUIRED_ROLES = {
        "PLATFORM_SUPER_ADMIN",
        "FEDERATION_ADMIN",
        "FEDERATION_ANALYST",
        "FEDERATION_SUPPORT",
        "GYM_OWNER",
        "GYM_ADMIN",
        "GYM_MANAGER",
        "ACCOUNTANT",
        "FRONT_DESK",
        "TRAINER",
        "MEMBER",
    }
    
    has_error = False
    
    # Check for missing roles
    for req_role in REQUIRED_ROLES:
        if req_role not in roles_dict:
            print(f"Error: Required canonical role '{req_role}' is missing from permissions.yml")
            has_error = True

    for role_name, role_data in roles_dict.items():
        if role_name not in REQUIRED_ROLES:
            print(f"Error: Unknown role '{role_name}' found in permissions.yml")
            has_error = True
        role_permissions = role_data.get("permissions", [])
        for perm in role_permissions:
            if perm not in valid_permission_ids:
                print(f"Error: Role '{role_name}' has invalid permission '{perm}'")
                has_error = True

    if has_error:
        print("Permission validation failed.")
        sys.exit(1)
        
    print("Permission matrix is valid.")
    sys.exit(0)

if __name__ == "__main__":
    main()

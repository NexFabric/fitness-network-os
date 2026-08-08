#!/usr/bin/env python3
import sys
import yaml
from pathlib import Path

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
    
    has_error = False
    
    for role_name, role_data in roles_dict.items():
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

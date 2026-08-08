#!/usr/bin/env python3
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.base import Base, TenantMixin
from app.models import *  # ensure all models are loaded in Base.metadata

def main():
    errors = []
    
    # Check all registered mappers in SQLAlchemy metadata
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        # If the class inherits from TenantMixin, it must have tenant_id
        if issubclass(cls, TenantMixin):
            if not hasattr(cls, "tenant_id"):
                errors.append(f"Model {cls.__name__} inherits from TenantMixin but lacks tenant_id definition.")
            elif "tenant_id" not in cls.__table__.columns:
                errors.append(f"Table {cls.__tablename__} lacks tenant_id column despite TenantMixin.")
    
    if errors:
        print("Tenancy violations found:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
        
    print("All tenant models conform to tenancy rules.")

if __name__ == "__main__":
    main()

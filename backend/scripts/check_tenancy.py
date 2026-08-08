#!/usr/bin/env python3
import asyncio
import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text

from app.db.base import Base, TenantMixin
from app.db.session import engine
from app.models import *  # ensure all models are loaded in Base.metadata


async def check_db_rls(errors, table_name):
    async with engine.connect() as conn:
        # Check pg_class
        query = f"""
        SELECT relrowsecurity, relforcerowsecurity 
        FROM pg_class 
        WHERE relname = '{table_name}'
        """
        res = await conn.execute(text(query))
        row = res.fetchone()
        if not row:
            errors.append(f"DB Error: Table {table_name} does not exist in DB.")
            return
        if not row[0]:
            errors.append(f"DB Error: Table {table_name} does NOT have RLS enabled (relrowsecurity=False).")
        if not row[1]:
            errors.append(f"DB Error: Table {table_name} does NOT have FORCE RLS enabled (relforcerowsecurity=False).")
        
        # Check pg_policies
        query2 = f"""
        SELECT cmd, qual, with_check 
        FROM pg_policies 
        WHERE tablename = '{table_name}'
        """
        res2 = await conn.execute(text(query2))
        policies = res2.fetchall()
        if not policies:
            errors.append(f"DB Error: Table {table_name} has NO RLS policies defined.")
        else:
            has_using = False
            has_with_check = False
            for p in policies:
                if p[1] is not None and "app.current_tenant_id" in p[1]:
                    has_using = True
                if p[2] is not None and "app.current_tenant_id" in p[2]:
                    has_with_check = True
                if p[0] == 'ALL':
                    if p[1] is not None and "app.current_tenant_id" in p[1]:
                        has_using = True
                    if p[2] is None and p[1] is not None and "app.current_tenant_id" in p[1]:
                        has_with_check = True
            
            if not has_using:
                errors.append(f"DB Error: Table {table_name} lacks USING policy with app.current_tenant_id.")
            if not has_with_check:
                errors.append(f"DB Error: Table {table_name} lacks WITH CHECK policy with app.current_tenant_id.")

async def main_async():
    static_only = "--static" in sys.argv
    errors = []
    
    # Identify all tenant-owned models
    tenant_models = {}
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if issubclass(cls, TenantMixin):
            tenant_models[cls.__tablename__] = cls

    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if not issubclass(cls, TenantMixin):
            continue

        table_name = cls.__tablename__
        
        # 1. tenant_id NOT NULL
        tenant_col = cls.__table__.columns.get("tenant_id")
        if tenant_col is None:
            errors.append(f"Model {cls.__name__} lacks tenant_id column.")
        elif tenant_col.nullable:
            errors.append(f"Model {cls.__name__} tenant_id column is nullable. MUST BE NOT NULL.")
            
        # 2. UNIQUE(tenant_id, id)
        has_unique = False
        for const in cls.__table__.constraints:
            if type(const).__name__ in ("UniqueConstraint", "PrimaryKeyConstraint"):
                col_names = [c.name for c in const.columns]
                if "tenant_id" in col_names and "id" in col_names:
                    has_unique = True
                    break
        if not has_unique:
            errors.append(f"Model {cls.__name__} must have a UniqueConstraint or PrimaryKeyConstraint on (tenant_id, id) for composite FK safety.")
            
        # 3. Composite Tenant FKs
        for fk in cls.__table__.foreign_key_constraints:
            target_table = fk.elements[0].column.table.name
            if target_table in tenant_models:
                source_cols = [e.parent.name for e in fk.elements]
                target_cols = [e.column.name for e in fk.elements]
                if "tenant_id" not in source_cols or "tenant_id" not in target_cols:
                    errors.append(f"Model {cls.__name__} has a non-composite FK to {target_table}. MUST include tenant_id in the constraint.")
                else:
                    idx = source_cols.index("tenant_id")
                    if target_cols[idx] != "tenant_id":
                         errors.append(f"Model {cls.__name__} composite FK to {target_table} maps tenant_id to something else.")


        # 5. tenant_id Index
        has_index = False
        tenant_col = cls.__table__.columns.get("tenant_id")
        if tenant_col is not None and tenant_col.index:
            has_index = True
            
        if not has_index:
            for index in cls.__table__.indexes:
                col_names = [c.name for c in index.columns]
                if col_names and col_names[0] == "tenant_id":
                    has_index = True
                    break
        
        if not has_index:
            for const in cls.__table__.constraints:
                if type(const).__name__ in ("UniqueConstraint", "PrimaryKeyConstraint"):
                    col_names = [c.name for c in const.columns]
                    if col_names and col_names[0] == "tenant_id":
                        has_index = True
                        break
                        
        if not has_index:
            errors.append(f"Model {cls.__name__} missing an index starting with tenant_id.")

        # 4. RLS enabled in DB
        if not static_only:
            await check_db_rls(errors, table_name)
    
    if errors:
        print("Tenancy violations found:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
        
    print("All tenant models conform to tenancy rules.")

if __name__ == "__main__":
    asyncio.run(main_async())

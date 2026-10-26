from alembic import op


def enable_rls(table_name: str, tenant_column: str = "tenant_id"):
    """
    Helper function to enable RLS on a tenant-owned table.
    Should be called inside alembic upgrade() functions.
    """
    policy_name = f"{table_name}_tenant_isolation_policy"

    # 1. Enable RLS
    op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")

    # 2. Create Policy (checks current_setting)
    # The 'true' argument to current_setting prevents it from throwing an error if missing, returning NULL instead.
    op.execute(f"""
        CREATE POLICY {policy_name} ON {table_name}
        FOR ALL
        USING ({tenant_column} = nullif(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK ({tenant_column} = nullif(current_setting('app.current_tenant_id', true), '')::uuid);
    """)

    # 3. Force RLS for table owner (prevents bypass by superusers acting as app)
    op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;")


def disable_rls(table_name: str):
    """
    Helper function to disable RLS.
    Should be called inside alembic downgrade() functions.
    """
    policy_name = f"{table_name}_tenant_isolation_policy"
    op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table_name};")
    op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;")

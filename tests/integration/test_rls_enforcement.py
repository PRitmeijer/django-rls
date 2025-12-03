"""
Integration tests for RLS enforcement at the database level.

These tests verify that:
1. The middleware correctly sets PostgreSQL session variables
2. RLS policies filter database queries correctly (PostgreSQL only)
3. The end-to-end flow works as expected (makemigrations -> migrate -> query)

Note: All tests use PostgreSQL since RLS is PostgreSQL-only.
Start PostgreSQL with 'docker-compose up -d' or 'task postgresql:up' before running tests.
"""
import os
import pytest
from django.db import connection
from django.test import RequestFactory
from django.core.management import call_command
from django.apps import apps
from django.contrib.auth.models import AnonymousUser
from django_rls.middleware import RLSMiddleware
from django_rls.settings_type import DjangoRLSSettings
from django_rls.constants import RlsWildcard
from testproject.app.models import (
    TenantModel, MixedModel, UserModel, NoRLSModel,
    UUIDTenantModel, UUIDMixedModel
)


# Fixtures are now in conftest.py


@pytest.mark.django_db
def test_middleware_sets_session_variables(middleware, rls_settings, settings):
    """Test that middleware actually sets session variables in the database."""
    settings.DJANGO_RLS = rls_settings
    
    # Create a mock request with tenant_id and user_id
    factory = RequestFactory()
    request = factory.get("/")
    
    # Mock resolver to return specific values
    def resolver(req):
        return {"tenant_id": 123, "user_id": 456}
    
    rls_settings.REQUEST_RESOLVER = resolver
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    
    # Process request through middleware
    middleware.process_request(request)
    
    # Verify session variables were set
    with connection.cursor() as cursor:
        # Check tenant_id
        cursor.execute("SELECT current_setting('rls.tenant_id', true)")
        tenant_value = cursor.fetchone()[0]
        assert tenant_value == "123"
        
        # Check user_id
        cursor.execute("SELECT current_setting('rls.user_id', true)")
        user_value = cursor.fetchone()[0]
        assert user_value == "456"


@pytest.mark.django_db
def test_middleware_sets_wildcard_all(middleware, rls_settings, settings):
    """Test that middleware sets ALL wildcard when bypass is enabled."""
    settings.DJANGO_RLS = rls_settings
    
    factory = RequestFactory()
    request = factory.get("/")
    
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: True
    
    middleware.process_request(request)
    
    # Verify both fields are set to ALL
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('rls.tenant_id', true)")
        tenant_value = cursor.fetchone()[0]
        assert tenant_value == RlsWildcard.ALL.value
        
        cursor.execute("SELECT current_setting('rls.user_id', true)")
        user_value = cursor.fetchone()[0]
        assert user_value == RlsWildcard.ALL.value


@pytest.mark.django_db
def test_middleware_handles_none_values(middleware, rls_settings, settings):
    """Test that middleware sets NONE wildcard for missing values."""
    settings.DJANGO_RLS = rls_settings
    
    factory = RequestFactory()
    request = factory.get("/")
    
    # Resolver returns None for user_id
    def resolver(req):
        return {"tenant_id": 123, "user_id": None}
    
    rls_settings.REQUEST_RESOLVER = resolver
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    
    middleware.process_request(request)
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('rls.tenant_id', true)")
        tenant_value = cursor.fetchone()[0]
        assert tenant_value == "123"
        
        cursor.execute("SELECT current_setting('rls.user_id', true)")
        user_value = cursor.fetchone()[0]
        assert user_value == RlsWildcard.NONE.value


@pytest.mark.django_db
def test_rls_enforces_tenant_isolation(rls_settings, settings):
    """
    Test that RLS policies actually filter rows based on tenant_id.
    
    This test:
    1. Creates records with different tenant_id values
    2. Sets session variable for tenant_id = 123
    3. Queries the database
    4. Verifies only records with tenant_id = 123 are returned
    """
    settings.DJANGO_RLS = rls_settings
    
    # First, create migrations and then create the tables
    call_command("makemigrations", "test_app", interactive=False)
    call_command("migrate", "test_app", verbosity=0)
    
    # Then, ensure RLS is enabled and policies exist
    # (This would normally be done via migrations)
    with connection.cursor() as cursor:
        # Enable RLS on the table
        cursor.execute("ALTER TABLE test_app_tenantmodel ENABLE ROW LEVEL SECURITY")
        
        # Create a simple RLS policy for testing
        # (In production, this would be created via migrations)
        try:
            cursor.execute("DROP POLICY IF EXISTS test_rls_policy ON test_app_tenantmodel")
        except Exception:
            pass  # Policy might not exist
        
        cursor.execute(f"""
            CREATE POLICY test_rls_policy ON test_app_tenantmodel
            FOR ALL
            USING (
                CASE
                    WHEN current_setting('rls.tenant_id', true) IS NULL THEN FALSE
                    WHEN current_setting('rls.tenant_id') = '{RlsWildcard.NONE.value}' THEN FALSE
                    WHEN current_setting('rls.tenant_id') = '{RlsWildcard.ALL.value}' THEN TRUE
                    ELSE tenant_id = current_setting('rls.tenant_id')::int
                END
            )
            WITH CHECK (
                CASE
                    WHEN current_setting('rls.tenant_id', true) IS NULL THEN FALSE
                    WHEN current_setting('rls.tenant_id') = '{RlsWildcard.NONE.value}' THEN FALSE
                    WHEN current_setting('rls.tenant_id') = '{RlsWildcard.ALL.value}' THEN TRUE
                    ELSE tenant_id = current_setting('rls.tenant_id')::int
                END
            )
        """)
    
    # Set session variable to ALL to allow creating records with different tenant_ids
    with connection.cursor() as cursor:
        cursor.execute("SET rls.tenant_id = %s", [RlsWildcard.ALL.value])
    
    # Create test records
    TenantModel.objects.create(tenant_id=123, name="Tenant 123 Record 1")
    TenantModel.objects.create(tenant_id=123, name="Tenant 123 Record 2")
    TenantModel.objects.create(tenant_id=456, name="Tenant 456 Record 1")
    
    # Set session variable for tenant_id = 123
    with connection.cursor() as cursor:
        cursor.execute("SET rls.tenant_id = %s", ["123"])
    
    # Query the database - should only return tenant_id = 123 records
    results = list(TenantModel.objects.all())
    
    assert len(results) == 2
    assert all(r.tenant_id == 123 for r in results)
    assert all(r.name.startswith("Tenant 123") for r in results)
    
    # Change session variable to tenant_id = 456
    with connection.cursor() as cursor:
        cursor.execute("SET rls.tenant_id = %s", ["456"])
    
    # Query again - should only return tenant_id = 456 records
    results = list(TenantModel.objects.all())
    
    assert len(results) == 1
    assert results[0].tenant_id == 456
    assert results[0].name == "Tenant 456 Record 1"
    
    # Cleanup
    with connection.cursor() as cursor:
        cursor.execute("DROP POLICY IF EXISTS test_rls_policy ON test_app_tenantmodel")
        TenantModel.objects.all().delete()


@pytest.fixture
def clean_migrations_and_db():
    """Cleanup migrations and database state for end-to-end tests."""
    # Setup: clean migrations before test
    for app_label in ["test_app"]:
        app_config = apps.get_app_config(app_label)
        migrations_dir = os.path.join(app_config.path, "migrations")
        if os.path.exists(migrations_dir):
            for f in os.listdir(migrations_dir):
                if f != "__init__.py" and f.endswith(".py"):
                    try:
                        os.remove(os.path.join(migrations_dir, f))
                    except PermissionError:
                        pass
    
    yield
    
    # Teardown: clean migrations and data after test
    for app_label in ["test_app"]:
        app_config = apps.get_app_config(app_label)
        migrations_dir = os.path.join(app_config.path, "migrations")
        if os.path.exists(migrations_dir):
            for f in os.listdir(migrations_dir):
                if f != "__init__.py" and f.endswith(".py"):
                    try:
                        os.remove(os.path.join(migrations_dir, f))
                    except PermissionError:
                        pass
    
    # Clean up test data
    TenantModel.objects.all().delete()
    MixedModel.objects.all().delete()
    UserModel.objects.all().delete()
    UUIDTenantModel.objects.all().delete()
    UUIDMixedModel.objects.all().delete()


@pytest.mark.django_db
def test_rls_enforces_multiple_fields(rls_settings, settings):
    """
    Test that RLS policies work with multiple fields (tenant_id AND user_id).
    
    This test verifies that when both tenant_id and user_id are set,
    only records matching BOTH conditions are returned.
    """
    settings.DJANGO_RLS = rls_settings
    
    # First, create migrations and then create the tables
    call_command("makemigrations", "test_app", interactive=False)
    call_command("migrate", "test_app", verbosity=0)
    
    with connection.cursor() as cursor:
        # Enable RLS
        cursor.execute("ALTER TABLE test_app_mixedmodel ENABLE ROW LEVEL SECURITY")
        
        # Create RLS policy with both fields
        try:
            cursor.execute("DROP POLICY IF EXISTS test_rls_policy ON test_app_mixedmodel")
        except Exception:
            pass
        
        cursor.execute(f"""
            CREATE POLICY test_rls_policy ON test_app_mixedmodel
            FOR ALL
            USING (
                (
                    CASE
                        WHEN current_setting('rls.tenant_id', true) IS NULL THEN FALSE
                        WHEN current_setting('rls.tenant_id') = '{RlsWildcard.NONE.value}' THEN FALSE
                        WHEN current_setting('rls.tenant_id') = '{RlsWildcard.ALL.value}' THEN TRUE
                        ELSE tenant_id = current_setting('rls.tenant_id')::int
                    END
                ) AND
                (
                    CASE
                        WHEN current_setting('rls.user_id', true) IS NULL THEN FALSE
                        WHEN current_setting('rls.user_id') = '{RlsWildcard.NONE.value}' THEN FALSE
                        WHEN current_setting('rls.user_id') = '{RlsWildcard.ALL.value}' THEN TRUE
                        ELSE user_id = current_setting('rls.user_id')::int
                    END
                )
            )
            WITH CHECK (
                (
                    CASE
                        WHEN current_setting('rls.tenant_id', true) IS NULL THEN FALSE
                        WHEN current_setting('rls.tenant_id') = '{RlsWildcard.NONE.value}' THEN FALSE
                        WHEN current_setting('rls.tenant_id') = '{RlsWildcard.ALL.value}' THEN TRUE
                        ELSE tenant_id = current_setting('rls.tenant_id')::int
                    END
                ) AND
                (
                    CASE
                        WHEN current_setting('rls.user_id', true) IS NULL THEN FALSE
                        WHEN current_setting('rls.user_id') = '{RlsWildcard.NONE.value}' THEN FALSE
                        WHEN current_setting('rls.user_id') = '{RlsWildcard.ALL.value}' THEN TRUE
                        ELSE user_id = current_setting('rls.user_id')::int
                    END
                )
            )
        """)
    
    # Set session variables to ALL to allow creating records with different values
    with connection.cursor() as cursor:
        cursor.execute("SET rls.tenant_id = %s", [RlsWildcard.ALL.value])
        cursor.execute("SET rls.user_id = %s", [RlsWildcard.ALL.value])
    
    # Create test records
    MixedModel.objects.create(tenant_id=123, user_id=1, content="Record 1")
    MixedModel.objects.create(tenant_id=123, user_id=2, content="Record 2")
    MixedModel.objects.create(tenant_id=456, user_id=1, content="Record 3")
    MixedModel.objects.create(tenant_id=123, user_id=1, content="Record 4")
    
    # Set session variables for tenant_id=123 AND user_id=1
    with connection.cursor() as cursor:
        cursor.execute("SET rls.tenant_id = %s", ["123"])
        cursor.execute("SET rls.user_id = %s", ["1"])
    
    # Query - should only return records matching both
    results = list(MixedModel.objects.all())
    
    assert len(results) == 2
    assert all(r.tenant_id == 123 and r.user_id == 1 for r in results)
    
    # Change to tenant_id=123, user_id=2
    with connection.cursor() as cursor:
        cursor.execute("SET rls.user_id = %s", ["2"])
    
    results = list(MixedModel.objects.all())
    
    assert len(results) == 1
    assert results[0].tenant_id == 123
    assert results[0].user_id == 2
    
    # Cleanup
    with connection.cursor() as cursor:
        cursor.execute("DROP POLICY IF EXISTS test_rls_policy ON test_app_mixedmodel")
        MixedModel.objects.all().delete()


@pytest.mark.django_db
def test_rls_wildcard_all_bypasses_filtering(rls_settings, settings):
    """
    Test that RlsWildcard.ALL bypasses RLS filtering.
    
    When session variable is set to ALL, all records should be returned
    regardless of their tenant_id/user_id values.
    """
    settings.DJANGO_RLS = rls_settings
    
    # First, create migrations and then create the tables
    call_command("makemigrations", "test_app", interactive=False)
    call_command("migrate", "test_app", verbosity=0)
    
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE test_app_tenantmodel ENABLE ROW LEVEL SECURITY")
        
        try:
            cursor.execute("DROP POLICY IF EXISTS test_rls_policy ON test_app_tenantmodel")
        except Exception:
            pass
        
        cursor.execute(f"""
            CREATE POLICY test_rls_policy ON test_app_tenantmodel
            FOR ALL
            USING (
                CASE
                    WHEN current_setting('rls.tenant_id', true) IS NULL THEN FALSE
                    WHEN current_setting('rls.tenant_id') = '{RlsWildcard.NONE.value}' THEN FALSE
                    WHEN current_setting('rls.tenant_id') = '{RlsWildcard.ALL.value}' THEN TRUE
                    ELSE tenant_id = current_setting('rls.tenant_id')::int
                END
            )
            WITH CHECK (
                CASE
                    WHEN current_setting('rls.tenant_id', true) IS NULL THEN FALSE
                    WHEN current_setting('rls.tenant_id') = '{RlsWildcard.NONE.value}' THEN FALSE
                    WHEN current_setting('rls.tenant_id') = '{RlsWildcard.ALL.value}' THEN TRUE
                    ELSE tenant_id = current_setting('rls.tenant_id')::int
                END
            )
        """)
    
    # Set ALL wildcard before creating records
    with connection.cursor() as cursor:
        cursor.execute("SET rls.tenant_id = %s", [RlsWildcard.ALL.value])
    
    # Create records with different tenant_ids
    TenantModel.objects.create(tenant_id=123, name="Tenant 123")
    TenantModel.objects.create(tenant_id=456, name="Tenant 456")
    TenantModel.objects.create(tenant_id=789, name="Tenant 789")
    
    # Query - should return ALL records
    results = list(TenantModel.objects.all())
    
    assert len(results) == 3
    
    # Cleanup
    with connection.cursor() as cursor:
        cursor.execute("DROP POLICY IF EXISTS test_rls_policy ON test_app_tenantmodel")
        TenantModel.objects.all().delete()


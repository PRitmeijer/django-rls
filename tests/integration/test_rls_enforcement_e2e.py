"""
End-to-end tests for RLS enforcement using actual Django commands.

These tests verify the complete workflow:
1. makemigrations -> creates migrations with RLS policies
2. migrate -> applies migrations to database
3. Create test data
4. Set session variables via middleware
5. Query database and verify RLS enforcement works

Note: All tests use PostgreSQL since RLS is PostgreSQL-only.
Start PostgreSQL with 'docker-compose up -d' or 'task postgresql:up' before running tests.
"""
import os
import pytest
from django.db import connection
from django.test import RequestFactory
from django.core.management import call_command
from django.apps import apps
from django_rls.middleware import RLSMiddleware
from django_rls.settings_type import DjangoRLSSettings
from testproject.app.models import (
    TenantModel, MixedModel, UserModel, NoRLSModel,
    UUIDTenantModel, UUIDMixedModel
)


# Fixtures are now in conftest.py


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
def test_end_to_end_makemigrations_migrate_enforcement(clean_migrations_and_db, rls_settings, settings):
    """
    End-to-end test: makemigrations -> migrate -> verify RLS enforcement works.
    
    This test:
    1. Runs makemigrations to create migrations with RLS policies
    2. Runs migrate to apply those migrations
    3. Creates test data with different tenant_id values
    4. Sets session variables via middleware
    5. Queries the database and verifies RLS filtering works
    """
    settings.DJANGO_RLS = rls_settings
    
    # Step 1: Create migrations with RLS policies
    call_command("makemigrations", "test_app", interactive=False)
    
    # Step 2: Apply migrations (this creates the RLS policies in the database)
    call_command("migrate", "test_app", verbosity=0)
    
    # Step 3: Create test data with different tenant_id values
    # Use bypass to allow data creation without session variables
    factory = RequestFactory()
    request = factory.get("/")
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: True
    middleware = RLSMiddleware(lambda req: None)
    middleware.process_request(request)
    
    TenantModel.objects.create(tenant_id=123, name="Tenant 123 Record 1")
    TenantModel.objects.create(tenant_id=123, name="Tenant 123 Record 2")
    TenantModel.objects.create(tenant_id=456, name="Tenant 456 Record 1")
    TenantModel.objects.create(tenant_id=789, name="Tenant 789 Record 1")
    
    # Step 4: Set session variable for tenant_id = 123 via middleware
    factory = RequestFactory()
    request = factory.get("/")
    
    def resolver(req):
        return {"tenant_id": 123, "user_id": None}
    
    rls_settings.REQUEST_RESOLVER = resolver
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    
    middleware = RLSMiddleware(lambda req: None)
    middleware.process_request(request)
    
    # Step 5: Query the database - should only return tenant_id = 123 records
    results = list(TenantModel.objects.all())
    
    assert len(results) == 2, f"Expected 2 records, got {len(results)}"
    assert all(r.tenant_id == 123 for r in results), "All results should have tenant_id = 123"
    assert all(r.name.startswith("Tenant 123") for r in results)
    
    # Step 6: Change session variable to tenant_id = 456
    def resolver_456(req):
        return {"tenant_id": 456, "user_id": None}
    
    rls_settings.REQUEST_RESOLVER = resolver_456
    middleware.process_request(request)
    
    # Query again - should only return tenant_id = 456 records
    results = list(TenantModel.objects.all())
    
    assert len(results) == 1, f"Expected 1 record, got {len(results)}"
    assert results[0].tenant_id == 456
    assert results[0].name == "Tenant 456 Record 1"
    
    # Step 7: Test ALL wildcard bypass
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: True
    middleware.process_request(request)
    
    # Query - should return ALL records (bypass RLS)
    results = list(TenantModel.objects.all())
    
    assert len(results) == 4, f"Expected 4 records with ALL wildcard, got {len(results)}"


@pytest.mark.django_db
def test_end_to_end_mixed_model_multiple_fields(clean_migrations_and_db, rls_settings, settings):
    """
    End-to-end test for MixedModel with multiple RLS fields (tenant_id AND user_id).
    
    This test verifies that RLS policies created via makemigrations/migrate
    correctly enforce multiple fields.
    """
    settings.DJANGO_RLS = rls_settings
    
    # Step 1: Create and apply migrations
    call_command("makemigrations", "test_app", interactive=False)
    call_command("migrate", "test_app", verbosity=0)
    
    # Step 2: Create test data
    # Use bypass to allow data creation without session variables
    factory = RequestFactory()
    request = factory.get("/")
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: True
    middleware = RLSMiddleware(lambda req: None)
    middleware.process_request(request)
    
    MixedModel.objects.create(tenant_id=123, user_id=1, content="Record 1")
    MixedModel.objects.create(tenant_id=123, user_id=2, content="Record 2")
    MixedModel.objects.create(tenant_id=456, user_id=1, content="Record 3")
    MixedModel.objects.create(tenant_id=123, user_id=1, content="Record 4")
    
    # Step 3: Set session variables for tenant_id=123 AND user_id=1
    factory = RequestFactory()
    request = factory.get("/")
    
    def resolver(req):
        return {"tenant_id": 123, "user_id": 1}
    
    rls_settings.REQUEST_RESOLVER = resolver
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    
    middleware = RLSMiddleware(lambda req: None)
    middleware.process_request(request)
    
    # Step 4: Query - should only return records matching both conditions
    results = list(MixedModel.objects.all())
    
    assert len(results) == 2, f"Expected 2 records, got {len(results)}"
    assert all(r.tenant_id == 123 and r.user_id == 1 for r in results)
    
    # Step 5: Change to tenant_id=123, user_id=2
    def resolver_2(req):
        return {"tenant_id": 123, "user_id": 2}
    
    rls_settings.REQUEST_RESOLVER = resolver_2
    middleware.process_request(request)
    
    results = list(MixedModel.objects.all())
    
    assert len(results) == 1, f"Expected 1 record, got {len(results)}"
    assert results[0].tenant_id == 123
    assert results[0].user_id == 2
    assert results[0].content == "Record 2"


@pytest.mark.django_db
def test_end_to_end_add_rls_command_enforcement(clean_migrations_and_db, rls_settings, settings):
    """
    End-to-end test: add_rls command -> migrate -> verify RLS enforcement works.
    
    This test verifies that the add_rls command creates migrations that,
    when applied, correctly enforce RLS.
    """
    settings.DJANGO_RLS = rls_settings
    
    # Step 1: Create initial migrations (without RLS)
    call_command("makemigrations", "test_app", interactive=False)
    call_command("migrate", "test_app", verbosity=0)
    
    # Step 2: Use add_rls command to add RLS policies
    call_command("add_rls", "test_app")
    
    # Step 3: Apply the RLS migration
    call_command("migrate", "test_app", verbosity=0)
    
    # Step 4: Create test data
    # Use bypass to allow data creation without session variables
    factory = RequestFactory()
    request = factory.get("/")
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: True
    middleware = RLSMiddleware(lambda req: None)
    middleware.process_request(request)
    
    TenantModel.objects.create(tenant_id=100, name="Tenant 100")
    TenantModel.objects.create(tenant_id=200, name="Tenant 200")
    TenantModel.objects.create(tenant_id=100, name="Tenant 100 Second")
    
    # Step 5: Set session variable and verify enforcement
    factory = RequestFactory()
    request = factory.get("/")
    
    def resolver(req):
        return {"tenant_id": 100, "user_id": None}
    
    rls_settings.REQUEST_RESOLVER = resolver
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    
    middleware = RLSMiddleware(lambda req: None)
    middleware.process_request(request)
    
    # Query - should only return tenant_id = 100 records
    results = list(TenantModel.objects.all())
    
    assert len(results) == 2, f"Expected 2 records, got {len(results)}"
    assert all(r.tenant_id == 100 for r in results)


@pytest.mark.django_db
def test_end_to_end_uuid_tenant_isolation(clean_migrations_and_db, rls_settings, settings):
    """
    End-to-end test for UUIDTenantModel with UUID tenant_id field.
    
    This test verifies that RLS policies work correctly with UUID fields.
    """
    import uuid
    settings.DJANGO_RLS = rls_settings
    
    # Step 1: Create and apply migrations
    call_command("makemigrations", "test_app", interactive=False)
    call_command("migrate", "test_app", verbosity=0)
    
    # Step 2: Create test data with UUIDs
    tenant_uuid_1 = uuid.uuid4()
    tenant_uuid_2 = uuid.uuid4()
    
    # Use bypass to allow data creation without session variables
    factory = RequestFactory()
    request = factory.get("/")
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: True
    middleware = RLSMiddleware(lambda req: None)
    middleware.process_request(request)
    
    UUIDTenantModel.objects.create(tenant_id=tenant_uuid_1, name="UUID Tenant 1 Record 1")
    UUIDTenantModel.objects.create(tenant_id=tenant_uuid_1, name="UUID Tenant 1 Record 2")
    UUIDTenantModel.objects.create(tenant_id=tenant_uuid_2, name="UUID Tenant 2 Record 1")
    
    # Step 3: Set session variable for tenant_uuid_1 via middleware
    factory = RequestFactory()
    request = factory.get("/")
    
    def resolver(req):
        return {"tenant_id": tenant_uuid_1, "user_id": None}
    
    rls_settings.REQUEST_RESOLVER = resolver
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    
    middleware = RLSMiddleware(lambda req: None)
    middleware.process_request(request)
    
    # Step 4: Query - should only return tenant_uuid_1 records
    results = list(UUIDTenantModel.objects.all())
    
    assert len(results) == 2, f"Expected 2 records, got {len(results)}"
    assert all(str(r.tenant_id) == str(tenant_uuid_1) for r in results)
    
    # Step 5: Change to tenant_uuid_2
    def resolver_2(req):
        return {"tenant_id": tenant_uuid_2, "user_id": None}
    
    rls_settings.REQUEST_RESOLVER = resolver_2
    middleware.process_request(request)
    
    results = list(UUIDTenantModel.objects.all())
    
    assert len(results) == 1, f"Expected 1 record, got {len(results)}"
    assert str(results[0].tenant_id) == str(tenant_uuid_2)


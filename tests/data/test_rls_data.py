"""
Manual data tests for RLS enforcement.

These tests can be run interactively after migrations are applied.
They create test data and verify RLS filtering works correctly.

Usage in Django shell:
    from tests.data.test_rls_data import *
    manual_test_tenant_isolation()
    manual_test_uuid_tenant_isolation()
    manual_test_mixed_fields()
    cleanup_test_data()
    # Or run all:
    run_all_tests()
"""
import uuid
from django.conf import settings as django_settings
from django.db import connection
from django.test import RequestFactory
from django_rls.middleware import RLSMiddleware
from django_rls.settings_type import DjangoRLSSettings
from django_rls.constants import RlsWildcard
from testproject.app.models import (
    TenantModel, MixedModel, UserModel, NoRLSModel,
    UUIDTenantModel, UUIDMixedModel
)


def get_middleware(rls_settings):
    """Get configured middleware instance."""
    from django_rls.middleware import RLSMiddleware
    
    def get_response(request):
        return None
    middleware = RLSMiddleware(get_response)
    return middleware


def manual_test_tenant_isolation():
    """Test RLS isolation with integer tenant_id."""
    print("\n=== Testing Tenant Isolation (Integer) ===")
    
    # Setup - use settings from Django settings
    rls_settings = getattr(django_settings, "DJANGO_RLS", DjangoRLSSettings(
        RLS_FIELDS=["tenant_id", "user_id"],
        TENANT_APPS=["test_app"],
    ))
    django_settings.DJANGO_RLS = rls_settings
    middleware = get_middleware(rls_settings)
    
    # Create test data
    TenantModel.objects.all().delete()  # Cleanup first
    TenantModel.objects.create(tenant_id=123, name="Tenant 123 Record 1")
    TenantModel.objects.create(tenant_id=123, name="Tenant 123 Record 2")
    TenantModel.objects.create(tenant_id=456, name="Tenant 456 Record 1")
    TenantModel.objects.create(tenant_id=789, name="Tenant 789 Record 1")
    
    print(f"Created {TenantModel.objects.count()} records")
    
    # Test with tenant_id=123
    factory = RequestFactory()
    request = factory.get("/")
    
    def resolver_123(req):
        return {"tenant_id": 123, "user_id": None}
    
    rls_settings.REQUEST_RESOLVER = resolver_123
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    middleware.process_request(request)
    
    results = list(TenantModel.objects.all())
    print(f"With tenant_id=123: Found {len(results)} records")
    assert len(results) == 2, f"Expected 2 records, got {len(results)}"
    assert all(r.tenant_id == 123 for r in results)
    print("✓ Tenant isolation works correctly")
    
    # Test with tenant_id=456
    def resolver_456(req):
        return {"tenant_id": 456, "user_id": None}
    
    rls_settings.REQUEST_RESOLVER = resolver_456
    middleware.process_request(request)
    
    results = list(TenantModel.objects.all())
    print(f"With tenant_id=456: Found {len(results)} records")
    assert len(results) == 1
    assert results[0].tenant_id == 456
    print("✓ Tenant filtering works correctly")


def manual_test_uuid_tenant_isolation():
    """Test RLS isolation with UUID tenant_id."""
    print("\n=== Testing Tenant Isolation (UUID) ===")
    
    # Setup - use settings from Django settings
    rls_settings = getattr(django_settings, "DJANGO_RLS", DjangoRLSSettings(
        RLS_FIELDS=["tenant_id", "user_id"],
        TENANT_APPS=["test_app"],
    ))
    django_settings.DJANGO_RLS = rls_settings
    middleware = get_middleware(rls_settings)
    
    # Create test data with UUIDs
    UUIDTenantModel.objects.all().delete()  # Cleanup first
    tenant_uuid_1 = uuid.uuid4()
    tenant_uuid_2 = uuid.uuid4()
    
    UUIDTenantModel.objects.create(tenant_id=tenant_uuid_1, name="UUID Tenant 1 Record 1")
    UUIDTenantModel.objects.create(tenant_id=tenant_uuid_1, name="UUID Tenant 1 Record 2")
    UUIDTenantModel.objects.create(tenant_id=tenant_uuid_2, name="UUID Tenant 2 Record 1")
    
    print(f"Created {UUIDTenantModel.objects.count()} UUID records")
    print(f"Tenant UUID 1: {tenant_uuid_1}")
    print(f"Tenant UUID 2: {tenant_uuid_2}")
    
    # Test with tenant_uuid_1
    factory = RequestFactory()
    request = factory.get("/")
    
    def resolver_uuid1(req):
        return {"tenant_id": tenant_uuid_1, "user_id": None}
    
    rls_settings.REQUEST_RESOLVER = resolver_uuid1
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    middleware.process_request(request)
    
    results = list(UUIDTenantModel.objects.all())
    print(f"With tenant_id={tenant_uuid_1}: Found {len(results)} records")
    assert len(results) == 2, f"Expected 2 records, got {len(results)}"
    assert all(str(r.tenant_id) == str(tenant_uuid_1) for r in results)
    print("✓ UUID tenant isolation works correctly")


def manual_test_mixed_fields():
    """Test RLS with multiple fields (tenant_id AND user_id)."""
    print("\n=== Testing Mixed Fields (Integer) ===")
    
    # Setup - use settings from Django settings
    rls_settings = getattr(django_settings, "DJANGO_RLS", DjangoRLSSettings(
        RLS_FIELDS=["tenant_id", "user_id"],
        TENANT_APPS=["test_app"],
    ))
    django_settings.DJANGO_RLS = rls_settings
    middleware = get_middleware(rls_settings)
    
    # Create test data
    MixedModel.objects.all().delete()  # Cleanup first
    MixedModel.objects.create(tenant_id=123, user_id=1, content="Record 1")
    MixedModel.objects.create(tenant_id=123, user_id=2, content="Record 2")
    MixedModel.objects.create(tenant_id=456, user_id=1, content="Record 3")
    MixedModel.objects.create(tenant_id=123, user_id=1, content="Record 4")
    
    print(f"Created {MixedModel.objects.count()} mixed records")
    
    # Test with tenant_id=123 AND user_id=1
    factory = RequestFactory()
    request = factory.get("/")
    
    def resolver_mixed(req):
        return {"tenant_id": 123, "user_id": 1}
    
    rls_settings.REQUEST_RESOLVER = resolver_mixed
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    middleware.process_request(request)
    
    results = list(MixedModel.objects.all())
    print(f"With tenant_id=123 AND user_id=1: Found {len(results)} records")
    assert len(results) == 2
    assert all(r.tenant_id == 123 and r.user_id == 1 for r in results)
    print("✓ Mixed field filtering works correctly")


def manual_test_uuid_mixed_fields():
    """Test RLS with UUID fields (tenant_id AND user_id)."""
    print("\n=== Testing Mixed Fields (UUID) ===")
    
    # Setup - use settings from Django settings
    rls_settings = getattr(django_settings, "DJANGO_RLS", DjangoRLSSettings(
        RLS_FIELDS=["tenant_id", "user_id"],
        TENANT_APPS=["test_app"],
    ))
    django_settings.DJANGO_RLS = rls_settings
    middleware = get_middleware(rls_settings)
    
    # Create test data with UUIDs
    UUIDMixedModel.objects.all().delete()  # Cleanup first
    tenant_uuid = uuid.uuid4()
    user_uuid_1 = uuid.uuid4()
    user_uuid_2 = uuid.uuid4()
    
    UUIDMixedModel.objects.create(tenant_id=tenant_uuid, user_id=user_uuid_1, content="UUID Record 1")
    UUIDMixedModel.objects.create(tenant_id=tenant_uuid, user_id=user_uuid_2, content="UUID Record 2")
    UUIDMixedModel.objects.create(tenant_id=tenant_uuid, user_id=user_uuid_1, content="UUID Record 3")
    
    print(f"Created {UUIDMixedModel.objects.count()} UUID mixed records")
    
    # Test with specific tenant and user UUIDs
    factory = RequestFactory()
    request = factory.get("/")
    
    def resolver_uuid_mixed(req):
        return {"tenant_id": tenant_uuid, "user_id": user_uuid_1}
    
    rls_settings.REQUEST_RESOLVER = resolver_uuid_mixed
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: False
    middleware.process_request(request)
    
    results = list(UUIDMixedModel.objects.all())
    print(f"With tenant_id={tenant_uuid} AND user_id={user_uuid_1}: Found {len(results)} records")
    assert len(results) == 2
    assert all(str(r.tenant_id) == str(tenant_uuid) and str(r.user_id) == str(user_uuid_1) for r in results)
    print("✓ UUID mixed field filtering works correctly")


def manual_test_wildcard_all():
    """Test that RlsWildcard.ALL bypasses RLS filtering."""
    print("\n=== Testing Wildcard ALL ===")
    
    # Setup - use settings from Django settings
    rls_settings = getattr(django_settings, "DJANGO_RLS", DjangoRLSSettings(
        RLS_FIELDS=["tenant_id", "user_id"],
        TENANT_APPS=["test_app"],
    ))
    django_settings.DJANGO_RLS = rls_settings
    middleware = get_middleware(rls_settings)
    
    # Ensure we have data
    if TenantModel.objects.count() == 0:
        TenantModel.objects.create(tenant_id=123, name="Tenant 123")
        TenantModel.objects.create(tenant_id=456, name="Tenant 456")
        TenantModel.objects.create(tenant_id=789, name="Tenant 789")
    
    factory = RequestFactory()
    request = factory.get("/")
    
    # Enable bypass
    rls_settings.BYPASS_CHECK_RESOLVER = lambda r: True
    middleware.process_request(request)
    
    results = list(TenantModel.objects.all())
    print(f"With ALL wildcard: Found {len(results)} records")
    assert len(results) >= 3, "Should return all records with ALL wildcard"
    print("✓ Wildcard ALL bypass works correctly")


def cleanup_test_data():
    """Clean up all test data."""
    print("\n=== Cleaning up test data ===")
    TenantModel.objects.all().delete()
    MixedModel.objects.all().delete()
    UserModel.objects.all().delete()
    UUIDTenantModel.objects.all().delete()
    UUIDMixedModel.objects.all().delete()
    print("✓ All test data cleaned up")


def run_all_tests():
    """Run all data tests in sequence."""
    print("=" * 50)
    print("Running all RLS data tests")
    print("=" * 50)
    
    try:
        manual_test_tenant_isolation()
        manual_test_uuid_tenant_isolation()
        manual_test_mixed_fields()
        manual_test_uuid_mixed_fields()
        manual_test_wildcard_all()
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


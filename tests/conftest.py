"""
Pytest configuration and fixtures for django-rls tests.

Note: All tests use PostgreSQL by default since RLS is PostgreSQL-only.
Start PostgreSQL with 'docker-compose up -d' or 'task postgresql:up' before running tests.
"""
import pytest
from django_rls.settings_type import DjangoRLSSettings


@pytest.fixture
def rls_settings():
    """Create RLS settings for testing with integer and UUID field support."""
    return DjangoRLSSettings(
        RLS_FIELDS=["tenant_id", "user_id"],
        TENANT_APPS=["test_app"],
    )


@pytest.fixture
def middleware():
    """Create middleware instance for testing."""
    from django_rls.middleware import RLSMiddleware
    
    def get_response(request):
        return None
    return RLSMiddleware(get_response)

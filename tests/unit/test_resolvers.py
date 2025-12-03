import pytest
from types import SimpleNamespace
from django_rls.resolvers import default_request_user_resolver
from django_rls.settings_type import DjangoRLSSettings

@pytest.fixture
def mock_settings(monkeypatch):
    settings = DjangoRLSSettings(RLS_FIELDS=["tenant_id", "user_id"])
    # Patching where get_rls_settings is defined or used
    # Since we added get_rls_settings helper in resolvers.py, we should patch that or the import
    
    # But wait, resolvers.py imports get_rls_settings which imports django_rls_settings from settings.py
    # It's cleaner to patch django_rls.settings.django_rls_settings
    monkeypatch.setattr("django_rls.settings.django_rls_settings", settings)
    return settings

def test_resolver_unauthenticated_user():
    request = SimpleNamespace(user=SimpleNamespace(is_authenticated=False))
    context = default_request_user_resolver(request)
    assert context == {}

def test_resolver_authenticated_user_with_fields(mock_settings):
    user = SimpleNamespace(
        is_authenticated=True,
        tenant_id=123,
        user_id=456
    )
    request = SimpleNamespace(user=user)
    
    context = default_request_user_resolver(request)
    
    assert context["tenant_id"] == 123
    assert context["user_id"] == 456


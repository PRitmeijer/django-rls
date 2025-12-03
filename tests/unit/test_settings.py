import pytest
from django.conf import settings
from django_rls.settings_type import DjangoRLSSettings

def test_default_settings():
    rls_settings = DjangoRLSSettings()
    assert rls_settings.RLS_FIELDS == ["tenant_id", "user_id"]
    assert rls_settings.TENANT_APPS == []

def test_custom_settings_loaded():
    assert hasattr(settings, "DJANGO_RLS")
    rls_settings = settings.DJANGO_RLS
    assert isinstance(rls_settings, DjangoRLSSettings)
    assert "test_app" in rls_settings.TENANT_APPS


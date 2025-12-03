import pytest
from unittest.mock import MagicMock, patch
from django_rls.middleware import RLSMiddleware
from django_rls.settings_type import DjangoRLSSettings
from django_rls.constants import RlsWildcard

@pytest.fixture
def middleware():
    return RLSMiddleware(get_response=MagicMock())

@patch("django_rls.middleware.connection")
def test_process_request_bypass(mock_connection, middleware):
    request = MagicMock()
    
    # Mock connection vendor to be postgresql (required for middleware to proceed)
    mock_connection.vendor = "postgresql"
    
    # Mock settings
    settings = DjangoRLSSettings(RLS_FIELDS=["tenant_id"])
    
    # Mock bypass resolver to return True
    settings.BYPASS_CHECK_RESOLVER = lambda r: True
    
    with patch("django_rls.middleware.django_settings") as mock_django_settings:
        mock_django_settings.DJANGO_RLS = settings
        
        middleware.process_request(request)
        
        cursor = mock_connection.cursor.return_value.__enter__.return_value
        # Should set ALL wildcard
        cursor.execute.assert_called_with(
            f"SET {settings.SESSION_NAMESPACE_PREFIX}.tenant_id = %s", 
            [RlsWildcard.ALL.value]
        )

@patch("django_rls.middleware.connection")
def test_process_request_normal(mock_connection, middleware):
    request = MagicMock()
    
    # Mock connection vendor to be postgresql (required for middleware to proceed)
    mock_connection.vendor = "postgresql"
    
    settings = DjangoRLSSettings(RLS_FIELDS=["tenant_id"])
    # Bypass False
    settings.BYPASS_CHECK_RESOLVER = lambda r: False
    # Resolver returns value
    settings.REQUEST_RESOLVER = lambda r: {"tenant_id": 100}
    
    with patch("django_rls.middleware.django_settings") as mock_django_settings:
        mock_django_settings.DJANGO_RLS = settings
        
        middleware.process_request(request)
        
        cursor = mock_connection.cursor.return_value.__enter__.return_value
        cursor.execute.assert_called_with(
            f"SET {settings.SESSION_NAMESPACE_PREFIX}.tenant_id = %s", 
            [100]
        )

@patch("django_rls.middleware.connection")
def test_process_request_filters_fields(mock_connection, middleware):
    request = MagicMock()
    
    # Mock connection vendor to be postgresql (required for middleware to proceed)
    mock_connection.vendor = "postgresql"
    
    settings = DjangoRLSSettings(RLS_FIELDS=["tenant_id"])
    settings.BYPASS_CHECK_RESOLVER = lambda r: False
    # Resolver returns extra field not in RLS_FIELDS
    settings.REQUEST_RESOLVER = lambda r: {"tenant_id": 100, "extra_field": 200}
    
    with patch("django_rls.middleware.django_settings") as mock_django_settings:
        mock_django_settings.DJANGO_RLS = settings
        
        middleware.process_request(request)
        
        cursor = mock_connection.cursor.return_value.__enter__.return_value
        # Should only call for tenant_id
        assert cursor.execute.call_count == 1
        cursor.execute.assert_called_with(
            f"SET {settings.SESSION_NAMESPACE_PREFIX}.tenant_id = %s", 
            [100]
        )


# Bypass Checks

Bypass checks determine when RLS should be completely bypassed, allowing access to all data regardless of RLS policies.

For API documentation on bypass check functions, see the [API Reference](../api/index.md) (search for `bypass`).

## Default Behavior

The default bypass check allows superusers to bypass RLS:

```python
from django_rls.resolvers import default_rls_bypass_check

DJANGO_RLS = DjangoRLSSettings(
    BYPASS_CHECK_RESOLVER=default_rls_bypass_check,
)
```

## Custom Bypass Checks

### Role-Based Bypass

```python
from typing import Any

def role_based_bypass(request: Any) -> bool:
    """
    Bypass RLS for users with specific roles.
    """
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    
    # Bypass for superusers
    if getattr(user, 'is_superuser', False):
        return True
    
    # Bypass for admin role
    if hasattr(user, 'role') and user.role == 'admin':
        return True
    
    # Bypass for staff
    if getattr(user, 'is_staff', False):
        return True
    
    return False

DJANGO_RLS = DjangoRLSSettings(
    BYPASS_CHECK_RESOLVER=role_based_bypass,
)
```

### IP-Based Bypass

```python
from typing import Any

def ip_based_bypass(request: Any) -> bool:
    """
    Bypass RLS for requests from specific IP addresses.
    """
    ip = request.META.get('REMOTE_ADDR')
    trusted_ips = ['127.0.0.1', '192.168.1.100', '10.0.0.0/8']
    
    for trusted_ip in trusted_ips:
        if ip == trusted_ip or ip.startswith(trusted_ip):
            return True
    
    return False

DJANGO_RLS = DjangoRLSSettings(
    BYPASS_CHECK_RESOLVER=ip_based_bypass,
)
```

### Path-Based Bypass

```python
from typing import Any

def path_based_bypass(request: Any) -> bool:
    """
    Bypass RLS for specific URL paths (e.g., admin interface).
    """
    bypass_paths = ['/admin/', '/api/admin/', '/internal/']
    
    for path in bypass_paths:
        if request.path.startswith(path):
            return True
    
    return False

DJANGO_RLS = DjangoRLSSettings(
    BYPASS_CHECK_RESOLVER=path_based_bypass,
)
```

### Combined Bypass

```python
from typing import Any

def combined_bypass(request: Any) -> bool:
    """
    Combine multiple bypass conditions.
    """
    user = getattr(request, 'user', None)
    
    # Superuser bypass
    if user and getattr(user, 'is_superuser', False):
        return True
    
    # IP bypass
    ip = request.META.get('REMOTE_ADDR')
    if ip in ['127.0.0.1', '192.168.1.100']:
        return True
    
    # Path bypass
    if request.path.startswith('/admin/'):
        return True
    
    # Header bypass (for internal services)
    if request.META.get('HTTP_X_INTERNAL_SERVICE') == 'true':
        return True
    
    return False

DJANGO_RLS = DjangoRLSSettings(
    BYPASS_CHECK_RESOLVER=combined_bypass,
)
```

## What Happens When Bypassed?

When `BYPASS_CHECK_RESOLVER` returns `True`, all RLS fields are set to `RlsWildcard.ALL`:

```python
# Normal request
{
    "tenant_id": 123,
    "user_id": 456,
}

# Bypassed request
{
    "tenant_id": RlsWildcard.ALL,
    "user_id": RlsWildcard.ALL,
}
```

PostgreSQL RLS policies should handle this wildcard appropriately, or you can create policies that allow access when the value is the wildcard.

## Security Considerations

⚠️ **Warning**: Bypass checks should be used carefully. Only bypass RLS when absolutely necessary and ensure proper authentication/authorization is in place.

Best practices:
- Always verify user authentication
- Use specific conditions (don't bypass too broadly)
- Log bypass events for auditing
- Review bypass logic regularly

## Testing Bypass Checks

```python
from django.test import RequestFactory
from myapp.bypass import role_based_bypass

def test_bypass_check():
    factory = RequestFactory()
    request = factory.get('/')
    
    # Test without user
    assert role_based_bypass(request) == False
    
    # Test with superuser
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    request.user = user
    
    assert role_based_bypass(request) == True
```

## Next Steps

- [Custom Resolvers](custom-resolvers.md) - Custom resolver patterns
- [Configuration](../configuration/settings.md) - Bypass check configuration


# Resolvers

Resolvers are functions that extract RLS context values from requests or GraphQL info objects.

## Built-in Resolvers

django-rls provides several built-in resolvers. For complete API documentation, see the [API Reference](../api/index.md) (search for `resolvers`).

### Using Built-in Resolvers

```python
from django_rls.resolvers import (
    default_request_user_resolver,
    default_rls_bypass_check,
    strawberry_context_user_resolver,
    strawberry_rls_bypass_check,
)

# For Django requests
DJANGO_RLS = DjangoRLSSettings(
    REQUEST_RESOLVER=default_request_user_resolver,
    BYPASS_CHECK_RESOLVER=default_rls_bypass_check,
)

# For Strawberry GraphQL
DJANGO_RLS = DjangoRLSSettings(
    REQUEST_RESOLVER=strawberry_context_user_resolver,
    BYPASS_CHECK_RESOLVER=strawberry_rls_bypass_check,
)
```

## Custom Resolvers

You can create custom resolvers for your specific needs.

### Custom Request Resolver

```python
from typing import Any, Dict
from django_rls.constants import RLSValue, RlsWildcard

def my_custom_resolver(request: Any) -> Dict[str, RLSValue]:
    """
    Custom resolver that extracts RLS values from request.
    
    Returns a dictionary mapping field names to their values.
    """
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {}
    
    return {
        "tenant_id": user.tenant.id if hasattr(user, "tenant") else RlsWildcard.NONE,
        "user_id": user.id,
        "organization_id": user.organization.id if hasattr(user, "organization") else None,
    }

DJANGO_RLS = DjangoRLSSettings(
    REQUEST_RESOLVER=my_custom_resolver,
)
```

### Custom Bypass Check

```python
from typing import Any

def my_bypass_check(request: Any) -> bool:
    """
    Custom bypass check.
    
    Returns True if RLS should be bypassed for this request.
    """
    user = getattr(request, "user", None)
    if not user:
        return False
    
    # Bypass for superusers
    if getattr(user, "is_superuser", False):
        return True
    
    # Bypass for specific roles
    if hasattr(user, "role") and user.role == "admin":
        return True
    
    # Bypass for specific IPs
    ip = request.META.get("REMOTE_ADDR")
    if ip in ["127.0.0.1", "192.168.1.100"]:
        return True
    
    return False

DJANGO_RLS = DjangoRLSSettings(
    BYPASS_CHECK_RESOLVER=my_bypass_check,
)
```

## RLS Values

Resolvers can return:

- **Integer/string values**: Direct values like `123` or `"tenant-abc"`
- **RlsWildcard.NONE**: Indicates no value (treated as `None` in database)
- **RlsWildcard.ALL**: Special wildcard that bypasses RLS for that field (only used by bypass check)

```python
from django_rls.constants import RlsWildcard

{
    "tenant_id": 123,  # Specific tenant
    "user_id": RlsWildcard.NONE,  # No user restriction
    "organization_id": RlsWildcard.ALL,  # Bypass (only if bypass check returns True)
}
```

## Next Steps

- [Custom Resolvers](../advanced/custom-resolvers.md) - Advanced resolver patterns
- [Bypass Checks](../advanced/bypass-checks.md) - Advanced bypass patterns


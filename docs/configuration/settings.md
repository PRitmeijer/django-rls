# Configuration

The `DJANGO_RLS` setting controls how django-rls behaves in your application.

## Basic Configuration

```python
from django_rls.settings_type import DjangoRLSSettings
from django_rls.resolvers import default_request_user_resolver, default_rls_bypass_check

DJANGO_RLS = DjangoRLSSettings(
    RLS_FIELDS=["tenant_id", "user_id"],
    TENANT_APPS=["myapp"],
    REQUEST_RESOLVER=default_request_user_resolver,
    BYPASS_CHECK_RESOLVER=default_rls_bypass_check,
    AUTO_SET_FIELDS=True,
)
```

## Complete Settings Reference

For complete documentation of all settings fields, types, and defaults, see the [API Reference](../api/index.md) (search for `DjangoRLSSettings`).

## Common Configuration Examples

### Multi-Tenant Setup

```python
DJANGO_RLS = DjangoRLSSettings(
    RLS_FIELDS=["tenant_id", "user_id"],
    TENANT_APPS=["myapp", "otherapp"],
    AUTO_SET_FIELDS=True,
)
```

### Custom Resolver

```python
def my_custom_resolver(request):
    return {
        "tenant_id": request.user.tenant.id,
        "user_id": request.user.id,
    }

DJANGO_RLS = DjangoRLSSettings(
    RLS_FIELDS=["tenant_id", "user_id"],
    REQUEST_RESOLVER=my_custom_resolver,
)
```

### Custom Bypass Check

```python
def my_bypass_check(request):
    # Allow superusers and specific IPs
    if request.user.is_superuser:
        return True
    if request.META.get('REMOTE_ADDR') == '192.168.1.100':
        return True
    return False

DJANGO_RLS = DjangoRLSSettings(
    BYPASS_CHECK_RESOLVER=my_bypass_check,
)
```

### Migration User Setup

```python
DJANGO_RLS = DjangoRLSSettings(
    USE_DB_MIGRATION_USER=True,
    MIGRATION_USER="migration_user",
    MIGRATION_PASSWORD="secure_password",
)
```

## Next Steps

- [API Reference](../api/index.md) - Complete settings documentation
- [Resolvers](resolvers.md) - Learn about built-in and custom resolvers
- [Usage Examples](../usage/middleware.md) - See how to use these settings


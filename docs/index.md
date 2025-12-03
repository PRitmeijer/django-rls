# django-rls

**Django extension for PostgreSQL Row-Level Security (RLS)**

django-rls provides a seamless way to implement Row-Level Security (RLS) in your Django applications using PostgreSQL's native RLS features. It integrates with Django's middleware system and supports both traditional Django views and Strawberry GraphQL.

## Features

- 🔒 **PostgreSQL RLS Integration**: Leverage PostgreSQL's native Row-Level Security policies
- 🎯 **Automatic Field Management**: Auto-fill RLS fields on model creation
- 🔧 **Flexible Configuration**: Customizable resolvers for different contexts
- 🚀 **Strawberry GraphQL Support**: Built-in resolvers for Strawberry GraphQL
- 🛡️ **Bypass Controls**: Configurable bypass checks for superusers and special cases
- 📦 **Migration Support**: Safe migration handling with dedicated database users

## Quick Example

```python
# settings.py
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

```python
# middleware.py
MIDDLEWARE = [
    # ... other middleware
    'django_rls.middleware.RLSMiddleware',
    # ... rest of middleware
]
```

## Installation

```bash
pip install django-rls
```

## Documentation

- [Installation Guide](getting-started/installation.md)
- [Quick Start](getting-started/quick-start.md)
- [Configuration](configuration/settings.md)
- [Usage Examples](usage/middleware.md)

## Requirements

- Django >= 4.2, < 5.4
- PostgreSQL (RLS is PostgreSQL-only)
- Python >= 3.10, < 3.14

## License

MIT License - see [LICENSE](../LICENSE) file for details.

## Links

- [GitHub Repository](https://github.com/pritmeijer/django-rls)
- [Issue Tracker](https://github.com/pritmeijer/django-rls/issues)


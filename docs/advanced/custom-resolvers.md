# Custom Resolvers

Create custom resolvers to extract RLS context from your specific request structure.

For API documentation on resolver functions, see the [API Reference](../api/index.md) (search for `resolvers`).

## Request-Based Resolver

For Django views and REST APIs:

```python
from typing import Any, Dict
from django_rls.constants import RLSValue, RlsWildcard

def custom_request_resolver(request: Any) -> Dict[str, RLSValue]:
    """
    Extract RLS values from custom request structure.
    """
    # Example: Extract from custom headers
    tenant_id = request.META.get('HTTP_X_TENANT_ID')
    user_id = request.META.get('HTTP_X_USER_ID')
    
    context = {}
    
    if tenant_id:
        context['tenant_id'] = int(tenant_id)
    else:
        context['tenant_id'] = RlsWildcard.NONE
    
    if user_id:
        context['user_id'] = int(user_id)
    else:
        context['user_id'] = RlsWildcard.NONE
    
    return context

DJANGO_RLS = DjangoRLSSettings(
    REQUEST_RESOLVER=custom_request_resolver,
)
```

## JWT Token Resolver

Extract RLS values from JWT tokens:

```python
import jwt
from typing import Any, Dict
from django_rls.constants import RLSValue

def jwt_token_resolver(request: Any) -> Dict[str, RLSValue]:
    """
    Extract RLS values from JWT token in Authorization header.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return {}
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, 'your-secret-key', algorithms=['HS256'])
        return {
            'tenant_id': payload.get('tenant_id'),
            'user_id': payload.get('user_id'),
        }
    except jwt.InvalidTokenError:
        return {}

DJANGO_RLS = DjangoRLSSettings(
    REQUEST_RESOLVER=jwt_token_resolver,
)
```

## Multi-Tenant with Subdomain

Extract tenant from subdomain:

```python
from typing import Any, Dict
from django_rls.constants import RLSValue

def subdomain_tenant_resolver(request: Any) -> Dict[str, RLSValue]:
    """
    Extract tenant from subdomain.
    """
    host = request.get_host()
    subdomain = host.split('.')[0]
    
    # Look up tenant by subdomain
    from myapp.models import Tenant
    try:
        tenant = Tenant.objects.get(subdomain=subdomain)
        return {
            'tenant_id': tenant.id,
            'user_id': getattr(request.user, 'id', None) if request.user.is_authenticated else None,
        }
    except Tenant.DoesNotExist:
        return {}

DJANGO_RLS = DjangoRLSSettings(
    REQUEST_RESOLVER=subdomain_tenant_resolver,
)
```

## Complex Nested Resolver

Handle complex user relationships:

```python
from typing import Any, Dict
from django_rls.constants import RLSValue, RlsWildcard

def complex_user_resolver(request: Any) -> Dict[str, RLSValue]:
    """
    Extract RLS values from complex user relationships.
    """
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return {}
    
    context = {}
    
    # Primary tenant
    if hasattr(user, 'primary_tenant'):
        context['tenant_id'] = user.primary_tenant.id
    elif hasattr(user, 'tenant'):
        context['tenant_id'] = user.tenant.id
    else:
        context['tenant_id'] = RlsWildcard.NONE
    
    # User ID
    context['user_id'] = user.id
    
    # Organization (if exists)
    if hasattr(user, 'organization'):
        context['organization_id'] = user.organization.id
    
    # Department (if exists)
    if hasattr(user, 'department'):
        context['department_id'] = user.department.id
    
    return context

DJANGO_RLS = DjangoRLSSettings(
    RLS_FIELDS=['tenant_id', 'user_id', 'organization_id', 'department_id'],
    REQUEST_RESOLVER=complex_user_resolver,
)
```

## Testing Resolvers

Test your custom resolvers:

```python
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from myapp.resolvers import custom_request_resolver

def test_custom_resolver():
    factory = RequestFactory()
    request = factory.get('/')
    request.user = AnonymousUser()
    
    result = custom_request_resolver(request)
    assert result == {}
    
    # Test with authenticated user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user('test', 'test@example.com')
    request.user = user
    
    result = custom_request_resolver(request)
    assert 'user_id' in result
```

## Next Steps

- [Bypass Checks](bypass-checks.md) - Custom bypass logic
- [Resolvers](../configuration/resolvers.md) - Built-in resolvers


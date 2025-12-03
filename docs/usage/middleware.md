# Middleware

The `RLSMiddleware` is responsible for setting PostgreSQL session variables based on the current request context.

For complete API documentation, see the [API Reference](../api/index.md) (search for `RLSMiddleware`).

## How It Works

1. **Request Processing**: On each request, the middleware runs `REQUEST_RESOLVER` to get RLS context values
2. **Bypass Check**: If `BYPASS_CHECK_RESOLVER` returns `True`, all fields are set to `RlsWildcard.ALL`
3. **Session Variables**: PostgreSQL session variables are set (e.g., `SET rls.tenant_id = 123`)
4. **RLS Enforcement**: PostgreSQL RLS policies use `current_setting()` to read these variables

## Setup

Add the middleware to your `MIDDLEWARE` setting:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Add RLS middleware after AuthenticationMiddleware
    'django_rls.middleware.RLSMiddleware',
]
```

**Important**: Place `RLSMiddleware` after `AuthenticationMiddleware` so that `request.user` is available.

## Session Variables

The middleware sets PostgreSQL session variables in the format:

```
{rls.SESSION_NAMESPACE_PREFIX}.{field_name} = {value}
```

For example, with default settings:
- `rls.tenant_id = 123`
- `rls.user_id = 456`

These variables are available in PostgreSQL RLS policies:

```sql
CREATE POLICY tenant_isolation ON myapp_mymodel
    FOR ALL
    USING (tenant_id = current_setting('rls.tenant_id')::integer);
```

## Bypass Behavior

When `BYPASS_CHECK_RESOLVER` returns `True`, all RLS fields are set to a special wildcard value that bypasses RLS checks. This is useful for:

- Superuser access
- Admin interfaces
- System operations
- Specific IP addresses

## Database Vendor Check

The middleware automatically skips processing if the database vendor is not PostgreSQL (since RLS is PostgreSQL-only). This allows your application to work with other databases during development, though RLS won't be enforced.

## Example

```python
# settings.py
DJANGO_RLS = DjangoRLSSettings(
    RLS_FIELDS=["tenant_id", "user_id"],
    REQUEST_RESOLVER=default_request_user_resolver,
)

# On each request:
# 1. REQUEST_RESOLVER extracts: {"tenant_id": 123, "user_id": 456}
# 2. Middleware executes:
#    SET rls.tenant_id = 123;
#    SET rls.user_id = 456;
# 3. PostgreSQL RLS policies check these values
# 4. Only matching rows are returned
```

## Next Steps

- [Adding RLS](adding-rls.md) - How to add RLS policies to models
- [Migrations](migrations.md) - Handling migrations with RLS


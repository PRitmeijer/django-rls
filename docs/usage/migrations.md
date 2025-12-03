# Migrations

Handling migrations with Row-Level Security requires special consideration.

For API documentation on migration-related classes, see the [API Reference](../api/index.md) (search for `migrations`).

## Migration User

When using RLS, it's important to have a dedicated migration user that can bypass or work around RLS policies during migrations.

### Why?

- Migrations need to modify tables and policies
- The app's runtime user should be subject to RLS
- A separate migration user ensures migrations can run safely

### Setup

```python
# settings.py
DJANGO_RLS = DjangoRLSSettings(
    USE_DB_MIGRATION_USER=True,
    MIGRATION_USER="migration_user",
    MIGRATION_PASSWORD="secure_password",
)
```

### Creating the Migration User

In PostgreSQL:

```sql
CREATE USER migration_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE your_database TO migration_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO migration_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO migration_user;
```

## Migration Hooks

django-rls includes migration hooks that automatically handle RLS during migrations. The `makemigrations` command hook ensures RLS policies are properly managed.

## Running Migrations

With `USE_DB_MIGRATION_USER=True`, migrations will use the migration user credentials:

```bash
python manage.py migrate
```

## Manual Migration Steps

If you need to manually handle RLS during migrations:

1. **Temporarily disable RLS** (if needed):
   ```sql
   ALTER TABLE myapp_mymodel DISABLE ROW LEVEL SECURITY;
   ```

2. **Run the migration**:
   ```bash
   python manage.py migrate
   ```

3. **Re-enable RLS**:
   ```sql
   ALTER TABLE myapp_mymodel ENABLE ROW LEVEL SECURITY;
   ```

4. **Update policies** if schema changed:
   ```bash
   python manage.py add_rls myapp.MyModel
   ```

## Best Practices

1. **Always use a migration user** for production
2. **Test migrations** in a development environment first
3. **Review generated SQL** before applying policies
4. **Backup your database** before running migrations
5. **Document policy changes** in migration files

## Next Steps

- [Adding RLS](adding-rls.md) - How to add RLS to models
- [Configuration](../configuration/settings.md) - Migration user configuration


# Adding RLS

The `add_rls` management command helps you add Row-Level Security to your Django models.

For complete API documentation, see the [API Reference](../api/index.md) (search for `add_rls`).

## Basic Usage

```bash
python manage.py add_rls myapp.MyModel
```

This will:
- Enable RLS on the table
- Generate SQL for creating RLS policies
- Show you the SQL to run in PostgreSQL

## Interactive Mode

Run without arguments for interactive mode:

```bash
python manage.py add_rls
```

The command will prompt you to:
1. Select the app
2. Select the model
3. Choose which RLS fields to use
4. Configure policy options

## Field Selection

The command will automatically detect RLS fields from your `RLS_FIELDS` setting and suggest fields that exist on the model.

For models in `TENANT_APPS`, `tenant_id` will be suggested by default if the field exists.

## Generated SQL

The command generates SQL that you need to run in PostgreSQL. Example:

```sql
-- Enable RLS
ALTER TABLE myapp_mymodel ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY tenant_isolation ON myapp_mymodel
    FOR ALL
    USING (tenant_id = current_setting('rls.tenant_id')::integer);
```

## Policy Types

The command can generate different types of policies:

- **SELECT**: For read operations
- **INSERT**: For create operations
- **UPDATE**: For update operations
- **DELETE**: For delete operations
- **ALL**: For all operations (default)

## Multiple Fields

You can use multiple RLS fields:

```bash
python manage.py add_rls myapp.MyModel --fields tenant_id user_id
```

This will create policies that check both fields:

```sql
CREATE POLICY tenant_user_isolation ON myapp_mymodel
    FOR ALL
    USING (
        tenant_id = current_setting('rls.tenant_id')::integer
        AND user_id = current_setting('rls.user_id')::integer
    );
```

## Next Steps

- [Migrations](migrations.md) - How to handle migrations with RLS
- [Configuration](../configuration/settings.md) - Configure RLS settings


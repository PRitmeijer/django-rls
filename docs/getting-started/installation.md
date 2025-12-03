# Installation

## Requirements

- Django >= 4.2, < 5.4
- PostgreSQL (RLS is PostgreSQL-only feature)
- Python >= 3.10, < 3.14

## Install django-rls

Install django-rls using pip:

```bash
pip install django-rls
```

Or using uv:

```bash
uv add django-rls
```

## Database Setup

django-rls requires PostgreSQL as it relies on PostgreSQL's Row-Level Security features. Make sure your Django project is configured to use PostgreSQL:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_database',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Enable RLS in PostgreSQL

Row-Level Security must be enabled on the tables you want to protect. This is typically done when creating RLS policies, but you can also enable it manually:

```sql
ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;
```

The `add_rls` management command (see [Adding RLS](../usage/adding-rls.md)) will handle this automatically.

## Next Steps

- [Quick Start Guide](quick-start.md) - Get up and running quickly
- [Configuration](../configuration/settings.md) - Configure django-rls for your needs


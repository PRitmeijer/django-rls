# Quick Start

This guide will help you get django-rls up and running in your Django project.

## Step 1: Add Middleware

Add `RLSMiddleware` to your `MIDDLEWARE` setting:

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Add RLS middleware after AuthenticationMiddleware
    'django_rls.middleware.RLSMiddleware',
]
```

## Step 2: Configure Settings

Add `DJANGO_RLS` configuration to your settings:

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

## Step 3: Add RLS Fields to Models

Add the RLS fields to your models:

```python
# myapp/models.py
from django.db import models

class MyModel(models.Model):
    tenant_id = models.IntegerField()
    user_id = models.IntegerField()
    name = models.CharField(max_length=100)
    # ... other fields
```

## Step 4: Create RLS Policies

Use the management command to add RLS policies:

```bash
python manage.py add_rls myapp.MyModel
```

This will:
- Enable RLS on the table
- Create RLS policies based on your configuration
- Set up session variable checks

## Step 5: Create PostgreSQL Policies

The `add_rls` command will generate SQL for you. You'll need to create the actual policies in PostgreSQL. See [Adding RLS](../usage/adding-rls.md) for more details.

## What Happens Next?

Once configured:

1. **On each request**: The middleware extracts RLS values from the user/context
2. **Session variables are set**: PostgreSQL session variables are set (e.g., `rls.tenant_id`, `rls.user_id`)
3. **RLS policies enforce access**: PostgreSQL RLS policies check these session variables
4. **Auto-fill fields**: If `AUTO_SET_FIELDS=True`, fields are automatically set on model save

## Example: Accessing Data

```python
# views.py
from django.shortcuts import render
from myapp.models import MyModel

def my_view(request):
    # RLS middleware has already set session variables
    # PostgreSQL will automatically filter based on RLS policies
    items = MyModel.objects.all()  # Only returns items matching RLS context
    return render(request, 'template.html', {'items': items})
```

## Next Steps

- [Configuration Guide](../configuration/settings.md) - Learn about all configuration options
- [Adding RLS](../usage/adding-rls.md) - Detailed guide on adding RLS to models
- [Custom Resolvers](../advanced/custom-resolvers.md) - Create custom resolvers for your needs


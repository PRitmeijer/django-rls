import os
import re
import glob
import textwrap
from typing import List
from django.conf import settings as django_settings
from django.apps import apps
from django.core.management import call_command, BaseCommand, CommandError
from django.core.exceptions import FieldDoesNotExist

from django_rls.settings_type import DjangoRLSSettings
from django_rls.constants import RlsWildcard
from django_rls.utils import build_rls_using_clause, get_field_sql_type


class Command(BaseCommand):
    help = (
        "Creates a migration that adds a row-level security (RLS) policy to models.\n"
        "Usage: manage.py add_rls <app_label>"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label", type=str,
            help="The Django app label where the model(s) is defined."
        )

    def handle(self, *args, **options):
        self.rls_settings: DjangoRLSSettings = getattr(
            django_settings, "DJANGO_RLS", DjangoRLSSettings()
        )
        app_label = options["app_label"]

        # Determine target models
        app_config = apps.get_app_config(app_label)
        models = list(app_config.get_models())

        if not models:
            self.stdout.write(self.style.WARNING(f"No models found in app '{app_label}'."))
            return

        # Filter models and prepare configuration
        rls_config = {}
        
        # Check if app is in TENANT_APPS
        is_tenant_app = app_label in self.rls_settings.TENANT_APPS
        
        if not is_tenant_app:
             self.stdout.write(self.style.WARNING(f"App '{app_label}' is not in TENANT_APPS. Please add it to your settings to enable RLS generation."))
             return

        for model in models:
            model_name = model.__name__
            
            # Determine fields for this model - check all RLS_FIELDS if present
            # Use model._meta.get_field() to check for actual database fields,
            # not just Python attributes
            fields = []
            for rls_field in self.rls_settings.RLS_FIELDS:
                try:
                    model._meta.get_field(rls_field)
                    fields.append(rls_field)
                except FieldDoesNotExist:
                    # Field doesn't exist on this model, skip it
                    continue
            
            if not fields:
                # Skip models that don't have any RLS fields
                continue

            # Build using clause
            using_clause = self._build_using_clause(model, fields)
            rls_config[model_name] = using_clause

        if not rls_config:
            self.stdout.write(self.style.WARNING("No models matched criteria for RLS policy creation."))
            return

        # Generate migration
        migration_name = f"add_rls_policies_to_{app_label}"

        self.stdout.write("Creating an empty migration...")
        call_command("makemigrations", app_label, "--empty", "--name", migration_name)

        filepath = self._locate_migration_file(app_label, migration_name)
        dependencies_line = self._extract_dependencies(filepath)

        migration_content = self._build_migration_content(app_label, rls_config, dependencies_line)

        with open(filepath, "w") as f:
            f.write(migration_content)

        self.stdout.write(self.style.SUCCESS(f"Migration file created at {filepath}"))
        self.stdout.write(self.style.SUCCESS(f"Run `python manage.py migrate {app_label}` to apply RLS."))


    def _locate_migration_file(self, app_label, migration_name):
        app_config = apps.get_app_config(app_label)
        migrations_dir = os.path.join(app_config.path, "migrations")
        pattern = os.path.join(migrations_dir, f"*_{migration_name}.py")
        matches = glob.glob(pattern)
        if not matches:
            # Fallback for truncated names or slightly different naming by django
            # Try finding latest file
            all_migrations = sorted(glob.glob(os.path.join(migrations_dir, "*.py")))
            if all_migrations:
                 return all_migrations[-1]
            raise CommandError(f"Could not locate migration file matching pattern: {pattern}")
        return matches[0]

    def _extract_dependencies(self, filepath):
        with open(filepath, "r") as f:
            content = f.read()
        match = re.search(r"dependencies\s*=\s*(\[[^\]]*\])", content)
        return match.group(1) if match else "[]"
    
    def _build_using_clause(self, model, fields: List[str]) -> str:
        """
        Constructs the RLS USING clause with wildcard and null handling for each field.
        Each field's condition is wrapped in a CASE statement and joined via AND.
        """
        field_types = {}
        for field in fields:
            field_types[field] = get_field_sql_type(model, field)
            
        return build_rls_using_clause(
            fields, 
            field_types,
            self.rls_settings.SESSION_NAMESPACE_PREFIX
        )

    def _build_migration_content(self, app_label: str, rls_config: dict, dependencies_line: str) -> str:
        # rls_config is { "ModelName": "using_clause" }
        
        # Build config dict with proper escaping
        config_items = []
        for model, clause in rls_config.items():
            # Use repr() to safely escape the clause string
            # This handles any special characters, quotes, etc.
            config_items.append(f"    {model!r}: {clause!r}")
        config_str = "{\n" + ",\n".join(config_items) + "\n}"

        template = '''"""
Auto-generated RLS migration.
"""

from django.db import migrations
from django.db.backends.ddl_references import Statement, Table
from django.apps import apps

from django_rls.migrations import RunDynamicSQL

APP_LABEL = {app_label}
RLS_CONFIG = {config_str}

def get_create_sql(schema_editor):
    statements = []
    for model_name, using_clause in RLS_CONFIG.items():
        model = apps.get_model(APP_LABEL, model_name)
        table_name = model._meta.db_table
        policy_name = f"{{table_name}}_rls_policy"
        # Format using_clause as single line for Statement template
        using_clause_single_line = " ".join(using_clause.split())
        stmt = Statement(
            "DROP POLICY IF EXISTS %(policy_name)s ON %(table_name)s;"
            "CREATE POLICY %(policy_name)s ON %(table_name)s FOR ALL USING (%(using_clause)s) WITH CHECK (%(using_clause)s);"
            "ALTER TABLE %(table_name)s ENABLE ROW LEVEL SECURITY;"
            "ALTER TABLE %(table_name)s FORCE ROW LEVEL SECURITY;",
            policy_name=policy_name,
            table_name=Table(table_name, schema_editor.quote_name),
            using_clause=using_clause_single_line
        )
        statements.append(str(stmt))
    return "\\n".join(statements)

def get_drop_sql(schema_editor):
    statements = []
    for model_name, _ in RLS_CONFIG.items():
        model = apps.get_model(APP_LABEL, model_name)
        table_name = model._meta.db_table
        policy_name = f"{{table_name}}_rls_policy"
        stmt = Statement(
            "ALTER TABLE %(table_name)s NO FORCE ROW LEVEL SECURITY;"
            "ALTER TABLE %(table_name)s DISABLE ROW LEVEL SECURITY;"
            "DROP POLICY IF EXISTS %(policy_name)s ON %(table_name)s;",
            policy_name=policy_name,
            table_name=Table(table_name, schema_editor.quote_name),
        )
        statements.append(str(stmt))
    return "\\n".join(statements)

class Migration(migrations.Migration):
    dependencies = {dependencies_line}
    operations = [
        RunDynamicSQL(create_func=get_create_sql, drop_func=get_drop_sql),
    ]
'''
        return textwrap.dedent(template).format(
            app_label=repr(app_label),
            config_str=config_str,
            dependencies_line=dependencies_line
        )

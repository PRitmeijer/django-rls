import os
import re
import glob
from django.conf import settings as django_settings
from django.apps import apps
from django.core.management import call_command, BaseCommand, CommandError

from django_rls.settings_type import DjangoRLSSettings
from django_rls.constants import RlsWildcard


class Command(BaseCommand):
    help = (
        "Creates a migration that adds a row-level security (RLS) policy to a model "
        "based on fields selected from ENFORCE_FIELDS.\n"
        "Usage: manage.py add_rls <app_label> <model_name> --fields tenant_id user_id"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label", type=str,
            help="The Django app label where the model is defined."
        )
        parser.add_argument(
            "model_name", type=str,
            help="The name of the model (case insensitive) to add RLS to."
        )
        parser.add_argument(
            "--fields", nargs="+", required=True,
            help="List of fields to enforce RLS on (must be part of ENFORCE_FIELDS)."
        )

    def handle(self, *args, **options):
        self.rls_settings: DjangoRLSSettings = getattr(
            django_settings, "DJANGO_RLS", DjangoRLSSettings()
        )
        app_label = options["app_label"]
        model_name = options["model_name"]
        enforce_fields = options["fields"]

        model = self._get_model(app_label, model_name)

        # Validate the requested fields
        self._validate_fields(model, enforce_fields)

        migration_name = f"add_rls_policy_to_{model_name.lower()}"
        self.stdout.write("Creating an empty migration...")
        call_command("makemigrations", app_label, "--empty", "--name", migration_name)

        filepath = self._locate_migration_file(app_label, migration_name)
        dependencies_line = self._extract_dependencies(filepath)

        # Build the policy condition
        condition = " AND ".join([
            f"{field} = current_setting('{self.rls_settings.SESSION_NAMESPACE_PREFIX}.{field}')::{self._get_field_sql_type(model, field)}"
            for field in enforce_fields
        ])

        migration_content = self._build_migration_content(app_label, model_name, dependencies_line, condition)

        with open(filepath, "w") as f:
            f.write(migration_content)

        self.stdout.write(self.style.SUCCESS(f"✅ Migration file created at {filepath}"))
        self.stdout.write(self.style.SUCCESS(f"▶ Run `python manage.py migrate {app_label}` to apply RLS."))

    def _get_model(self, app_label, model_name):
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            raise CommandError(f"Model '{model_name}' not found in app '{app_label}'.")

        return model

    def _validate_fields(self, model, enforce_fields):
        for field in enforce_fields:
            if field not in self.rls_settings.ENFORCE_FIELDS:
                raise CommandError(f"Field '{field}' is not listed in ENFORCE_FIELDS.")
            if not hasattr(model, field):
                raise CommandError(f"Model does not have field '{field}'.")

    def _locate_migration_file(self, app_label, migration_name):
        app_config = apps.get_app_config(app_label)
        migrations_dir = os.path.join(app_config.path, "migrations")
        pattern = os.path.join(migrations_dir, f"*_{migration_name}.py")
        matches = glob.glob(pattern)
        if not matches:
            raise CommandError(f"Could not locate migration file matching pattern: {pattern}")
        return matches[0]

    def _extract_dependencies(self, filepath):
        with open(filepath, "r") as f:
            content = f.read()
        match = re.search(r"dependencies\s*=\s*(\[[^\]]*\])", content)
        return match.group(1) if match else "[]"
    
    def _build_using_clause(self, model, fields: list[str]) -> str:
        """
        Constructs the RLS USING clause with wildcard and null handling for each field.
        Each field's condition is wrapped in a CASE statement and joined via AND.
        """
        prefix = self.rls_settings.SESSION_NAMESPACE_PREFIX
        clauses = []

        for field in fields:
            sql_type = self._get_field_sql_type(model, field)
            clause = f"""(
                CASE
                    WHEN current_setting('{prefix}.{field}', true) IS NULL THEN FALSE
                    WHEN current_setting('{prefix}.{field}') = '{RlsWildcard.NONE.value}' THEN FALSE
                    WHEN current_setting('{prefix}.{field}') = '{RlsWildcard.ALL.value}' THEN TRUE
                    ELSE {field} = current_setting('{prefix}.{field}')::{sql_type}
                END
            )"""
            clauses.append(clause)

        return " AND\n".join(clauses)


    def _get_field_sql_type(self, model, field_name):
        field = model._meta.get_field(field_name)
        return {
            "IntegerField": "int",
            "BigIntegerField": "bigint",
            "UUIDField": "uuid",
            "CharField": "text",
            "BooleanField": "boolean",
        }.get(field.get_internal_type(), "text")  # fallback

    def _build_migration_content(self, app_label: str, model_name: str, dependencies_line: str, using_clause: str) -> str:
        return f'''"""
    Auto-generated RLS migration for {model_name}.
    """

    from django.db import migrations
    from django.db.backends.ddl_references import Statement, Table
    from django.apps import apps

    from pegamento_sec.migrations import RunDynamicSQL

    APP_LABEL = {app_label!r}
    MODEL_NAME = {model_name!r}

    def get_create_sql(schema_editor):
        model = apps.get_model(APP_LABEL, MODEL_NAME)
        table_name = model._meta.db_table
        policy_name = f"{{table_name}}_rls_policy"
        return str(Statement(
            "CREATE POLICY %(policy_name)s ON %(table_name)s USING ({using_clause});"
            "ALTER TABLE %(table_name)s ENABLE ROW LEVEL SECURITY;"
            "ALTER TABLE %(table_name)s FORCE ROW LEVEL SECURITY;",
            policy_name=policy_name,
            table_name=Table(table_name, schema_editor.quote_name),
            using_clause=""" + '"""' + using_clause + '"""' + f"""
        ))

    def get_drop_sql(schema_editor):
        model = apps.get_model(APP_LABEL, MODEL_NAME)
        table_name = model._meta.db_table
        policy_name = f"{{table_name}}_rls_policy"
        return str(Statement(
            "ALTER TABLE %(table_name)s NO FORCE ROW LEVEL SECURITY;"
            "ALTER TABLE %(table_name)s DISABLE ROW LEVEL SECURITY;"
            "DROP POLICY IF EXISTS %(policy_name)s ON %(table_name)s;",
            policy_name=policy_name,
            table_name=Table(table_name, schema_editor.quote_name),
        ))

    class Migration(migrations.Migration):
        dependencies = {dependencies_line}
        operations = [
            RunDynamicSQL(create_func=get_create_sql, drop_func=get_drop_sql),
        ]
    '''.replace("{using_clause}", using_clause)

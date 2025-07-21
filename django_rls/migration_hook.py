import sys
from django.conf import settings as django_settings
from django_rls.settings_type import DjangoRLSSettings

def configure_rls_migration_user() -> None:
    rls_settings: DjangoRLSSettings = getattr(
        django_settings, "DJANGO_RLS", DjangoRLSSettings()
    )

    if (
        rls_settings.USE_DB_MIGRATION_USER
        and "manage.py" in sys.argv[0]
        and any(cmd in sys.argv for cmd in ["migrate", "makemigrations"])
    ):
        db_name = "default"
        db = django_settings.DATABASES[db_name]

        if not rls_settings.MIGRATION_USER or not rls_settings.MIGRATION_PASSWORD:
            raise RuntimeError("MIGRATION_USER and MIGRATION_PASSWORD must be set if USE_DB_MIGRATION_USER is True.")

        db["USER"] = rls_settings.MIGRATION_USER
        db["PASSWORD"] = rls_settings.MIGRATION_PASSWORD

        print(f"✅ RLS migration DB user active for {db_name}: {rls_settings.MIGRATION_USER}")
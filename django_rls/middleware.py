from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.conf import settings as django_settings
from typing import Any

from django_rls.settings_type import DjangoRLSSettings
from django_rls.constants import RlsWildcard, DBSafeValue


class RLSMiddleware(MiddlewareMixin):
    """
    Middleware that sets PostgreSQL session variables based on RLS context.

    - If BYPASS_CHECK_RESOLVER returns True, sets all session vars to RlsWildcard.ALL.
    - Otherwise uses VALUE_RESOLVER to fetch per-field RLS values.
    - Only sets session vars for fields in ENFORCE_FIELDS.

    These variables are used in PostgreSQL RLS policies with current_setting().
    """

    def process_request(self, request: Any):
        rls_settings: DjangoRLSSettings = getattr(
            django_settings, "DJANGO_RLS", DjangoRLSSettings()
        )

        # 1. Bypass check
        if rls_settings.BYPASS_CHECK_RESOLVER(request):
            rls_context = {
                field: RlsWildcard.ALL for field in rls_settings.ENFORCE_FIELDS
            }
        else:
            rls_context = rls_settings.REQUEST_RESOLVER(request)

        # 2. Set PostgreSQL session vars
        with connection.cursor() as cursor:
            for field, value in rls_context.items():
                if field not in rls_settings.ENFORCE_FIELDS:
                    continue

                if isinstance(value, RlsWildcard):
                    db_value : DBSafeValue = value.value  # e.g., SPECIAL_CASE_ALL

                if value is None:
                    db_value = RlsWildcard.NONE.value

                session_key = f"{rls_settings.SESSION_NAMESPACE_PREFIX}.{field}"
                cursor.execute(f"SET {session_key} = %s", [db_value])

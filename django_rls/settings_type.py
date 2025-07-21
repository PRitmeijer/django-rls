from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
)

from django_rls.constants import RLSValue
from django_rls.resolvers import default_request_user_resolver, default_rls_bypass_check

T = TypeVar("T")

class DjangoSetting(Generic[T]):
    __slots__ = ("setting", "cached")

    def __init__(self, setting: str, value: T | None = None):
        self.setting = setting
        self.cached: T | None = value

    @property
    def value(self) -> T:
        if self.cached:  # slotted classes can't use cached property (without __dict__)
            return self.cached
        from django.conf import settings

        final = settings
        for attr in self.setting.split("."):
            final = getattr(final, attr)

        return final  # type: ignore

    @classmethod
    def override(cls, value: T) -> "DjangoSetting":
        return DjangoSetting(setting="", value=value)


@dataclass
class DjangoRLSSettings:
    """
    DjangoRLSSettings

    Configuration for enabling PostgreSQL Row-Level Security (RLS)
    across selected Django models, with enforcement scoped by model fields
    and session variables.

    This includes dynamic policy generation, session binding, and model auto-filling.
    """

    ENFORCE_FIELDS: List[str] = field(default_factory=list)
    """
    A global list of field names that are allowed to be enforced through PostgreSQL RLS.

    These fields represent values like `tenant_id`, `user_id`, etc., that may be present
    on multiple models. This list doesn't enforce RLS directly but defines which fields
    are eligible for enforcement when creating RLS policies (e.g., through the `add_rls` command).

    The actual models and fields to apply RLS to are chosen at command-line args in `manage.py add_rls`.

    Example:
        ENFORCE_FIELDS = ["tenant_id", "user_id"]

    PostgreSQL RLS policies will use session variables like:
        current_setting('rls.tenant_id')
        current_setting('rls.user_id')
    """

    REQUEST_RESOLVER: Callable[[Any], Dict[str, RLSValue]] = default_request_user_resolver
    """
    A function that returns the current RLS context to set into PostgreSQL session variables.

    Example return:
        {
            "user_id": 1,
            "tenant_id": 4,
            "public":true,
        }

    This value is used for:
    - Setting session variables like `SET rls.tenant_id = 123`
    - Auto-filling fields on models if AUTO_SET_FIELDS = True

    You can plug in a Django request-based or Strawberry GraphQL resolver here.
    """

    BYPASS_CHECK_RESOLVER: Callable[[Any], bool] = default_rls_bypass_check
    """
    Optional function to determine if RLS should be bypassed entirely for a request or context.

    If this returns True, all fields in ENFORCE_FIELDS will be set to RlsWildcard.ALL.

    Example use case:
        - Allow superusers to bypass RLS enforcement
        - Allow specific IPs or roles to see all data
    """

    AUTO_SET_FIELDS: bool = False #TODO
    """
    If True, models listed in `ENFORCE_POLICIES` will have their scoped fields automatically
    set on creation/save based on the current session context (as resolved by `REQUEST_RESOLVER`).

    For example, if a model requires `tenant_id` and `user_id`, and the current session provides:
        {"tenant_id": 123, "user_id": 456}

    Then calling `model.save()` will auto-fill these fields before validation (unless explicitly set).
    This helps prevent accidental leaks or incomplete data in a multi-tenant system.
    """

    SKIP_MODELS: Optional[List[str]]= field(default_factory=list) #TODO
    """
    Optional list of model paths (e.g., `"app.Model"`) to explicitly exclude from Auto Set Field setting even if they match `ENFORCE_POLICIES`.

    Example:
        SKIP_MODELS = [
            "core.AuditLog",
            "sessions.Session"
        ]
    """

    SESSION_NAMESPACE_PREFIX: str = "rls"
    """
    Prefix for PostgreSQL session variables used in `current_setting()`.

    Changing this will break existing RLS policies unless manually updated.
    """

    USE_DB_MIGRATION_USER: bool = False
    """
    If True, migrations (and potentially startup checks) that apply RLS policies
    will explicitly use the `MIGRATION_USER` and `MIGRATION_PASSWORD` credentials.

    This ensures that runtime roles (used by the app) are properly enforced by RLS as they are not the owner of the RLS policy.
    """

    MIGRATION_USER: Optional[str] = None
    """
    Username of the dedicated RLS-safe migration user.

    This user must:
    - Have sufficient privileges to create policies
    - Be separate from the app's runtime role
    """

    MIGRATION_PASSWORD: Optional[str] = None
    """
    Password for the MIGRATION_USER.
    """

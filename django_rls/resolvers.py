from typing import Any, Dict, Union
from django_rls.constants import RlsWildcard, RLSValue
from django_rls.settings import django_rls_settings

def default_request_user_resolver(request: Any) -> Dict[str, RLSValue]:
    """
    Default RLS resolver for standard Django requests in REQUEST_RESOLVER.

    Dynamically builds a dict based on the fields in ENFORCE_FIELDS.
    Extracts the value from request.user or request.user.{field}.

    If user is not authenticated, returns an empty dict.
    """
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {}

    context: Dict[str, RLSValue] = {}

    for field in django_rls_settings.ENFORCE_FIELDS:
        value = getattr(user, field, None)

        if value is None:
            parent_attr = getattr(user, field.split("_")[0], None)
            if parent_attr:
                value = getattr(parent_attr, "id", None)

        context[field] = value if value is not None else RlsWildcard.NONE

    return context


def default_rls_bypass_check(request: Any) -> bool:
    """
    Returns True if the current request's user is a superuser.
    Default for BYPASS_CHECK_RESOLVER.
    """
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bool(getattr(user, "is_superuser", False))



def strawberry_context_user_resolver(info: Any) -> Dict[str, RLSValue]:
    """
    Strawberry GraphQL version of the default resolver.

    Reads info.context.user and resolves all ENFORCE_FIELDS dynamically.
    """
    user = getattr(getattr(info, "context", None), "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {}

    context: Dict[str, RLSValue] = {}

    for field in django_rls_settings.ENFORCE_FIELDS:
        value = getattr(user, field, None)

        if value is None:
            parent_attr = getattr(user, field.split("_")[0], None)
            if parent_attr:
                value = getattr(parent_attr, "id", None)

        context[field] = value if value is not None else RlsWildcard.NONE

    return context

def strawberry_rls_bypass_check(info: Any) -> bool:
    """
    Returns True if the info.context.user is a superuser.
    Intended for use as a BYPASS_CHECK_RESOLVER.
    """
    user = getattr(getattr(info, "context", None), "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bool(getattr(user, "is_superuser", False))




__all__ = [
    "default_request_user_resolver",
    "default_rls_bypass_check",
    "strawberry_context_user_resolver",
    "strawberry_rls_bypass_check"
]
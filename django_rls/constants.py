from enum import Enum
from typing import Union
import uuid

class RlsWildcard(Enum):
    ALL = "SPECIAL_CASE_ALL"
    NONE = "SPECIAL_CASE_NONE"

# Values that can be returned by REQUEST_RESOLVER
# Includes UUID since RLS can filter on UUID fields
RLSValue = Union[int, bool, uuid.UUID, RlsWildcard]

# Values that can be safely passed to PostgreSQL via psycopg2
# psycopg2 handles UUID conversion automatically
DBSafeValue = Union[int, bool, str, uuid.UUID]
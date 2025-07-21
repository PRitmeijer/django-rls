from enum import Enum

from typing import Union

class RlsWildcard(Enum):
    ALL = "SPECIAL_CASE_ALL"
    NONE = "SPECIAL_CASE_NONE"

RLSValue = Union[int, bool, RlsWildcard]

DBSafeValue = Union[int, bool, str]
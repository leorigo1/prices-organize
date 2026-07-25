from dataclasses import dataclass
from typing import Any


@dataclass
class SearchSimilarRequest:
    reference_text: str
    payload: Any


@dataclass
class SearchSimilarResponse:
    payload: Any

import json
from typing import Any

from openai_service import OpenAIService
from dtos import SearchSimilarRequest, SearchSimilarResponse


class SearchService:
    def __init__(self) -> None:
        self.openai_service = OpenAIService()

    def search_similar(self, request: SearchSimilarRequest) -> SearchSimilarResponse:
        filtered_payload = self.openai_service.search_similar(
            payload=request.payload,
            reference_text=request.reference_text,
            top_k=5,
        )
        return SearchSimilarResponse(payload=filtered_payload)

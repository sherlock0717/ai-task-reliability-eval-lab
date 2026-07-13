from __future__ import annotations

from typing import Any

from .base import ModelProvider, ProviderRequest, ProviderResponse


class ScriptedProvider(ModelProvider):
    provider_id = "scripted"

    def __init__(self, responses: dict[str, dict[str, Any]], fallback: Any = "") -> None:
        self._responses = responses
        self._fallback = fallback

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        case_responses = self._responses.get(request.case_id, {})
        content = case_responses.get(request.stage, case_responses.get("default", self._fallback))
        return ProviderResponse(content=content, model=self.provider_id)

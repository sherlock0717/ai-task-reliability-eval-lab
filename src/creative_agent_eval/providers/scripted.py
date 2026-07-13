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
        scripted = case_responses.get(request.stage, case_responses.get("default", self._fallback))
        if isinstance(scripted, dict) and any(
            key in scripted for key in ("content", "tool_calls", "usage", "model")
        ):
            return ProviderResponse(
                content=scripted.get("content"),
                tool_calls=scripted.get("tool_calls") or [],
                usage=scripted.get("usage") or {},
                model=scripted.get("model", self.provider_id),
            )
        return ProviderResponse(content=scripted, model=self.provider_id)

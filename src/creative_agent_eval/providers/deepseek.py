from __future__ import annotations

import os
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .base import ModelProvider, ProviderRequest, ProviderResponse


class DeepSeekConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_url: str = "https://api.deepseek.com"
    model: Literal["deepseek-v4-flash", "deepseek-v4-pro"] = "deepseek-v4-flash"
    thinking: bool = True
    reasoning_effort: Literal["high", "max"] = "high"
    timeout_seconds: float = Field(default=120.0, gt=0)


class DeepSeekProvider(ModelProvider):
    provider_id = "deepseek"

    def __init__(
        self,
        config: DeepSeekConfig | None = None,
        api_key: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.config = config or DeepSeekConfig()
        self._api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self._client = client
        self._owns_client = client is None

    def _get_client(self) -> httpx.Client:
        if not self._api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured")
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.base_url.rstrip("/"),
                timeout=self.config.timeout_seconds,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        messages = request.messages or [{"role": "user", "content": request.prompt}]
        payload: dict[str, object] = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
        }
        if request.tools:
            payload["tools"] = request.tools
        if self.config.thinking:
            payload["thinking"] = {"type": "enabled"}
            payload["reasoning_effort"] = self.config.reasoning_effort
        else:
            payload["thinking"] = {"type": "disabled"}

        response = self._get_client().post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]
        usage = {
            key: int(value)
            for key, value in data.get("usage", {}).items()
            if isinstance(value, int)
        }
        return ProviderResponse(
            content=message.get("content"),
            tool_calls=message.get("tool_calls") or [],
            usage=usage,
            model=str(data.get("model", self.config.model)),
        )

    def close(self) -> None:
        if self._owns_client and self._client is not None:
            self._client.close()
            self._client = None

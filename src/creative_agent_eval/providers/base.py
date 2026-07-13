from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProviderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    stage: str
    prompt: str
    messages: list[dict[str, str]] = Field(default_factory=list)
    tools: list[dict[str, Any]] = Field(default_factory=list)
    seed: int = 0


class ProviderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: Any
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, int] = Field(default_factory=dict)
    model: str = "scripted"


class ModelProvider(ABC):
    provider_id: str

    @abstractmethod
    def generate(self, request: ProviderRequest) -> ProviderResponse:
        raise NotImplementedError

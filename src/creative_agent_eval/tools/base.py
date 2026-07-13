from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    call_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    call_id: str
    name: str
    ok: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error_type: str | None = None
    error_message: str | None = None


class ToolContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    allowed_tools: set[str] = Field(default_factory=set)
    fixture: dict[str, Any] = Field(default_factory=dict)


ToolHandler = Callable[[dict[str, Any], ToolContext], dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, name: str, handler: ToolHandler) -> None:
        if not name:
            raise ValueError("tool name must not be empty")
        if name in self._handlers:
            raise ValueError(f"tool already registered: {name}")
        self._handlers[name] = handler

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def call(self, request: ToolCall, context: ToolContext) -> ToolResult:
        if context.allowed_tools and request.name not in context.allowed_tools:
            return ToolResult(
                call_id=request.call_id,
                name=request.name,
                ok=False,
                error_type="tool_not_allowed",
                error_message=f"{request.name} is not allowed for {context.case_id}",
            )
        handler = self._handlers.get(request.name)
        if handler is None:
            return ToolResult(
                call_id=request.call_id,
                name=request.name,
                ok=False,
                error_type="tool_not_registered",
                error_message=f"tool is not registered: {request.name}",
            )
        try:
            output = handler(request.arguments, context)
            return ToolResult(call_id=request.call_id, name=request.name, ok=True, output=output)
        except (KeyError, TypeError, ValueError) as exc:
            return ToolResult(
                call_id=request.call_id,
                name=request.name,
                ok=False,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

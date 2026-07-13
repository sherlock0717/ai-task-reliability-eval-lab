from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .base import ToolCall, ToolContext, ToolRegistry, ToolResult


class ToolFaultPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["timeout_first_call", "error_first_call", "empty_first_call"]
    target_tool: str | None = None
    recoverable: bool = True
    error_message: str = "injected recoverable tool fault"


class FaultInjectingRegistry:
    """Wrap a deterministic registry and inject a predeclared tool condition.

    The wrapper keeps call counts in memory for one run. It never changes fixture
    data and delegates all later calls to the original registry.
    """

    def __init__(self, base: ToolRegistry, plan: ToolFaultPlan) -> None:
        self._base = base
        self.plan = plan
        self._calls: Counter[str] = Counter()

    def names(self) -> tuple[str, ...]:
        return self._base.names()

    def call(self, request: ToolCall, context: ToolContext) -> ToolResult:
        self._calls[request.name] += 1
        is_target = self.plan.target_tool is None or request.name == self.plan.target_tool
        should_inject = is_target and self._calls[request.name] == 1
        if should_inject:
            if self.plan.mode == "empty_first_call":
                return ToolResult(
                    call_id=request.call_id,
                    name=request.name,
                    ok=True,
                    output={"status": "empty_injected_result"},
                )
            error_type = "timeout" if self.plan.mode == "timeout_first_call" else "injected_error"
            return ToolResult(
                call_id=request.call_id,
                name=request.name,
                ok=False,
                error_type=error_type,
                error_message=self.plan.error_message,
            )
        return self._base.call(request, context)

    def call_count(self, tool_name: str) -> int:
        return self._calls[tool_name]

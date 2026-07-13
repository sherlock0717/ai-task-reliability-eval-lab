from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from ..models import EvalCase
from ..providers import ModelProvider, ProviderRequest
from ..runtime import RunTrace, TraceRecorder
from ..tools import ToolCall, ToolContext, ToolRegistry


def _tool_specs(case: EvalCase) -> list[dict[str, Any]]:
    specs = []
    for tool in case.tool_environment.get("tools", []):
        properties = {
            key: {"type": "string", "description": str(value)}
            for key, value in tool.get("inputs", {}).items()
        }
        specs.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": list(properties),
                        "additionalProperties": False,
                    },
                },
            }
        )
    return specs


def _arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("tool arguments must be an object")


@dataclass(frozen=True)
class ToolGroundedLoop:
    loop_id: str = "L3"
    max_retries_per_call: int = 1

    def run(
        self,
        case: EvalCase,
        provider: ModelProvider,
        registry: ToolRegistry,
        fixture: dict[str, Any],
        seed: int = 0,
    ) -> RunTrace:
        recorder = TraceRecorder(case.case_id, self.loop_id, provider.provider_id, seed)
        recorder.emit("run_started", {"title": case.title})
        tool_specs = _tool_specs(case)
        allowed_tools = {item["function"]["name"] for item in tool_specs}
        max_calls = int(case.tool_environment.get("max_tool_calls", 8))
        try:
            plan = provider.generate(
                ProviderRequest(
                    case_id=case.case_id,
                    stage="tool_plan",
                    prompt=f"{case.prompt}\n请识别需要外部验证的关键假设，并在需要时调用工具。",
                    tools=tool_specs,
                    seed=seed,
                )
            )
            recorder.emit("model_responded", {"stage": "tool_plan", "model": plan.model})
            recorder.emit("tool_plan_created", {"content": plan.content, "tool_call_count": len(plan.tool_calls)})
            results = []
            context = ToolContext(case_id=case.case_id, allowed_tools=allowed_tools, fixture=fixture)
            for index, raw_call in enumerate(plan.tool_calls[:max_calls]):
                function = raw_call.get("function", raw_call)
                request = ToolCall(
                    call_id=str(raw_call.get("id", f"tool-{index + 1}")),
                    name=str(function["name"]),
                    arguments=_arguments(function.get("arguments", {})),
                )
                attempt = 0
                while True:
                    recorder.emit("tool_requested", {**request.model_dump(mode="json"), "attempt": attempt + 1})
                    result = registry.call(request, context)
                    if result.ok:
                        results.append(result.model_dump(mode="json"))
                        recorder.emit("tool_returned", {**result.model_dump(mode="json"), "attempt": attempt + 1})
                        break
                    recorder.emit("tool_failed", {**result.model_dump(mode="json"), "attempt": attempt + 1})
                    if attempt >= self.max_retries_per_call:
                        results.append(result.model_dump(mode="json"))
                        break
                    attempt += 1
                    recorder.emit(
                        "tool_retry",
                        {
                            "call_id": request.call_id,
                            "name": request.name,
                            "next_attempt": attempt + 1,
                            "reason": result.error_type,
                        },
                    )
            recorder.emit("revalidation_started", {"tool_result_count": len(results)})
            final_prompt = (
                "请依据工具证据修订并输出最终结果。\n"
                f"题目：{case.prompt}\n初步计划：{json.dumps(plan.content, ensure_ascii=False)}\n"
                f"工具结果：{json.dumps(results, ensure_ascii=False)}"
            )
            final = provider.generate(
                ProviderRequest(case_id=case.case_id, stage="final", prompt=final_prompt, seed=seed)
            )
            recorder.emit("model_responded", {"stage": "final", "model": final.model})
            recorder.emit("revision_created", {"content": final.content, "tool_results": len(results)})
            recorder.emit(
                "revalidation_completed",
                {
                    "tool_result_count": len(results),
                    "successful_tool_results": sum(bool(item.get("ok")) for item in results),
                },
            )
            return recorder.complete(final.content)
        except Exception as exc:
            return recorder.fail(exc)

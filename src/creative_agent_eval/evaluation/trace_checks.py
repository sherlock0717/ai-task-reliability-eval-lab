from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from ..models import EvalCase
from ..runtime import RunTrace
from .oracles import OracleResult, classify_check


class TraceEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    loop_id: str
    results: list[OracleResult] = Field(default_factory=list)
    status_counts: dict[str, int] = Field(default_factory=dict)


def _result(
    check_id: str,
    status: str,
    evidence: list[str],
    message: str,
    severity: str = "major",
) -> OracleResult:
    return OracleResult(
        check_id=check_id,
        status=status,  # type: ignore[arg-type]
        evidence=evidence,
        message=message,
        severity=severity,  # type: ignore[arg-type]
        capability="trace_required",
    )


def evaluate_trace_check(case: EvalCase, check_id: str, trace: RunTrace) -> OracleResult:
    normalized = check_id.casefold()
    event_types = [event.event_type for event in trace.events]

    if "event_acknowledged" in normalized:
        if trace.has_event("event_acknowledged"):
            return _result(check_id, "pass", ["event_acknowledged"], "Trace记录了对外部事件的确认。")
        if trace.has_event("tool_failed") and trace.has_event("tool_retry"):
            return _result(
                check_id,
                "pass",
                ["tool_failed", "tool_retry"],
                "Trace记录了工具异常并进入重试流程。",
            )
        return _result(
            check_id,
            "needs_review",
            event_types,
            "Trace中没有可识别的外部事件确认记录。",
        )

    if "critical_assumption_coverage" in normalized or "assumption" in normalized:
        plans = trace.events_of("tool_plan_created")
        requests = trace.events_of("tool_requested")
        returns = trace.events_of("tool_returned")
        if requests and returns:
            return _result(
                check_id,
                "pass",
                [f"tool_requests={len(requests)}", f"tool_returns={len(returns)}"],
                "关键假设进入了工具核验流程。",
            )
        if plans:
            return _result(
                check_id,
                "needs_review",
                [f"tool_plans={len(plans)}", f"tool_requests={len(requests)}"],
                "存在工具计划，但没有足够调用结果确认假设覆盖。",
            )
        return _result(
            check_id,
            "needs_review",
            [],
            "当前Loop没有记录关键假设核验阶段。",
        )

    if any(token in normalized for token in ("verification", "evidence", "tool")):
        successful = [event for event in trace.events_of("tool_returned") if event.payload.get("ok")]
        failed = trace.events_of("tool_failed")
        if successful:
            return _result(
                check_id,
                "pass",
                [f"successful_tool_results={len(successful)}", f"failed_tool_results={len(failed)}"],
                "Trace中存在成功工具证据。",
            )
        if failed:
            return _result(
                check_id,
                "fail",
                [f"failed_tool_results={len(failed)}"],
                "工具调用失败且没有成功结果。",
                severity="critical",
            )
        return _result(check_id, "needs_review", [], "Trace中没有工具证据。")

    if "revalidation" in normalized:
        if trace.has_event("revalidation_started") and trace.has_event("revalidation_completed"):
            return _result(
                check_id,
                "pass",
                ["revalidation_started", "revalidation_completed"],
                "Trace记录了重新验证的开始与完成。",
            )
        return _result(check_id, "needs_review", event_types, "未形成完整的重新验证事件对。")

    if "terminal_decision" in normalized:
        if trace.has_event("stop_decision"):
            decisions = [str(event.payload.get("decision")) for event in trace.events_of("stop_decision")]
            return _result(check_id, "pass", decisions, "Trace记录了显式停止决策。")
        return _result(check_id, "fail", [], "Trace缺少显式停止决策。", severity="critical")

    return _result(check_id, "needs_review", event_types, "当前Trace检查需要Case级事件定义。", severity="minor")


def evaluate_trace_checks(case: EvalCase, trace: RunTrace) -> TraceEvaluation:
    selected = [
        check_id
        for check_id in case.automatic_checks
        if classify_check(check_id) == "trace_required"
        or "revalidation" in check_id.casefold()
        or "terminal_decision" in check_id.casefold()
    ]
    results = [evaluate_trace_check(case, check_id, trace) for check_id in selected]
    counts = Counter(result.status for result in results)
    return TraceEvaluation(
        case_id=case.case_id,
        loop_id=trace.loop_id,
        results=results,
        status_counts={
            status: counts.get(status, 0)
            for status in ("pass", "fail", "needs_review")
        },
    )

from pathlib import Path

from creative_agent_eval.loops import OneShotLoop
from creative_agent_eval.models import EvalCase
from creative_agent_eval.providers import ScriptedProvider
from creative_agent_eval.runtime import TraceRecorder
from creative_agent_eval.tools import ToolCall, ToolContext, build_default_registry


def make_case() -> EvalCase:
    return EvalCase(
        case_id="B04",
        suite="creative_problem_solving",
        title="fixture smoke",
        status="pilot",
        prompt_finalized=True,
        language="zh-CN",
        source_basis=["self-authored"],
        construct_targets=["appropriateness"],
        prompt="这是一个用于验证运行器和Trace结构的固定测试题面，长度足够且不发起真实模型请求。",
        tool_environment={},
        gold={},
        rubric=[
            {
                "criterion_id": f"B04-C{i}",
                "dimension": "x",
                "description": "d",
                "weight": 1,
                "automatic": True,
                "anchors": {"0": "f", "1": "b", "2": "p"},
            }
            for i in range(1, 5)
        ],
        boundary_examples=[
            {"label": "pass", "output": "ok", "rationale": "ok"},
            {"label": "borderline", "output": "maybe", "rationale": "maybe"},
            {"label": "fail", "output": "bad", "rationale": "bad"},
        ],
        automatic_checks=["a", "b", "c"],
        post_training_diagnostic_targets=["x", "y"],
        problem_family="B-X",
        source_policy="self-authored",
    )


def test_tool_registry_enforces_allowlist() -> None:
    registry = build_default_registry()
    context = ToolContext(
        case_id="B04",
        allowed_tools={"inventory_lookup"},
        fixture={"inventory": {"bottle": {"capacity_ml": 500}}},
    )
    allowed = registry.call(
        ToolCall(call_id="1", name="inventory_lookup", arguments={"item": "bottle"}),
        context,
    )
    denied = registry.call(
        ToolCall(call_id="2", name="risk_check", arguments={"plan": "x"}),
        context,
    )
    assert allowed.ok is True
    assert allowed.output["properties"]["capacity_ml"] == 500
    assert denied.ok is False
    assert denied.error_type == "tool_not_allowed"


def test_one_shot_scripted_provider_records_trace() -> None:
    case = make_case()
    provider = ScriptedProvider({"B04": {"final": "fixed output"}})
    trace = OneShotLoop().run(case, provider, seed=7)
    assert trace.terminal_state == "completed"
    assert trace.final_output == "fixed output"
    assert [event.event_type for event in trace.events] == [
        "run_started",
        "model_requested",
        "model_responded",
        "run_completed",
    ]


def test_trace_jsonl_round_trip(tmp_path: Path) -> None:
    recorder = TraceRecorder("A01", "L0", "scripted", 1)
    recorder.emit("run_started")
    recorder.complete("done")
    path = tmp_path / "trace.jsonl"
    recorder.append_jsonl(path)
    assert '"case_id":"A01"' in path.read_text(encoding="utf-8")

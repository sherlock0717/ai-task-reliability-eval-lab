from creative_agent_eval.evaluation import evaluate_trace_checks, score_output
from creative_agent_eval.loops import ToolGroundedLoop
from creative_agent_eval.providers import ScriptedProvider
from creative_agent_eval.registry import load_cases
from creative_agent_eval.tools import (
    FaultInjectingRegistry,
    ToolFaultPlan,
    build_default_registry,
)
from creative_agent_eval.tools.materialize import materialize_fixture


def _case(case_id: str):
    return next(case for case in load_cases() if case.case_id == case_id)


def test_l3_records_recoverable_tool_failure_and_retry():
    case = _case("B04")
    fixture = materialize_fixture(case)
    call = {
        "id": "lookup-1",
        "function": {
            "name": "inventory_lookup",
            "arguments": {"item": "塑料瓶"},
        },
    }
    provider = ScriptedProvider(
        {
            case.case_id: {
                "tool_plan": {"content": "先核对可用物品。", "tool_calls": [call]},
                "final": case.boundary_examples[0].output,
            }
        }
    )
    registry = FaultInjectingRegistry(
        build_default_registry(),
        ToolFaultPlan(
            mode="timeout_first_call",
            target_tool="inventory_lookup",
            recoverable=True,
        ),
    )
    trace = ToolGroundedLoop(max_retries_per_call=1).run(
        case,
        provider,
        registry,  # type: ignore[arg-type]
        fixture.data,
        seed=7,
    )
    assert trace.terminal_state == "completed"
    assert trace.has_event("tool_failed")
    assert trace.has_event("tool_retry")
    assert trace.has_event("tool_returned")
    assert trace.has_event("revalidation_completed")
    assert trace.has_event("stop_decision")
    assert registry.call_count("inventory_lookup") == 2

    trace_evaluation = evaluate_trace_checks(case, trace)
    assumption = next(item for item in trace_evaluation.results if item.check_id == "critical_assumption_coverage")
    assert assumption.status == "pass"

    score = score_output(case, trace.final_output, trace=trace)
    assert any(item.source == "trace_oracle" for item in score.criterion_scores)


def test_api_independent_empty_fault_is_recorded_as_tool_result():
    case = _case("B04")
    fixture = materialize_fixture(case)
    call = {
        "id": "lookup-empty",
        "function": {
            "name": "inventory_lookup",
            "arguments": {"item": "塑料瓶"},
        },
    }
    provider = ScriptedProvider(
        {
            case.case_id: {
                "tool_plan": {"content": "检查资源。", "tool_calls": [call]},
                "final": case.boundary_examples[1].output,
            }
        }
    )
    registry = FaultInjectingRegistry(
        build_default_registry(),
        ToolFaultPlan(mode="empty_first_call", target_tool="inventory_lookup"),
    )
    trace = ToolGroundedLoop().run(case, provider, registry, fixture.data, seed=8)  # type: ignore[arg-type]
    assert trace.terminal_state == "completed"
    returned = trace.events_of("tool_returned")
    assert len(returned) == 1
    assert returned[0].payload["output"]["status"] == "empty_injected_result"
    assert not trace.has_event("tool_retry")

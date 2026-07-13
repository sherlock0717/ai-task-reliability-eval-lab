from creative_agent_eval.loops import CritiqueReviseLoop, DivergentConvergentLoop, ToolGroundedLoop
from creative_agent_eval.models import EvalCase
from creative_agent_eval.providers import ScriptedProvider
from creative_agent_eval.tools import build_default_registry


def make_case() -> EvalCase:
    return EvalCase(
        case_id="B04",
        suite="creative_problem_solving",
        title="loop smoke",
        status="pilot",
        prompt_finalized=True,
        language="zh-CN",
        source_basis=["self-authored"],
        construct_targets=["appropriateness"],
        prompt="这是一个用于验证多种Loop阶段、工具调用和Trace事件的固定测试题面，长度足够。",
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


def test_critique_revise_loop() -> None:
    case = make_case()
    provider = ScriptedProvider(
        {"B04": {"draft": "draft", "critique": "fix", "revision": "final"}}
    )
    trace = CritiqueReviseLoop().run(case, provider)
    assert trace.final_output == "final"
    assert any(event.event_type == "critique_created" for event in trace.events)


def test_divergent_convergent_loop() -> None:
    case = make_case()
    provider = ScriptedProvider(
        {
            "B04": {
                "candidate_1": "a",
                "candidate_2": "b",
                "candidate_3": "c",
                "synthesis": "best",
            }
        }
    )
    trace = DivergentConvergentLoop(candidate_count=3).run(case, provider)
    assert trace.final_output == "best"
    assert sum(event.event_type == "candidate_created" for event in trace.events) == 3


def test_tool_grounded_loop_calls_registry() -> None:
    case = make_case().model_copy(
        update={
            "tool_environment": {
                "tools": [
                    {
                        "name": "inventory_lookup",
                        "description": "lookup",
                        "inputs": {"item": "item name"},
                    }
                ],
                "max_tool_calls": 2,
            }
        }
    )
    provider = ScriptedProvider(
        {
            "B04": {
                "tool_plan": {
                    "content": "check bottle",
                    "tool_calls": [
                        {
                            "id": "t1",
                            "function": {
                                "name": "inventory_lookup",
                                "arguments": {"item": "bottle"},
                            },
                        }
                    ],
                },
                "final": "verified",
            }
        }
    )
    trace = ToolGroundedLoop().run(
        case,
        provider,
        build_default_registry(),
        {"inventory": {"bottle": {"capacity_ml": 500}}},
    )
    assert trace.final_output == "verified"
    assert any(event.event_type == "tool_returned" for event in trace.events)

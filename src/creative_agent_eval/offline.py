from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .evaluation.scoring import score_boundary_example
from .experiments import ExperimentPlan, ExperimentRunSpec
from .loops import CritiqueReviseLoop, DivergentConvergentLoop, OneShotLoop, ToolGroundedLoop
from .models import EvalCase
from .providers import ScriptedProvider
from .tools import build_default_registry
from .tools.materialize import materialize_fixture


def run_scripted_case(case: EvalCase, run: ExperimentRunSpec):
    example = next(item for item in case.boundary_examples if item.label == run.boundary_label)
    output = example.output
    if run.loop_id == "L0":
        provider = ScriptedProvider({case.case_id: {"final": output}})
        return OneShotLoop().run(case, provider, seed=run.seed)
    if run.loop_id == "L1":
        provider = ScriptedProvider(
            {case.case_id: {"draft": output, "critique": "检查硬约束、适用性与证据。", "revision": output}}
        )
        return CritiqueReviseLoop().run(case, provider, seed=run.seed)
    if run.loop_id == "L2":
        provider = ScriptedProvider(
            {
                case.case_id: {
                    "candidate_1": output,
                    "candidate_2": output,
                    "candidate_3": output,
                    "synthesis": output,
                }
            }
        )
        return DivergentConvergentLoop(candidate_count=3).run(case, provider, seed=run.seed)

    fixture = materialize_fixture(case)
    provider = ScriptedProvider(
        {case.case_id: {"tool_plan": {"content": output, "tool_calls": []}, "final": output}}
    )
    return ToolGroundedLoop().run(
        case,
        provider,
        build_default_registry(),
        fixture.data,
        seed=run.seed,
    )


def run_offline_plan(
    plan: ExperimentPlan,
    cases: list[EvalCase],
    out_dir: Path,
    max_runs: int | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    case_map = {case.case_id: case for case in cases}
    selected_runs = plan.runs[:max_runs] if max_runs is not None else plan.runs
    trace_path = out_dir / "traces.jsonl"
    regression_path = out_dir / "boundary_regressions.jsonl"
    terminal = Counter()
    loop_counts = Counter()
    label_counts = Counter()
    regression_counts = Counter()

    with trace_path.open("w", encoding="utf-8") as trace_handle, regression_path.open("w", encoding="utf-8") as regression_handle:
        for run in selected_runs:
            case = case_map[run.case_id]
            trace = run_scripted_case(case, run)
            trace_handle.write(trace.model_dump_json() + "\n")
            terminal[trace.terminal_state] += 1
            loop_counts[run.loop_id] += 1
            label_counts[run.boundary_label] += 1

            example = next(item for item in case.boundary_examples if item.label == run.boundary_label)
            regression = score_boundary_example(case, example)
            payload = {"run_id": run.run_id, **regression.model_dump(mode="json")}
            regression_handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            regression_counts[regression.regression_status] += 1

    summary: dict[str, Any] = {
        "plan_version": plan.plan_version,
        "planned_run_count": plan.run_count,
        "executed_run_count": len(selected_runs),
        "terminal_states": dict(terminal),
        "loop_counts": dict(loop_counts),
        "label_counts": dict(label_counts),
        "boundary_regression": dict(regression_counts),
        "traces": trace_path.name,
        "boundary_regressions": regression_path.name,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .evaluation.scoring import score_boundary_example
from .experiments import ExperimentPlan, ExperimentRunSpec
from .loops import CritiqueReviseLoop, DivergentConvergentLoop, OneShotLoop, ToolGroundedLoop
from .models import EvalCase
from .providers import ScriptedProvider
from .tools import build_default_registry
from .tools.materialize import materialize_fixture


class LedgerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    case_id: str
    loop_id: str
    boundary_label: str
    status: Literal["completed", "failed"]
    attempt_count: int = Field(ge=1)
    error: str | None = None


class RunLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_version: str
    entries: dict[str, LedgerEntry] = Field(default_factory=dict)


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


def _load_ledger(path: Path, plan_version: str, resume: bool) -> RunLedger:
    if resume and path.exists():
        ledger = RunLedger.model_validate_json(path.read_text(encoding="utf-8"))
        if ledger.plan_version != plan_version:
            raise ValueError("existing ledger uses a different experiment plan version")
        return ledger
    return RunLedger(plan_version=plan_version)


def _write_ledger(ledger: RunLedger, path: Path) -> None:
    path.write_text(
        json.dumps(ledger.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_offline_plan(
    plan: ExperimentPlan,
    cases: list[EvalCase],
    out_dir: Path,
    max_runs: int | None = None,
    resume: bool = False,
    max_failures: int | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    case_map = {case.case_id: case for case in cases}
    trace_path = out_dir / "traces.jsonl"
    regression_path = out_dir / "boundary_regressions.jsonl"
    ledger_path = out_dir / "ledger.json"
    ledger = _load_ledger(ledger_path, plan.plan_version, resume)

    completed_ids = {
        run_id
        for run_id, entry in ledger.entries.items()
        if entry.status == "completed"
    }
    pending_runs = [run for run in plan.runs if run.run_id not in completed_ids]
    selected_runs = pending_runs[:max_runs] if max_runs is not None else pending_runs
    mode = "a" if resume and trace_path.exists() else "w"
    new_failures = 0
    stop_reason: str | None = None

    with trace_path.open(mode, encoding="utf-8") as trace_handle, regression_path.open(mode, encoding="utf-8") as regression_handle:
        for run in selected_runs:
            previous = ledger.entries.get(run.run_id)
            attempts = (previous.attempt_count if previous else 0) + 1
            case = case_map[run.case_id]
            try:
                trace = run_scripted_case(case, run)
                trace_handle.write(trace.model_dump_json() + "\n")
                status: Literal["completed", "failed"] = "completed" if trace.terminal_state == "completed" else "failed"
                error = trace.error

                example = next(item for item in case.boundary_examples if item.label == run.boundary_label)
                regression = score_boundary_example(case, example)
                payload = {"run_id": run.run_id, **regression.model_dump(mode="json")}
                regression_handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            except Exception as exc:
                status = "failed"
                error = str(exc)

            ledger.entries[run.run_id] = LedgerEntry(
                run_id=run.run_id,
                case_id=run.case_id,
                loop_id=run.loop_id,
                boundary_label=run.boundary_label,
                status=status,
                attempt_count=attempts,
                error=error,
            )
            _write_ledger(ledger, ledger_path)

            if status == "failed":
                new_failures += 1
                if max_failures is not None and new_failures >= max_failures:
                    stop_reason = "max_failures_reached"
                    break

    terminal = Counter(entry.status for entry in ledger.entries.values())
    loop_counts = Counter(entry.loop_id for entry in ledger.entries.values())
    label_counts = Counter(entry.boundary_label for entry in ledger.entries.values())
    regression_counts = Counter()
    if regression_path.exists():
        for line in regression_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                regression_counts[json.loads(line)["regression_status"]] += 1

    summary: dict[str, Any] = {
        "plan_version": plan.plan_version,
        "planned_run_count": plan.run_count,
        "completed_run_count": terminal.get("completed", 0),
        "failed_run_count": terminal.get("failed", 0),
        "remaining_run_count": plan.run_count - terminal.get("completed", 0),
        "newly_selected_run_count": len(selected_runs),
        "resume": resume,
        "stop_reason": stop_reason,
        "terminal_states": dict(terminal),
        "loop_counts": dict(loop_counts),
        "label_counts": dict(label_counts),
        "boundary_regression_attempts": dict(regression_counts),
        "traces": trace_path.name,
        "boundary_regressions": regression_path.name,
        "ledger": ledger_path.name,
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary

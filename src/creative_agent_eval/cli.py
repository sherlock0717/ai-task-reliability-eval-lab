from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .evaluation import audit_evaluation
from .experiments import build_experiment_plan, write_experiment_plan
from .loops import CritiqueReviseLoop, DivergentConvergentLoop, OneShotLoop, ToolGroundedLoop
from .offline import run_offline_plan
from .providers import DeepSeekConfig, DeepSeekProvider, ScriptedProvider
from .registry import DEFAULT_REGISTRY_DIR, load_cases, validate_registry
from .tools import build_default_registry, load_fixture
from .tools.materialize import write_materialized_fixtures
from .variants import build_variant_plan, write_variant_plan


def _find_case(case_id: str):
    for case in load_cases():
        if case.case_id == case_id:
            return case
    raise SystemExit(f"case not found: {case_id}")


def _write_trace(trace, out: Path | None) -> None:
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(trace.model_dump_json(indent=2), encoding="utf-8")
    print(trace.model_dump_json(indent=2))


def _write_json(payload: Any, out: Path | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)


def _run_scripted(case, label: str, loop_id: str, seed: int, fixture_path: Path | None):
    example = next(item for item in case.boundary_examples if item.label == label)
    output = example.output
    if loop_id == "L0":
        return OneShotLoop().run(case, ScriptedProvider({case.case_id: {"final": output}}), seed=seed)
    if loop_id == "L1":
        provider = ScriptedProvider(
            {case.case_id: {"draft": output, "critique": "检查硬约束、适用性与证据。", "revision": output}}
        )
        return CritiqueReviseLoop().run(case, provider, seed=seed)
    if loop_id == "L2":
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
        return DivergentConvergentLoop(candidate_count=3).run(case, provider, seed=seed)
    fixture = load_fixture(fixture_path).data if fixture_path else {}
    provider = ScriptedProvider(
        {case.case_id: {"tool_plan": {"content": output, "tool_calls": []}, "final": output}}
    )
    return ToolGroundedLoop().run(case, provider, build_default_registry(), fixture, seed=seed)


def main() -> None:
    parser = argparse.ArgumentParser(prog="creative-agent-eval")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate-registry")
    validate.add_argument("--path", type=Path, default=DEFAULT_REGISTRY_DIR)

    materialize = subcommands.add_parser("materialize-fixtures")
    materialize.add_argument("--out-dir", type=Path, required=True)

    audit = subcommands.add_parser("audit-evaluation")
    audit.add_argument("--out", type=Path)
    audit.add_argument("--fail-on-error", action="store_true")

    plan = subcommands.add_parser("plan-experiment")
    plan.add_argument("--out", type=Path, required=True)
    plan.add_argument("--repeats", type=int, default=1)
    plan.add_argument("--seed-base", type=int, default=0)

    variants = subcommands.add_parser("plan-variants")
    variants.add_argument("--out", type=Path, required=True)

    offline = subcommands.add_parser("run-offline-matrix")
    offline.add_argument("--out-dir", type=Path, required=True)
    offline.add_argument("--repeats", type=int, default=1)
    offline.add_argument("--seed-base", type=int, default=0)
    offline.add_argument("--max-runs", type=int)
    offline.add_argument("--max-failures", type=int)
    offline.add_argument("--resume", action="store_true")

    dry_run = subcommands.add_parser("dry-run")
    dry_run.add_argument("--case-id", required=True)
    dry_run.add_argument("--label", choices=["pass", "borderline", "fail"], default="pass")
    dry_run.add_argument("--loop", choices=["L0", "L1", "L2", "L3"], default="L0")
    dry_run.add_argument("--fixture", type=Path)
    dry_run.add_argument("--seed", type=int, default=0)
    dry_run.add_argument("--out", type=Path)

    api_run = subcommands.add_parser("run-api")
    api_run.add_argument("--case-id", required=True)
    api_run.add_argument("--model", choices=["deepseek-v4-flash", "deepseek-v4-pro"], default="deepseek-v4-flash")
    api_run.add_argument("--thinking", choices=["enabled", "disabled"], default="enabled")
    api_run.add_argument("--reasoning-effort", choices=["high", "max"], default="high")
    api_run.add_argument("--seed", type=int, default=0)
    api_run.add_argument("--out", type=Path, required=True)

    args = parser.parse_args()
    cases = load_cases()

    if args.command == "validate-registry":
        print(json.dumps(validate_registry(args.path), ensure_ascii=False, indent=2))
        return

    if args.command == "materialize-fixtures":
        _write_json(write_materialized_fixtures(cases, args.out_dir), None)
        return

    if args.command == "audit-evaluation":
        result = audit_evaluation(cases)
        _write_json(result.model_dump(mode="json"), args.out)
        if args.fail_on_error and result.finding_counts.get("error", 0):
            raise SystemExit(1)
        return

    if args.command == "plan-experiment":
        experiment = build_experiment_plan(cases, repeats=args.repeats, seed_base=args.seed_base)
        write_experiment_plan(experiment, args.out)
        _write_json({"case_count": experiment.case_count, "run_count": experiment.run_count, "out": str(args.out)}, None)
        return

    if args.command == "plan-variants":
        variant_plan = build_variant_plan(cases)
        write_variant_plan(variant_plan, args.out)
        _write_json({"case_count": variant_plan.case_count, "variant_count": variant_plan.variant_count, "out": str(args.out)}, None)
        return

    if args.command == "run-offline-matrix":
        experiment = build_experiment_plan(cases, repeats=args.repeats, seed_base=args.seed_base)
        summary = run_offline_plan(
            experiment,
            cases,
            args.out_dir,
            max_runs=args.max_runs,
            resume=args.resume,
            max_failures=args.max_failures,
        )
        _write_json(summary, None)
        return

    if args.command == "dry-run":
        case = _find_case(args.case_id)
        trace = _run_scripted(case, args.label, args.loop, args.seed, args.fixture)
        _write_trace(trace, args.out)
        return

    if args.command == "run-api":
        case = _find_case(args.case_id)
        provider = DeepSeekProvider(
            DeepSeekConfig(
                model=args.model,
                thinking=args.thinking == "enabled",
                reasoning_effort=args.reasoning_effort,
            )
        )
        try:
            trace = OneShotLoop().run(case, provider, seed=args.seed)
        finally:
            provider.close()
        _write_trace(trace, args.out)
        if trace.terminal_state == "failed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .loops import OneShotLoop
from .providers import DeepSeekConfig, DeepSeekProvider, ScriptedProvider
from .registry import DEFAULT_REGISTRY_DIR, load_cases, validate_registry


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


def main() -> None:
    parser = argparse.ArgumentParser(prog="creative-agent-eval")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate-registry")
    validate.add_argument("--path", type=Path, default=DEFAULT_REGISTRY_DIR)

    dry_run = subcommands.add_parser("dry-run")
    dry_run.add_argument("--case-id", required=True)
    dry_run.add_argument("--label", choices=["pass", "borderline", "fail"], default="pass")
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

    if args.command == "validate-registry":
        print(json.dumps(validate_registry(args.path), ensure_ascii=False, indent=2))
        return

    if args.command == "dry-run":
        case = _find_case(args.case_id)
        example = next(item for item in case.boundary_examples if item.label == args.label)
        provider = ScriptedProvider({case.case_id: {"final": example.output}})
        trace = OneShotLoop().run(case, provider, seed=args.seed)
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

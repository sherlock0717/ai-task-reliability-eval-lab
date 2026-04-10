"""Run one task with the direct adapter, write trace JSONL, print rule scores."""

from __future__ import annotations

import sys
from pathlib import Path

# Direct script execution: ``python src/runners/run_*.py`` leaves ``__package__`` empty,
# so ``from src...`` would fail unless the repo root is on sys.path. ``python -m`` sets
# the package context and does not need this.
if not __package__:
    _repo_root = Path(__file__).resolve().parents[2]
    _root_s = str(_repo_root)
    if _root_s not in sys.path:
        sys.path.insert(0, _root_s)

import argparse
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.adapters.direct_adapter import DirectAdapter
from src.scorers.rule_scorer import score_task
from src.traces.recorder import append_trace
from src.traces.schema import TraceRecord
from src.utils.io import build_input_snapshot
from src.utils.jsonl import read_jsonl

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _find_task(tasks: List[Dict[str, Any]], task_id: str) -> Dict[str, Any]:
    for t in tasks:
        if t.get("task_id") == task_id:
            return t
    raise KeyError(f"task_id not found: {task_id}")


def _maybe_validate(task: Dict[str, Any], schema_path: Path) -> None:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        logger.warning("jsonschema not installed; skip validation")
        return
    from src.utils.io import read_json

    schema = read_json(schema_path)
    jsonschema.validate(instance=task, schema=schema)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a single eval task (direct baseline).")
    parser.add_argument("--task-id", required=True, help="task_id from the tasks JSONL")
    parser.add_argument(
        "--tasks-file",
        type=Path,
        default=None,
        help="Path to tasks JSONL (default: <repo>/data/tasks/v1_tasks.jsonl)",
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root (default: auto)")
    parser.add_argument(
        "--validate-schema",
        action="store_true",
        help="Validate task against data/tasks/task_schema.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override output base (default: <repo>/outputs/runs/single_<run_id>)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    root = Path(args.repo_root).resolve() if args.repo_root else _repo_root()
    tasks_path = (
        Path(args.tasks_file).resolve()
        if args.tasks_file
        else (root / "data" / "tasks" / "v1_tasks.jsonl")
    )

    tasks = read_jsonl(tasks_path)
    task = _find_task(tasks, args.task_id)

    if args.validate_schema:
        schema_path = root / "data" / "tasks" / "task_schema.json"
        _maybe_validate(task, schema_path)

    run_id = str(uuid.uuid4())
    out_dir = Path(args.output_dir) if args.output_dir else (root / "outputs" / "runs" / f"single_{run_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    traces_path = out_dir / "traces.jsonl"
    scored_path = out_dir.parent.parent / "scored_runs" / out_dir.name / "scores.jsonl"
    scored_path.parent.mkdir(parents=True, exist_ok=True)

    adapter = DirectAdapter()
    started_at = _utc_now()
    input_snapshot = build_input_snapshot(task, root)
    result = adapter.run_task(task, repo_root=root)
    finished_at = _utc_now()

    record = TraceRecord(
        run_id=run_id,
        task_id=str(task["task_id"]),
        candidate_id=adapter.candidate_id,
        status=str(result["status"]),
        input_snapshot=input_snapshot,
        raw_output=str(result.get("raw_output", "")),
        normalized_output=result.get("normalized_output"),
        intermediate_steps=list(result.get("intermediate_steps") or []),
        tool_calls=list(result.get("tool_calls") or []),
        human_interventions=list(result.get("human_interventions") or []),
        error_log=[str(x) for x in (result.get("error_log") or [])],
        latency_ms=float(result.get("latency_ms", 0.0)),
        token_usage={k: int(v) for k, v in (result.get("token_usage") or {}).items()},
        estimated_cost=result.get("estimated_cost"),
        started_at=started_at,
        finished_at=finished_at,
    )

    append_trace(traces_path, record)

    scored = score_task(
        task,
        result.get("normalized_output"),
        raw_output=str(result.get("raw_output", "")),
    )
    scored_row = {
        "run_id": run_id,
        "experiment_id": out_dir.name,
        "candidate_id": adapter.candidate_id,
        "trace_status": result.get("status"),
        **scored,
    }
    from src.utils.jsonl import append_jsonl

    append_jsonl(scored_path, scored_row)

    print(json.dumps(scored_row, ensure_ascii=False, indent=2))
    print(f"\nTrace: {traces_path}", file=sys.stderr)
    print(f"Scored: {scored_path}", file=sys.stderr)
    return 0 if scored.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())

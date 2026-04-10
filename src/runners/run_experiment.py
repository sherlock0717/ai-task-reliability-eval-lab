"""Batch-run all tasks in v1_tasks.jsonl with the direct adapter."""

from __future__ import annotations

import sys
from pathlib import Path

# See run_single_task.py — same ``from src...`` bootstrap for ``python path/to/run_*.py``.
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
from src.analysis.summarize import summarize_scored_file, write_summary_json
from src.scorers.rule_scorer import score_task
from src.traces.recorder import append_trace
from src.traces.schema import TraceRecord
from src.utils.io import build_input_snapshot
from src.utils.jsonl import append_jsonl, read_jsonl

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_experiment_id() -> str:
    return datetime.now(timezone.utc).strftime("exp_%Y%m%dT%H%M%SZ")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Batch eval: direct baseline over v1_tasks.jsonl.")
    parser.add_argument(
        "--tasks-file",
        type=Path,
        default=None,
        help="Tasks JSONL (default: <repo>/data/tasks/v1_tasks.jsonl)",
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root")
    parser.add_argument(
        "--experiment-id",
        default=None,
        help="Folder name under outputs/runs (default: UTC timestamp)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    root = Path(args.repo_root).resolve() if args.repo_root else _repo_root()
    tasks_path = (
        Path(args.tasks_file).resolve()
        if args.tasks_file
        else (root / "data" / "tasks" / "v1_tasks.jsonl")
    )
    exp_id = args.experiment_id or _default_experiment_id()

    runs_dir = root / "outputs" / "runs" / exp_id
    scored_dir = root / "outputs" / "scored_runs" / exp_id
    summaries_dir = root / "outputs" / "summaries" / exp_id
    runs_dir.mkdir(parents=True, exist_ok=True)
    scored_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir.mkdir(parents=True, exist_ok=True)

    traces_path = runs_dir / "traces.jsonl"
    scores_path = scored_dir / "scores.jsonl"
    summary_path = summaries_dir / "summary.json"

    tasks: List[Dict[str, Any]] = read_jsonl(tasks_path)
    adapter = DirectAdapter()

    for task in tasks:
        run_id = str(uuid.uuid4())
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
            "experiment_id": exp_id,
            "candidate_id": adapter.candidate_id,
            "trace_status": result.get("status"),
            **scored,
        }
        append_jsonl(scores_path, scored_row)

    summary = summarize_scored_file(scores_path)
    summary["experiment_id"] = exp_id
    summary["tasks_file"] = str(tasks_path)
    summary["traces_path"] = str(traces_path)
    summary["scores_path"] = str(scores_path)
    write_summary_json(summary_path, summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nTraces: {traces_path}", file=sys.stderr)
    print(f"Scores: {scores_path}", file=sys.stderr)
    print(f"Summary: {summary_path}", file=sys.stderr)

    failed = int(summary.get("failed", 0))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

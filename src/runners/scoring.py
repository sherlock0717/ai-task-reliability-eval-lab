"""Compose rule scores, quality proxy, and failure taxonomy for runners."""

from __future__ import annotations

from typing import Any, Dict

from src.analysis.failure_taxonomy import classify_failure
from src.scorers.quality_proxy_scorer import score_quality_proxy
from src.scorers.rule_scorer import score_task


def compose_scored_row(
    task: Dict[str, Any],
    result: Dict[str, Any],
    *,
    input_snapshot: Dict[str, Any],
    run_id: str,
    experiment_id: str,
    candidate_id: str,
) -> Dict[str, Any]:
    raw = str(result.get("raw_output", ""))
    norm = result.get("normalized_output")
    scored = score_task(task, norm, raw_output=raw)
    qp = score_quality_proxy(task, norm, raw_output=raw)
    ft = classify_failure(
        rule_passed=bool(scored.get("passed")),
        rule_checks=scored.get("checks") or {},
        quality_proxy=qp,
        trace_status=str(result.get("status")),
        raw_output=raw,
        input_snapshot=input_snapshot,
    )
    return {
        "run_id": run_id,
        "experiment_id": experiment_id,
        "candidate_id": candidate_id,
        "task_id": task.get("task_id"),
        "task_type": task.get("task_type"),
        "difficulty": task.get("difficulty"),
        "trace_status": result.get("status"),
        **scored,
        "quality_proxy": qp,
        "failure_taxonomy": ft,
    }

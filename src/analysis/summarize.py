"""Aggregate scores (rule + quality proxy + failure taxonomy) from scored JSONL."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from src.scorers.quality_proxy_scorer import average_citation_presence, average_proxy_metrics
from src.scorers.rule_scorer import summarize_run_scores
from src.utils.io import write_json
from src.utils.jsonl import read_jsonl


def load_scored_rows(path: Path) -> List[Dict[str, Any]]:
    """Load scored records (one dict per line)."""
    return read_jsonl(path)


def summarize_scored_file(path: Path) -> Dict[str, Any]:
    """Compute summary statistics for one scores.jsonl (v0.2 enriched)."""
    rows = load_scored_rows(path)
    if not rows:
        return _empty_summary(str(path))

    agg = summarize_run_scores(rows)

    if any("trace_status" in r for r in rows):
        success_tr = sum(1 for r in rows if r.get("trace_status") == "success")
        failed_tr = sum(1 for r in rows if r.get("trace_status") == "failed")
    else:
        success_tr = 0
        failed_tr = 0

    checks_overview: Dict[str, Dict[str, int]] = {}
    for r in rows:
        checks = r.get("checks") or {}
        for name, detail in checks.items():
            if not isinstance(detail, dict):
                continue
            ok = bool(detail.get("ok")) or bool(detail.get("skipped"))
            bucket = checks_overview.setdefault(name, {"pass": 0, "fail": 0})
            if ok:
                bucket["pass"] += 1
            else:
                bucket["fail"] += 1

    by_type: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})
    by_diff: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})

    for r in rows:
        tt = str(r.get("task_type") or "unknown")
        df = str(r.get("difficulty") or "unknown")
        by_type[tt]["total"] += 1
        by_diff[df]["total"] += 1
        if r.get("passed"):
            by_type[tt]["passed"] += 1
            by_diff[df]["passed"] += 1
        else:
            by_type[tt]["failed"] += 1
            by_diff[df]["failed"] += 1

    fail_dist: Counter[str] = Counter()
    for r in rows:
        ft = r.get("failure_taxonomy") or {}
        if isinstance(ft, dict):
            fail_dist[str(ft.get("primary") or "unknown")] += 1

    qp_avg = {
        "required_item_coverage": average_proxy_metrics(rows, "required_item_coverage"),
        "forbidden_violation_count_avg": average_proxy_metrics(rows, "forbidden_violation_count"),
        "constraint_hit_rate": average_proxy_metrics(rows, "constraint_hit_rate"),
        "output_nonempty_rate": average_proxy_metrics(rows, "output_nonempty"),
        "json_valid_rate": average_proxy_metrics(rows, "json_valid"),
    }
    cit = average_citation_presence(rows)
    if cit is not None:
        qp_avg["citation_presence_avg"] = cit

    return {
        "source": str(path),
        "total_tasks": agg["count"],
        "passed": agg["passed"],
        "failed": agg["failed"],
        "avg_rule_score": agg["avg_score"],
        "success_traces": success_tr,
        "failed_traces": failed_tr,
        "checks_overview": checks_overview,
        "by_task_type": dict(by_type),
        "by_difficulty": dict(by_diff),
        "quality_proxy_averages": qp_avg,
        "failure_taxonomy_distribution": dict(fail_dist),
    }


def _empty_summary(source: str) -> Dict[str, Any]:
    return {
        "source": source,
        "total_tasks": 0,
        "passed": 0,
        "failed": 0,
        "avg_rule_score": 0.0,
        "success_traces": 0,
        "failed_traces": 0,
        "checks_overview": {},
        "by_task_type": {},
        "by_difficulty": {},
        "quality_proxy_averages": {},
        "failure_taxonomy_distribution": {},
    }


def write_summary_json(path: Path, payload: Mapping[str, Any]) -> None:
    write_json(path, dict(payload))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize a scored JSONL from a batch run.")
    parser.add_argument("scores_jsonl", type=Path, help="Path to scores.jsonl")
    parser.add_argument("--out", type=Path, default=None, help="Write summary JSON to this path")
    args = parser.parse_args(argv)

    summary = summarize_scored_file(Path(args.scores_jsonl))
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        write_summary_json(Path(args.out), summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

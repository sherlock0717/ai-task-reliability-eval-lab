"""Aggregate rule scores from scored run JSONL files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from src.scorers.rule_scorer import summarize_run_scores
from src.utils.io import write_json
from src.utils.jsonl import read_jsonl


def load_scored_rows(path: Path) -> List[Dict[str, Any]]:
    """Load scored records (one dict per line)."""
    return read_jsonl(path)


def summarize_scored_file(path: Path) -> Dict[str, Any]:
    """Compute summary statistics for one scores.jsonl."""
    rows = load_scored_rows(path)
    if not rows:
        return {
            "source": str(path),
            "count": 0,
            "passed": 0,
            "failed": 0,
            "success_traces": 0,
            "failed_traces": 0,
            "avg_score": 0.0,
            "checks_overview": {},
        }

    # Rule pass/fail
    agg = summarize_run_scores(rows)

    # Trace status breakdown if present
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

    return {
        "source": str(path),
        "count": agg["count"],
        "passed": agg["passed"],
        "failed": agg["failed"],
        "avg_score": agg["avg_score"],
        "success_traces": success_tr,
        "failed_traces": failed_tr,
        "checks_overview": checks_overview,
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

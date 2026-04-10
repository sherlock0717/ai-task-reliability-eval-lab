"""Export simple charts from a scored JSONL (matplotlib, one figure per file)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if not __package__:
    _root = Path(__file__).resolve().parents[2]
    _s = str(_root)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from collections import Counter, defaultdict

import matplotlib.pyplot as plt

from src.utils.jsonl import read_jsonl


def _pass_rates(rows: List[Dict[str, Any]], key: str) -> Tuple[List[str], List[float]]:
    buckets: Dict[str, List[bool]] = defaultdict(list)
    for r in rows:
        k = str(r.get(key) or "unknown")
        buckets[k].append(bool(r.get("passed")))
    labels = sorted(buckets.keys())
    rates = []
    for lab in labels:
        xs = buckets[lab]
        rates.append(sum(xs) / len(xs) if xs else 0.0)
    return labels, rates


def _failure_counts(rows: List[Dict[str, Any]]) -> Tuple[List[str], List[int]]:
    c: Counter[str] = Counter()
    for r in rows:
        ft = r.get("failure_taxonomy") or {}
        if isinstance(ft, dict):
            c[str(ft.get("primary") or "unknown")] += 1
    labels = sorted(c.keys())
    return labels, [c[k] for k in labels]


def _quality_bars(rows: List[Dict[str, Any]]) -> Tuple[List[str], List[float]]:
    keys = [
        "required_item_coverage",
        "constraint_hit_rate",
        "output_nonempty",
        "json_valid",
    ]
    avgs: List[float] = []
    for k in keys:
        vals: List[float] = []
        for r in rows:
            qp = r.get("quality_proxy") or {}
            if not isinstance(qp, dict):
                continue
            v = qp.get(k)
            if v is None:
                continue
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                continue
        avgs.append(sum(vals) / len(vals) if vals else 0.0)
    labels = keys
    return labels, avgs


def plot_all(*, scores_jsonl: Path, out_dir: Path) -> List[Path]:
    rows = read_jsonl(scores_jsonl)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    # 1) Pass rate by task_type
    labels, rates = _pass_rates(rows, "task_type")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, rates)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Pass rate")
    ax.set_xlabel("task_type")
    ax.set_title("Pass rate by task type (rule passed)")
    fig.tight_layout()
    p1 = out_dir / "pass_rate_by_task_type.png"
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    written.append(p1)

    # 2) Pass rate by difficulty
    labels2, rates2 = _pass_rates(rows, "difficulty")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels2, rates2)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Pass rate")
    ax.set_xlabel("difficulty")
    ax.set_title("Pass rate by difficulty (rule passed)")
    fig.tight_layout()
    p2 = out_dir / "pass_rate_by_difficulty.png"
    fig.savefig(p2, dpi=150)
    plt.close(fig)
    written.append(p2)

    # 3) Quality proxy overview
    q_labels, q_vals = _quality_bars(rows)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(q_labels, q_vals)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Average (proxy)")
    ax.set_xlabel("metric")
    ax.set_title("Quality proxy overview (heuristic averages)")
    fig.tight_layout()
    p3 = out_dir / "quality_proxy_overview.png"
    fig.savefig(p3, dpi=150)
    plt.close(fig)
    written.append(p3)

    # 4) Failure taxonomy
    flabels, fcounts = _failure_counts(rows)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(flabels, fcounts)
    ax.set_ylabel("Count")
    ax.set_xlabel("failure primary")
    ax.set_title("Failure type distribution (rule-based mapping)")
    fig.tight_layout()
    p4 = out_dir / "failure_type_distribution.png"
    fig.savefig(p4, dpi=150)
    plt.close(fig)
    written.append(p4)

    return written


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Plot charts from scores.jsonl.")
    parser.add_argument("--scores-jsonl", type=Path, required=True)
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Directory for PNG files (e.g. outputs/charts/<experiment_id>)",
    )
    args = parser.parse_args(argv)
    paths = plot_all(scores_jsonl=Path(args.scores_jsonl), out_dir=Path(args.out_dir))
    for p in paths:
        print(str(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Lightweight quality proxy metrics — not a semantic gold-standard judge."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Mapping, Optional


def score_quality_proxy(
    task: Mapping[str, Any],
    normalized_output: Any,
    *,
    raw_output: str = "",
) -> Dict[str, Any]:
    """Return structured proxy metrics (0–1 scalars where applicable).

    Documented as **proxy only**: useful for dashboards and coarse triage, not final quality.
    """
    must = [x for x in (task.get("must_include") or []) if x]
    must_not = [x for x in (task.get("must_not_do") or []) if x]
    constraints = [x for x in (task.get("constraints") or []) if x]
    haystack = _haystack(normalized_output, raw_output)

    required_item_coverage = _coverage(must, haystack)
    forbidden_violation_count = sum(1 for p in must_not if p in haystack)
    output_nonempty = bool(haystack.strip())

    expected_type = str(task.get("expected_output_type", "text"))
    json_valid = _json_valid(expected_type, normalized_output, raw_output)

    meta = task.get("metadata") if isinstance(task.get("metadata"), dict) else {}
    expect_cit = bool(meta.get("proxy_expect_citation"))
    citation_presence: Optional[float]
    if expect_cit:
        citation_presence = _citation_score(haystack)
    else:
        citation_presence = None

    constraint_hit_rate = _constraint_hit_rate(constraints, haystack)

    return {
        "required_item_coverage": required_item_coverage,
        "forbidden_violation_count": forbidden_violation_count,
        "output_nonempty": output_nonempty,
        "json_valid": json_valid,
        "citation_presence": citation_presence,
        "constraint_hit_rate": constraint_hit_rate,
        "scorer": "quality-proxy-v0.2",
        "note": "Heuristic proxy metrics only; not semantic correctness.",
    }


def _haystack(normalized_output: Any, raw_output: str) -> str:
    parts: List[str] = []
    if isinstance(normalized_output, str):
        parts.append(normalized_output)
    elif normalized_output is not None:
        try:
            parts.append(json.dumps(normalized_output, ensure_ascii=False))
        except (TypeError, ValueError):
            parts.append(str(normalized_output))
    parts.append(raw_output)
    return "\n".join(parts)


def _coverage(phrases: List[str], haystack: str) -> float:
    if not phrases:
        return 1.0
    hit = sum(1 for p in phrases if p in haystack)
    return hit / len(phrases)


def _json_valid(expected_type: str, normalized_output: Any, raw_output: str) -> bool:
    if expected_type != "json":
        return True
    if isinstance(normalized_output, (dict, list)):
        return True
    if isinstance(normalized_output, str):
        try:
            json.loads(normalized_output.strip())
            return True
        except json.JSONDecodeError:
            return False
    try:
        json.loads(raw_output.strip())
        return True
    except json.JSONDecodeError:
        return False


def _citation_score(haystack: str) -> float:
    """Rough presence of citation-like markers (brackets / FAQ ids / clause ids)."""
    signals = 0
    total = 4
    if re.search(r"\[FAQ[-\s]?\d+\]|\[条款|【", haystack):
        signals += 1
    if "[" in haystack and "]" in haystack:
        signals += 1
    if re.search(r"\bR\d+\b|第[一二三四五六七八九十\d]+条", haystack):
        signals += 1
    if "http" in haystack.lower() or "附录" in haystack:
        signals += 1
    return signals / total


def _constraint_hit_rate(constraints: List[str], haystack: str) -> float:
    """Naive: whether each constraint line has a short prefix present in output (very rough)."""
    if not constraints:
        return 1.0
    hits = 0
    for c in constraints:
        c = c.strip()
        if not c:
            continue
        prefix = c[:8] if len(c) >= 8 else c
        if prefix and prefix in haystack:
            hits += 1
    return hits / len(constraints)


def average_proxy_metrics(rows: List[Mapping[str, Any]], key: str) -> float:
    vals: List[float] = []
    for r in rows:
        qp = r.get("quality_proxy") or {}
        if not isinstance(qp, dict):
            continue
        v = qp.get(key)
        if v is None:
            continue
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
    return sum(vals) / len(vals) if vals else 0.0


def average_citation_presence(rows: List[Mapping[str, Any]]) -> Optional[float]:
    vals: List[float] = []
    for r in rows:
        qp = r.get("quality_proxy") or {}
        if not isinstance(qp, dict):
            continue
        v = qp.get("citation_presence")
        if v is None:
            continue
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
    if not vals:
        return None
    return sum(vals) / len(vals)

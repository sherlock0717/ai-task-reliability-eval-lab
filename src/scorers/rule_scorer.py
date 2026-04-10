"""Rule-based checks for v0.1 (type, inclusion, exclusion, JSON syntax)."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping


def score_task(
    task: Mapping[str, Any],
    normalized_output: Any,
    *,
    raw_output: str = "",
) -> Dict[str, Any]:
    """Return structured rule scores; `passed` is True only if all checks pass."""
    checks: Dict[str, Any] = {}
    expected_type = str(task.get("expected_output_type", "text"))

    type_check = _check_expected_output_type(expected_type, normalized_output, raw_output=raw_output)
    checks["expected_output_type"] = type_check

    include_check = _check_must_include(
        list(task.get("must_include") or []),
        normalized_output,
        raw_output=raw_output,
    )
    checks["must_include"] = include_check

    exclude_check = _check_must_not_do(
        list(task.get("must_not_do") or []),
        normalized_output,
        raw_output=raw_output,
    )
    checks["must_not_do"] = exclude_check

    json_check: Dict[str, Any]
    if expected_type == "json":
        json_check = _check_json_parseable(normalized_output, raw_output=raw_output)
    else:
        json_check = {"ok": True, "skipped": True, "detail": "expected_output_type is not json"}
    checks["json_parseable"] = json_check

    json_ok = bool(json_check.get("skipped")) or bool(json_check.get("ok"))
    passed = (
        bool(type_check.get("ok"))
        and bool(include_check.get("ok"))
        and bool(exclude_check.get("ok"))
        and json_ok
    )

    weights = {"expected_output_type": 1.0, "must_include": 1.0, "must_not_do": 1.0, "json_parseable": 1.0}
    if json_check.get("skipped"):
        weights["json_parseable"] = 0.0
    score = _weighted_average(checks, weights)

    return {
        "task_id": task.get("task_id"),
        "passed": passed,
        "score": score,
        "checks": checks,
        "scorer": "rule-v0.1",
    }


def _weighted_average(checks: Mapping[str, Any], weights: Mapping[str, float]) -> float:
    total_w = 0.0
    acc = 0.0
    for name, w in weights.items():
        if w <= 0:
            continue
        c = checks.get(name) or {}
        ok = bool(c.get("ok")) or bool(c.get("skipped"))
        acc += w * (1.0 if ok else 0.0)
        total_w += w
    if total_w <= 0:
        return 1.0 if all(
            (checks.get(n) or {}).get("ok") or (checks.get(n) or {}).get("skipped")
            for n in checks
        ) else 0.0
    return acc / total_w


def _flatten_text(normalized_output: Any, raw_output: str) -> str:
    if isinstance(normalized_output, str):
        return normalized_output + "\n" + raw_output
    try:
        return json.dumps(normalized_output, ensure_ascii=False) + "\n" + raw_output
    except (TypeError, ValueError):
        return str(normalized_output) + "\n" + raw_output


def _check_expected_output_type(
    expected: str,
    normalized_output: Any,
    *,
    raw_output: str,
) -> Dict[str, Any]:
    if expected == "json":
        if isinstance(normalized_output, (dict, list)):
            ok = True
        elif isinstance(normalized_output, str):
            ok = _strict_json_parse(normalized_output.strip()) is not None
        else:
            ok = False
        return {
            "ok": ok,
            "expected": expected,
            "detail": None if ok else "Output is not JSON-compatible for expected_output_type=json",
        }
    if expected in ("text", "markdown"):
        parts: List[str] = []
        if isinstance(normalized_output, str):
            parts.append(normalized_output)
        elif normalized_output is not None:
            parts.append(_as_text(normalized_output))
        parts.append(raw_output)
        combined = "\n".join(p for p in parts if p).strip()
        ok = bool(combined)
        return {
            "ok": ok,
            "expected": expected,
            "detail": None if ok else "Empty text output",
        }
    return {"ok": False, "expected": expected, "detail": f"Unknown expected_output_type: {expected}"}


def _as_text(normalized_output: Any) -> str:
    if isinstance(normalized_output, str):
        return normalized_output
    if normalized_output is None:
        return ""
    try:
        return json.dumps(normalized_output, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(normalized_output)


def _check_must_include(
    phrases: List[str],
    normalized_output: Any,
    *,
    raw_output: str,
) -> Dict[str, Any]:
    haystack = _flatten_text(normalized_output, raw_output)
    missing = [p for p in phrases if p and p not in haystack]
    ok = len(missing) == 0
    return {"ok": ok, "missing": missing}


def _check_must_not_do(
    forbidden: List[str],
    normalized_output: Any,
    *,
    raw_output: str,
) -> Dict[str, Any]:
    haystack = _flatten_text(normalized_output, raw_output)
    violations = [p for p in forbidden if p and p in haystack]
    ok = len(violations) == 0
    return {"ok": ok, "violations": violations}


def _strict_json_parse(s: str) -> Any:
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def _check_json_parseable(normalized_output: Any, *, raw_output: str) -> Dict[str, Any]:
    if isinstance(normalized_output, (dict, list)):
        return {"ok": True, "detail": "parsed object"}
    if isinstance(normalized_output, str):
        parsed = _strict_json_parse(normalized_output.strip())
        if parsed is not None:
            return {"ok": True, "detail": "parsed string"}
        return {"ok": False, "detail": "string is not valid JSON"}
    parsed = _strict_json_parse(raw_output.strip())
    if parsed is not None:
        return {"ok": True, "detail": "parsed raw_output"}
    return {"ok": False, "detail": "could not parse JSON from output"}


def summarize_run_scores(scored_rows: List[Mapping[str, Any]]) -> Dict[str, Any]:
    """Aggregate a list of score dicts (same shape as score_task output)."""
    n = len(scored_rows)
    passed_n = sum(1 for r in scored_rows if r.get("passed"))
    failed_n = n - passed_n
    scores = [float(r.get("score", 0.0)) for r in scored_rows]
    avg = sum(scores) / n if n else 0.0
    return {
        "count": n,
        "passed": passed_n,
        "failed": failed_n,
        "avg_score": avg,
    }

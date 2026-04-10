"""Rule-based failure typing from scores + trace — not learned classification."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional


# Primary labels for v0.2 (extend later)
FORMAT_FAILURE = "format_failure"
MISSING_REQUIRED_INFO = "missing_required_info"
FORBIDDEN_CONTENT = "forbidden_content"
EMPTY_OUTPUT = "empty_output"
LIKELY_GROUNDING_ISSUE = "likely_grounding_issue"
NEEDS_HUMAN_REVIEW = "needs_human_review"
OK = "ok"


def classify_failure(
    *,
    rule_passed: bool,
    rule_checks: Mapping[str, Any],
    quality_proxy: Mapping[str, Any],
    trace_status: str,
    raw_output: str,
    input_snapshot: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Return `{primary, reasons, detail}` using deterministic rules only."""
    reasons: List[str] = []

    if trace_status != "success":
        reasons.append("adapter reported non-success status")
        return {"primary": FORMAT_FAILURE, "reasons": reasons, "detail": "execution_failed"}

    text = raw_output or ""
    if not text.strip():
        reasons.append("empty raw_output")
        return {"primary": EMPTY_OUTPUT, "reasons": reasons, "detail": "empty_output"}

    jp = quality_proxy.get("json_valid") if isinstance(quality_proxy, dict) else True
    if jp is False:
        reasons.append("quality_proxy.json_valid is false")
        return {"primary": FORMAT_FAILURE, "reasons": reasons, "detail": "json_invalid"}

    exp_ok = (rule_checks.get("expected_output_type") or {}).get("ok")
    if exp_ok is False:
        reasons.append("expected_output_type check failed")
        return {"primary": FORMAT_FAILURE, "reasons": reasons, "detail": "output_type"}

    mi = rule_checks.get("must_include") or {}
    if mi.get("ok") is False:
        reasons.append(f"missing: {mi.get('missing')}")
        return {"primary": MISSING_REQUIRED_INFO, "reasons": reasons, "detail": "must_include"}

    mnd = rule_checks.get("must_not_do") or {}
    if mnd.get("ok") is False:
        reasons.append(f"violations: {mnd.get('violations')}")
        return {"primary": FORBIDDEN_CONTENT, "reasons": reasons, "detail": "must_not_do"}

    jc = rule_checks.get("json_parseable") or {}
    if not jc.get("skipped") and jc.get("ok") is False:
        reasons.append("json_parseable rule failed")
        return {"primary": FORMAT_FAILURE, "reasons": reasons, "detail": "json_parseable"}

    # Grounding proxy: fixture load errors in snapshot
    if input_snapshot and _has_fixture_errors(input_snapshot):
        reasons.append("input file load error in snapshot — output may be ungrounded")
        return {"primary": LIKELY_GROUNDING_ISSUE, "reasons": reasons, "detail": "fixture_error"}

    # Citation-sensitive tasks (metadata flag)
    if isinstance(quality_proxy, dict) and quality_proxy.get("citation_presence") is not None:
        cp = float(quality_proxy.get("citation_presence") or 0.0)
        if cp < 0.25:
            reasons.append("low citation_presence for citation-sensitive task")

    if rule_passed and not reasons:
        return {"primary": OK, "reasons": [], "detail": "passed"}

    if rule_passed and reasons:
        return {"primary": NEEDS_HUMAN_REVIEW, "reasons": reasons, "detail": "proxy_flags"}

    if not rule_passed:
        return {"primary": NEEDS_HUMAN_REVIEW, "reasons": ["rule bundle failed"], "detail": "failed"}

    return {"primary": NEEDS_HUMAN_REVIEW, "reasons": reasons or ["unspecified"], "detail": "other"}


def _has_fixture_errors(snapshot: Mapping[str, Any]) -> bool:
    files = snapshot.get("resolved_files") or []
    if not isinstance(files, list):
        return False
    for f in files:
        if isinstance(f, dict) and "error" in f:
            return True
    return False

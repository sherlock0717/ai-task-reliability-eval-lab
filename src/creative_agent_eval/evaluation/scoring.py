from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models import BoundaryExample, EvalCase, RubricCriterion
from ..runtime import RunTrace
from .oracles import OracleResult, evaluate_automatic_checks
from .trace_checks import evaluate_trace_checks


class CriterionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion_id: str
    dimension: str
    score: int | None = Field(default=None, ge=0, le=2)
    verdict: Literal["pass", "borderline", "fail", "needs_review"]
    source: Literal["deterministic_oracle", "trace_oracle", "pending_semantic"]
    evidence: list[str] = Field(default_factory=list)
    reason: str


class CaseScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    oracle_summary: dict[str, int]
    criterion_scores: list[CriterionScore]
    hard_fail: bool
    review_required: bool


class BoundaryRegressionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    expected_label: Literal["pass", "borderline", "fail"]
    regression_status: Literal["supported", "underdetermined", "contradicted"]
    oracle_summary: dict[str, int]
    criterion_scores: list[CriterionScore]
    rationale: str


_DIMENSION_TOKENS: dict[str, tuple[str, ...]] = {
    "constraint": ("forbidden", "prohibited", "ban", "inventory", "whitelist", "material", "required_field", "structure"),
    "appropriateness": ("constraint", "risk", "assumption", "verification", "evidence", "tool", "state", "timeline"),
    "diversity": ("candidate_count", "response_count", "category_count", "cluster_count", "dedup", "duplicate"),
    "fluency": ("candidate_count", "response_count", "use_count", "item_count", "activity_count", "clue_count"),
    "verification": ("assumption", "verification", "evidence", "tool", "revalidation"),
    "recovery": ("event_acknowledged", "tool", "revalidation"),
    "stopping": ("terminal_decision", "stop"),
    "coherence": ("state", "timeline", "order", "sequence", "structure"),
    "state": ("state", "timeline", "order", "sequence"),
    "structure": ("required_field", "required_section", "final_plan_structure", "output_structure", "json_schema", "fact_ledger", "risk_field"),
}


def _summarize_oracles(results: list[OracleResult]) -> dict[str, int]:
    return {
        status: sum(result.status == status for result in results)
        for status in ("pass", "fail", "needs_review")
    }


def _merge_oracles(output_results: list[OracleResult], trace_results: list[OracleResult]) -> list[OracleResult]:
    merged = {result.check_id: result for result in output_results}
    for result in trace_results:
        current = merged.get(result.check_id)
        if current is None or current.status == "needs_review" or result.status == "fail":
            merged[result.check_id] = result
    return list(merged.values())


def _relevant_oracles(criterion: RubricCriterion, results: list[OracleResult]) -> list[OracleResult]:
    dimension = criterion.dimension.casefold()
    tokens: set[str] = set()
    for key, mapped in _DIMENSION_TOKENS.items():
        if key in dimension:
            tokens.update(mapped)
    if not tokens:
        return []
    return [
        result
        for result in results
        if any(token in result.check_id.casefold() for token in tokens)
    ]


def _score_criterion(criterion: RubricCriterion, results: list[OracleResult]) -> CriterionScore:
    relevant = _relevant_oracles(criterion, results)
    if not relevant:
        return CriterionScore(
            criterion_id=criterion.criterion_id,
            dimension=criterion.dimension,
            verdict="needs_review",
            source="pending_semantic",
            evidence=[],
            reason="该维度需要语义判断或Case级规则，通用Oracle暂不直接给分。",
        )

    evidence = [f"{item.check_id}:{item.status}" for item in relevant]
    source = "trace_oracle" if any(item.capability == "trace_required" for item in relevant) else "deterministic_oracle"
    if any(item.status == "fail" for item in relevant):
        return CriterionScore(
            criterion_id=criterion.criterion_id,
            dimension=criterion.dimension,
            score=0,
            verdict="fail",
            source=source,
            evidence=evidence,
            reason="至少一项相关检查失败。",
        )
    if all(item.status == "pass" for item in relevant):
        return CriterionScore(
            criterion_id=criterion.criterion_id,
            dimension=criterion.dimension,
            score=2,
            verdict="pass",
            source=source,
            evidence=evidence,
            reason="相关检查均通过。",
        )
    return CriterionScore(
        criterion_id=criterion.criterion_id,
        dimension=criterion.dimension,
        verdict="needs_review",
        source=source,
        evidence=evidence,
        reason="相关检查包含待复核项，暂不形成确定性分数。",
    )


def score_output(case: EvalCase, output: Any, trace: RunTrace | None = None) -> CaseScore:
    output_results = evaluate_automatic_checks(case, output)
    trace_results = evaluate_trace_checks(case, trace).results if trace is not None else []
    results = _merge_oracles(output_results, trace_results)
    criterion_scores = [_score_criterion(item, results) for item in case.rubric]
    hard_fail = any(item.status == "fail" and item.severity == "critical" for item in results)
    return CaseScore(
        case_id=case.case_id,
        oracle_summary=_summarize_oracles(results),
        criterion_scores=criterion_scores,
        hard_fail=hard_fail,
        review_required=any(item.verdict == "needs_review" for item in criterion_scores),
    )


def score_boundary_example(case: EvalCase, example: BoundaryExample) -> BoundaryRegressionResult:
    """Compare an author-declared boundary label with currently executable checks.

    A global boundary label is not copied to every rubric criterion. Deterministic
    checks score only the dimensions they can support; remaining dimensions stay
    open for later semantic or human review.
    """

    case_score = score_output(case, example.output)
    summary = case_score.oracle_summary
    has_fail = summary.get("fail", 0) > 0
    has_pass = summary.get("pass", 0) > 0

    if example.label == "pass":
        status = "contradicted" if case_score.hard_fail else ("supported" if has_pass else "underdetermined")
    elif example.label == "fail":
        status = "supported" if has_fail else "underdetermined"
    else:
        status = "contradicted" if case_score.hard_fail and not has_pass else "underdetermined"

    return BoundaryRegressionResult(
        case_id=case.case_id,
        expected_label=example.label,
        regression_status=status,
        oracle_summary=summary,
        criterion_scores=case_score.criterion_scores,
        rationale=example.rationale,
    )

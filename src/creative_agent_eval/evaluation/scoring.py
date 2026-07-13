from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models import BoundaryExample, EvalCase, RubricCriterion
from .oracles import OracleResult, evaluate_automatic_checks


class CriterionScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion_id: str
    score: int = Field(ge=0, le=2)
    verdict: Literal["pass", "borderline", "fail", "needs_review"]
    source: Literal["deterministic_oracle", "declared_boundary", "pending_semantic"]
    evidence: list[str] = Field(default_factory=list)
    reason: str


def _score_from_label(label: str) -> tuple[int, str]:
    if label == "pass":
        return 2, "pass"
    if label == "borderline":
        return 1, "borderline"
    return 0, "fail"


def score_boundary_example(case: EvalCase, example: BoundaryExample) -> list[CriterionScore]:
    """Create a regression target for each rubric criterion.

    Boundary labels are author-declared test expectations. They are kept separate
    from future model/Judge scores and used to detect scorer regressions.
    """
    score, verdict = _score_from_label(example.label)
    oracle_results = evaluate_automatic_checks(case, example.output)
    evidence = [
        f"{result.check_id}:{result.status}"
        for result in oracle_results
        if result.status != "needs_review"
    ]
    return [
        CriterionScore(
            criterion_id=criterion.criterion_id,
            score=score,
            verdict=verdict,  # type: ignore[arg-type]
            source="declared_boundary",
            evidence=evidence,
            reason=example.rationale,
        )
        for criterion in case.rubric
    ]


def summarize_oracles(results: list[OracleResult]) -> dict[str, int]:
    return {
        status: sum(result.status == status for result in results)
        for status in ("pass", "fail", "needs_review")
    }

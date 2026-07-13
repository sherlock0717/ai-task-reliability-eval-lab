from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models import EvalCase
from ..tools.materialize import fixture_coverage
from .oracles import oracle_coverage
from .scoring import score_boundary_example


class AuditFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    severity: Literal["error", "risk", "note"]
    code: str
    message: str


class EvaluationAudit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_count: int
    rubric_criterion_count: int
    boundary_example_count: int
    fixture_coverage: dict[str, int]
    oracle_coverage: dict[str, int]
    boundary_regression: dict[str, int]
    finding_counts: dict[str, int]
    findings: list[AuditFinding] = Field(default_factory=list)


def audit_evaluation(cases: list[EvalCase]) -> EvaluationAudit:
    findings: list[AuditFinding] = []
    regression_statuses: list[str] = []

    for case in cases:
        rubric_ids = [item.criterion_id for item in case.rubric]
        if len(rubric_ids) != len(set(rubric_ids)):
            findings.append(AuditFinding(case_id=case.case_id, severity="error", code="duplicate_rubric_id", message="同一Case存在重复Criterion ID。"))

        tool_names = [
            str(item.get("name"))
            for item in case.tool_environment.get("tools", [])
            if isinstance(item, dict) and item.get("name")
        ]
        if len(tool_names) != len(set(tool_names)):
            findings.append(AuditFinding(case_id=case.case_id, severity="error", code="duplicate_tool_name", message="同一Case存在重复工具名。"))

        labels = {item.label for item in case.boundary_examples}
        if labels != {"pass", "borderline", "fail"}:
            findings.append(AuditFinding(case_id=case.case_id, severity="error", code="boundary_labels", message="边界样例标签不完整。"))

        for field_name in ("required_elements", "accepted_strategies", "prohibited_failures"):
            if not case.gold.get(field_name):
                findings.append(AuditFinding(case_id=case.case_id, severity="risk", code=f"empty_{field_name}", message=f"Gold字段 {field_name} 为空。"))

        if len(case.automatic_checks) < 3:
            findings.append(AuditFinding(case_id=case.case_id, severity="risk", code="few_automatic_checks", message="自动检查少于3项。"))

        for example in case.boundary_examples:
            result = score_boundary_example(case, example)
            regression_statuses.append(result.regression_status)
            if result.regression_status == "contradicted":
                findings.append(AuditFinding(case_id=case.case_id, severity="error", code="boundary_contradiction", message=f"{example.label}边界样例与现有确定性检查冲突。"))

    finding_counts = dict(Counter(item.severity for item in findings))
    for key in ("error", "risk", "note"):
        finding_counts.setdefault(key, 0)

    regression_counts = dict(Counter(regression_statuses))
    for key in ("supported", "underdetermined", "contradicted"):
        regression_counts.setdefault(key, 0)

    return EvaluationAudit(
        case_count=len(cases),
        rubric_criterion_count=sum(len(case.rubric) for case in cases),
        boundary_example_count=sum(len(case.boundary_examples) for case in cases),
        fixture_coverage=fixture_coverage(cases),
        oracle_coverage=oracle_coverage(cases),
        boundary_regression=regression_counts,
        finding_counts=finding_counts,
        findings=findings,
    )

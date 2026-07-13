from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Suite = Literal["psychometric_probe", "creative_problem_solving", "creative_artifact", "loop_adaptation_recovery"]
Status = Literal["specification", "pilot", "frozen", "retired"]


class RubricCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion_id: str
    dimension: str
    description: str
    weight: int = Field(ge=1)
    automatic: bool
    anchors: dict[str, str]


class BoundaryExample(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: Literal["pass", "borderline", "fail"]
    output: Any
    rationale: str


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str = Field(pattern=r"^[A-D][0-9]{2}$")
    suite: Suite
    title: str
    status: Status
    prompt_finalized: bool
    language: str
    source_basis: list[str]
    construct_targets: list[str]
    prompt: str = Field(min_length=40)
    tool_environment: dict[str, Any]
    gold: dict[str, Any]
    rubric: list[RubricCriterion] = Field(min_length=4)
    boundary_examples: list[BoundaryExample] = Field(min_length=3)
    automatic_checks: list[str] = Field(min_length=3)
    post_training_diagnostic_targets: list[str] = Field(min_length=2)
    problem_family: str
    source_policy: str
    notes: str = ""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Suite = Literal["psychometric_probe","constrained_problem_solving","creative_artifact","loop_adaptation_recovery"]

class EvalCaseSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str = Field(pattern=r"^[A-D][0-9]{2}$")
    suite: Suite
    title: str
    status: Literal["specification","pilot","frozen","retired"]
    prompt_finalized: bool
    source_basis: list[str]
    construct_targets: list[str]
    task_spec: dict
    loop_pressure: str
    tool_profile: list[str]
    automatic_checks: list[str]
    human_rubric: list[str]
    post_training_diagnostic_targets: list[str]
    problem_family: str
    risk_notes: list[str] = []
    source_policy: str

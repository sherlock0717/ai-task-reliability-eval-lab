from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .models import EvalCase

LoopId = Literal["L0", "L1", "L2", "L3"]
BoundaryLabel = Literal["pass", "borderline", "fail"]


class ExperimentRunSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    case_id: str
    suite: str
    loop_id: LoopId
    boundary_label: BoundaryLabel
    repeat_index: int = Field(ge=0)
    seed: int
    provider_id: str = "scripted"
    fixture_mode: Literal["generated", "case_specific"] = "generated"


class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_version: str = "v0.1-offline"
    case_count: int
    run_count: int
    loops: list[LoopId]
    labels: list[BoundaryLabel]
    repeats: int
    runs: list[ExperimentRunSpec]


def build_experiment_plan(
    cases: list[EvalCase],
    loops: tuple[LoopId, ...] = ("L0", "L1", "L2", "L3"),
    labels: tuple[BoundaryLabel, ...] = ("pass", "borderline", "fail"),
    repeats: int = 1,
    seed_base: int = 0,
) -> ExperimentPlan:
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    runs: list[ExperimentRunSpec] = []
    for case_index, case in enumerate(sorted(cases, key=lambda item: item.case_id)):
        for loop_index, loop_id in enumerate(loops):
            for label_index, label in enumerate(labels):
                for repeat_index in range(repeats):
                    seed = seed_base + case_index * 1000 + loop_index * 100 + label_index * 10 + repeat_index
                    runs.append(
                        ExperimentRunSpec(
                            run_id=f"{case.case_id}-{loop_id}-{label}-r{repeat_index}",
                            case_id=case.case_id,
                            suite=case.suite,
                            loop_id=loop_id,
                            boundary_label=label,
                            repeat_index=repeat_index,
                            seed=seed,
                        )
                    )
    return ExperimentPlan(
        case_count=len(cases),
        run_count=len(runs),
        loops=list(loops),
        labels=list(labels),
        repeats=repeats,
        runs=runs,
    )


def write_experiment_plan(plan: ExperimentPlan, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(plan.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

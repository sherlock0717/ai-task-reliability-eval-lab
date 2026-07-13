from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .models import EvalCase

VariantKind = Literal[
    "equivalent_wording",
    "constraint_order",
    "irrelevant_context",
    "output_surface",
    "tool_order",
    "tool_fault",
]
VariantStatus = Literal["planned", "materialized"]


class VariantSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    variant_id: str
    case_id: str
    problem_family: str
    kind: VariantKind
    status: VariantStatus
    source_prompt_hash: str
    prompt: str | None = None
    tool_order: list[str] = Field(default_factory=list)
    fault_profile: dict[str, Any] = Field(default_factory=dict)
    validation_requirements: list[str] = Field(default_factory=list)


class VariantPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_version: str = "v0.1-variants"
    case_count: int
    variant_count: int
    kinds: list[VariantKind]
    variants: list[VariantSpec]


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _reorder_constraint_lines(prompt: str) -> str:
    lines = [line for line in prompt.splitlines() if line.strip()]
    if len(lines) < 3:
        return prompt
    return "\n".join([lines[0], *reversed(lines[1:])])


def _tool_names(case: EvalCase) -> list[str]:
    return [
        str(tool["name"])
        for tool in case.tool_environment.get("tools", [])
        if isinstance(tool, dict) and tool.get("name")
    ]


def build_variant_plan(cases: list[EvalCase]) -> VariantPlan:
    variants: list[VariantSpec] = []
    kinds: tuple[VariantKind, ...] = (
        "equivalent_wording",
        "constraint_order",
        "irrelevant_context",
        "output_surface",
        "tool_order",
        "tool_fault",
    )
    for case in sorted(cases, key=lambda item: item.case_id):
        source_hash = _prompt_hash(case.prompt)
        tools = _tool_names(case)
        shared = {
            "case_id": case.case_id,
            "problem_family": case.problem_family,
            "source_prompt_hash": source_hash,
        }
        variants.extend(
            [
                VariantSpec(
                    variant_id=f"{case.case_id}-V01",
                    kind="equivalent_wording",
                    status="planned",
                    validation_requirements=[
                        "保持全部硬约束与交付单元",
                        "不新增事实或资源",
                        "与原题按问题族共同划分数据集",
                    ],
                    **shared,
                ),
                VariantSpec(
                    variant_id=f"{case.case_id}-V02",
                    kind="constraint_order",
                    status="materialized",
                    prompt=_reorder_constraint_lines(case.prompt),
                    validation_requirements=[
                        "原始约束文本逐项保留",
                        "只改变非空行顺序",
                    ],
                    **shared,
                ),
                VariantSpec(
                    variant_id=f"{case.case_id}-V03",
                    kind="irrelevant_context",
                    status="materialized",
                    prompt=f"{case.prompt}\n\n补充记录：本题记录编号为R-17，该编号不改变任务条件与交付要求。",
                    validation_requirements=[
                        "附加信息与解题无关",
                        "Gold与Rubric保持不变",
                    ],
                    **shared,
                ),
                VariantSpec(
                    variant_id=f"{case.case_id}-V04",
                    kind="output_surface",
                    status="planned",
                    validation_requirements=[
                        "只改变输出容器或字段名",
                        "不改变需要完成的内容",
                        "确定性Oracle同步适配",
                    ],
                    **shared,
                ),
                VariantSpec(
                    variant_id=f"{case.case_id}-V05",
                    kind="tool_order",
                    status="materialized",
                    prompt=case.prompt,
                    tool_order=list(reversed(tools)),
                    validation_requirements=[
                        "工具集合保持一致",
                        "只改变工具声明顺序",
                    ],
                    **shared,
                ),
                VariantSpec(
                    variant_id=f"{case.case_id}-V06",
                    kind="tool_fault",
                    status="materialized",
                    prompt=case.prompt,
                    tool_order=tools,
                    fault_profile={
                        "mode": "timeout_first_call",
                        "target_tool": tools[0] if tools else None,
                        "recoverable": True,
                    },
                    validation_requirements=[
                        "只注入一次可恢复故障",
                        "后续调用返回原确定性fixture",
                        "记录重试与恢复事件",
                    ],
                    **shared,
                ),
            ]
        )
    return VariantPlan(
        case_count=len(cases),
        variant_count=len(variants),
        kinds=list(kinds),
        variants=variants,
    )


def write_variant_plan(plan: VariantPlan, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(plan.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

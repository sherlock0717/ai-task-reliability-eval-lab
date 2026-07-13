from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models import EvalCase


OracleStatus = Literal["pass", "fail", "needs_review"]


class OracleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    check_id: str
    status: OracleStatus
    evidence: list[str] = Field(default_factory=list)
    message: str
    severity: Literal["critical", "major", "minor"] = "major"


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _candidate_count(output: Any) -> int:
    if isinstance(output, list):
        return len(output)
    if isinstance(output, dict):
        for key in ("candidates", "ideas", "plans", "options", "responses"):
            value = output.get(key)
            if isinstance(value, list):
                return len(value)
    text = _text(output)
    numbered = re.findall(r"(?:^|\n)\s*(?:\d+[.、)]|[-*])\s+", text)
    return len(numbered)


def _parse_minimum(check_id: str) -> int | None:
    match = re.search(r">=\s*(\d+)", check_id)
    return int(match.group(1)) if match else None


def evaluate_check(case: EvalCase, check_id: str, output: Any) -> OracleResult:
    normalized = check_id.casefold()
    text = _text(output).casefold()

    if "candidate_count" in normalized or "response_count" in normalized:
        minimum = _parse_minimum(check_id) or 1
        count = _candidate_count(output)
        return OracleResult(
            check_id=check_id,
            status="pass" if count >= minimum else "fail",
            evidence=[f"count={count}", f"minimum={minimum}"],
            message="候选数量达到要求" if count >= minimum else "候选数量不足",
            severity="major",
        )

    if any(token in normalized for token in ("forbidden", "prohibited", "ban")):
        failures = [str(item) for item in case.gold.get("prohibited_failures", [])]
        hits = [item for item in failures if item.casefold() in text]
        return OracleResult(
            check_id=check_id,
            status="fail" if hits else "pass",
            evidence=hits,
            message="命中明确禁止项" if hits else "未命中明确禁止项",
            severity="critical",
        )

    if any(token in normalized for token in ("required_field", "final_plan_structure", "output_structure", "json_schema")):
        if isinstance(output, (dict, list)):
            return OracleResult(
                check_id=check_id,
                status="pass",
                evidence=[type(output).__name__],
                message="输出具备可解析结构",
                severity="major",
            )
        return OracleResult(
            check_id=check_id,
            status="needs_review",
            evidence=["plain_text"],
            message="当前输出为纯文本，需要Case级解析器确认结构",
            severity="major",
        )

    if any(token in normalized for token in ("state", "timeline", "order", "sequence")):
        return OracleResult(
            check_id=check_id,
            status="needs_review",
            evidence=[],
            message="需要状态或时间线fixture执行核验",
            severity="major",
        )

    if any(token in normalized for token in ("inventory", "whitelist", "material")):
        return OracleResult(
            check_id=check_id,
            status="needs_review",
            evidence=[],
            message="需要物品实体抽取后与fixture白名单比对",
            severity="critical",
        )

    if any(token in normalized for token in ("assumption", "verification", "evidence", "tool")):
        return OracleResult(
            check_id=check_id,
            status="needs_review",
            evidence=[],
            message="需要结合Trace中的工具调用与证据引用核验",
            severity="major",
        )

    return OracleResult(
        check_id=check_id,
        status="needs_review",
        evidence=[],
        message="当前检查项尚无通用确定性实现，保留到Case级Oracle",
        severity="minor",
    )


def evaluate_automatic_checks(case: EvalCase, output: Any) -> list[OracleResult]:
    return [evaluate_check(case, check_id, output) for check_id in case.automatic_checks]


def oracle_coverage(cases: list[EvalCase]) -> dict[str, int]:
    total = 0
    directly_supported = 0
    for case in cases:
        for check_id in case.automatic_checks:
            total += 1
            probe = evaluate_check(case, check_id, {})
            if "尚无通用确定性实现" not in probe.message:
                directly_supported += 1
    return {
        "automatic_check_count": total,
        "generic_oracle_supported": directly_supported,
        "case_specific_required": total - directly_supported,
    }

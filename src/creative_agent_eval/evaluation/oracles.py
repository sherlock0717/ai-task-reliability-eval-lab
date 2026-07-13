from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models import EvalCase

OracleStatus = Literal["pass", "fail", "needs_review"]
OracleCapability = Literal[
    "deterministic",
    "structured_output",
    "trace_required",
    "case_fixture_required",
    "semantic_required",
]


class OracleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    check_id: str
    status: OracleStatus
    evidence: list[str] = Field(default_factory=list)
    message: str
    severity: Literal["critical", "major", "minor"] = "major"
    capability: OracleCapability


_COUNT_ALIASES: dict[str, tuple[str, ...]] = {
    "candidate": ("candidates", "ideas", "plans", "options", "responses"),
    "response": ("responses", "answers", "ideas"),
    "use": ("uses", "ideas", "responses", "candidates"),
    "item": ("items", "objects", "candidates"),
    "activity": ("activities", "ideas", "candidates"),
    "clue": ("clues", "hints", "candidates"),
    "sense": ("senses", "meanings", "relations", "candidates"),
    "category": ("categories", "clusters", "groups"),
    "semantic_cluster": ("semantic_clusters", "clusters", "categories"),
    "mechanism_cluster": ("mechanism_clusters", "mechanisms", "clusters"),
    "accessory": ("accessories", "attachments", "items"),
}


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _normalise_item(value: Any) -> str:
    return re.sub(r"\s+", " ", _text(value).strip().casefold())


def _list_from_output(output: Any, aliases: tuple[str, ...] = ()) -> list[Any]:
    if isinstance(output, list):
        return output
    if isinstance(output, dict):
        for key in aliases:
            value = output.get(key)
            if isinstance(value, list):
                return value
        for value in output.values():
            if isinstance(value, list):
                return value
    text = _text(output)
    lines = re.findall(r"(?:^|\n)\s*(?:\d+[.、)]|[-*])\s+(.+)", text)
    return [line.strip() for line in lines]


def _parse_count_constraint(check_id: str) -> tuple[str | None, int | None]:
    match = re.search(r"(>=|<=|=)\s*(\d+)", check_id)
    if not match:
        return None, None
    return match.group(1), int(match.group(2))


def _count_family(check_id: str) -> str | None:
    normalized = check_id.casefold()
    for family in _COUNT_ALIASES:
        if family in normalized and ("count" in normalized or "coverage" in normalized):
            return family
    return None


def _evaluate_count(check_id: str, output: Any) -> OracleResult | None:
    family = _count_family(check_id)
    if family is None:
        return None
    values = _list_from_output(output, _COUNT_ALIASES[family])
    count = len(values)
    operator, target = _parse_count_constraint(check_id)
    if operator is None or target is None:
        return OracleResult(
            check_id=check_id,
            status="needs_review",
            evidence=[f"count={count}"],
            message="已提取数量，但检查项未声明可执行阈值。",
            severity="major",
            capability="structured_output",
        )
    passed = {
        ">=": count >= target,
        "<=": count <= target,
        "=": count == target,
    }[operator]
    return OracleResult(
        check_id=check_id,
        status="pass" if passed else "fail",
        evidence=[f"count={count}", f"constraint={operator}{target}"],
        message="数量条件满足" if passed else "数量条件未满足",
        severity="major",
        capability="deterministic",
    )


def _evaluate_duplicates(check_id: str, output: Any) -> OracleResult:
    values = _list_from_output(output)
    if len(values) < 2:
        return OracleResult(
            check_id=check_id,
            status="needs_review",
            evidence=[f"item_count={len(values)}"],
            message="未提取到足够条目执行去重检查。",
            severity="minor",
            capability="structured_output",
        )
    normalized = [_normalise_item(item) for item in values]
    duplicates = sorted({item for item in normalized if normalized.count(item) > 1})
    return OracleResult(
        check_id=check_id,
        status="fail" if duplicates else "pass",
        evidence=duplicates,
        message="存在完全重复条目" if duplicates else "未发现完全重复条目",
        severity="major",
        capability="deterministic",
    )


def _dict_has_key(output: Any, tokens: tuple[str, ...]) -> list[str]:
    if not isinstance(output, dict):
        return []
    return [str(key) for key in output if any(token in str(key).casefold() for token in tokens)]


def _structured_presence(
    check_id: str,
    output: Any,
    tokens: tuple[str, ...],
    message: str,
    severity: Literal["critical", "major", "minor"] = "major",
) -> OracleResult:
    keys = _dict_has_key(output, tokens)
    if keys:
        return OracleResult(
            check_id=check_id,
            status="pass",
            evidence=keys,
            message=message,
            severity=severity,
            capability="structured_output",
        )
    return OracleResult(
        check_id=check_id,
        status="needs_review",
        evidence=["plain_text" if isinstance(output, str) else "field_not_found"],
        message="需要Case级解析确认该结构是否存在。",
        severity=severity,
        capability="structured_output",
    )


def _evaluate_forbidden(case: EvalCase, check_id: str, output: Any) -> OracleResult:
    normalized = check_id.casefold()
    text = _text(output).casefold()
    failures = [str(item) for item in case.gold.get("prohibited_failures", [])]
    hits = [item for item in failures if item.casefold() in text]
    if "electronics" in normalized:
        electronics = ["电子", "电器", "手机", "电脑", "充电", "电池", "屏幕"]
        hits.extend(term for term in electronics if term in text)
    hits = sorted(set(hits))
    return OracleResult(
        check_id=check_id,
        status="fail" if hits else "pass",
        evidence=hits,
        message="命中明确禁止项" if hits else "未命中明确禁止项",
        severity="critical",
        capability="deterministic",
    )


def classify_check(check_id: str) -> OracleCapability:
    normalized = check_id.casefold()
    if _count_family(check_id) is not None or any(token in normalized for token in ("forbidden", "prohibited", "ban", "duplicate", "dedup", "electronics")):
        return "deterministic"
    if any(token in normalized for token in ("required_section", "required_field", "final_plan_structure", "output_structure", "json_schema", "fact_ledger", "risk_field", "terminal_decision", "affected_step", "revalidation")):
        return "structured_output"
    if any(token in normalized for token in ("assumption", "verification", "evidence", "tool", "event_acknowledged")):
        return "trace_required"
    if any(token in normalized for token in ("state", "timeline", "order", "sequence", "inventory", "whitelist", "material", "relation_table", "base_constraints")):
        return "case_fixture_required"
    return "semantic_required"


def evaluate_check(case: EvalCase, check_id: str, output: Any) -> OracleResult:
    normalized = check_id.casefold()

    count_result = _evaluate_count(check_id, output)
    if count_result is not None:
        return count_result

    if any(token in normalized for token in ("duplicate", "dedup")):
        return _evaluate_duplicates(check_id, output)

    if any(token in normalized for token in ("forbidden", "prohibited", "ban", "electronics", "target_leak", "risk_keyword")):
        return _evaluate_forbidden(case, check_id, output)

    if any(token in normalized for token in ("required_field", "final_plan_structure", "output_structure", "json_schema")):
        if isinstance(output, (dict, list)):
            return OracleResult(
                check_id=check_id,
                status="pass",
                evidence=[type(output).__name__],
                message="输出具备可解析结构",
                severity="major",
                capability="structured_output",
            )
        return OracleResult(
            check_id=check_id,
            status="needs_review",
            evidence=["plain_text"],
            message="当前输出为纯文本，需要Case级解析器确认结构。",
            severity="major",
            capability="structured_output",
        )

    if "required_section" in normalized:
        return _structured_presence(check_id, output, ("section", "summary", "plan", "result", "reason", "risk"), "发现结构化交付区块。")
    if "fact_ledger" in normalized:
        return _structured_presence(check_id, output, ("fact", "evidence", "ledger", "source"), "发现事实或证据台账字段。")
    if "risk_field" in normalized:
        return _structured_presence(check_id, output, ("risk", "safety", "风险", "安全"), "发现风险字段。")
    if "terminal_decision" in normalized:
        return _structured_presence(check_id, output, ("terminal", "decision", "stop", "continue", "终止", "停止"), "发现终止决策字段。")
    if "affected_step" in normalized:
        return _structured_presence(check_id, output, ("affected", "impact", "step", "影响", "步骤"), "发现受影响步骤字段。")
    if "revalidation" in normalized:
        keys = _dict_has_key(output, ("revalidation", "validation", "verify", "复核", "验证"))
        text = _text(output)
        if keys or re.search(r"重新验证|再次验证|复核|再检查", text):
            return OracleResult(check_id=check_id, status="pass", evidence=keys or ["text_marker"], message="发现重新验证步骤。", severity="major", capability="structured_output")
        return OracleResult(check_id=check_id, status="needs_review", evidence=[], message="需要确认是否进行了重新验证。", severity="major", capability="structured_output")

    if any(token in normalized for token in ("state", "timeline", "order", "sequence")):
        return OracleResult(check_id=check_id, status="needs_review", evidence=[], message="需要状态或时间线fixture执行核验。", severity="major", capability="case_fixture_required")

    if any(token in normalized for token in ("inventory", "whitelist", "material")):
        return OracleResult(check_id=check_id, status="needs_review", evidence=[], message="需要实体抽取并与Case级资源白名单比对。", severity="critical", capability="case_fixture_required")

    if "relation_table" in normalized:
        return OracleResult(check_id=check_id, status="needs_review", evidence=[], message="需要目标关系表fixture执行核验。", severity="major", capability="case_fixture_required")

    if "base_constraints" in normalized:
        return OracleResult(check_id=check_id, status="needs_review", evidence=[], message="需要比较变更前后的约束集合。", severity="critical", capability="case_fixture_required")

    if any(token in normalized for token in ("assumption", "verification", "evidence", "tool", "event_acknowledged")):
        return OracleResult(check_id=check_id, status="needs_review", evidence=[], message="需要结合Trace中的事件、工具调用与证据引用核验。", severity="major", capability="trace_required")

    return OracleResult(check_id=check_id, status="needs_review", evidence=[], message="该检查依赖语义判断或Case级规则。", severity="minor", capability="semantic_required")


def evaluate_automatic_checks(case: EvalCase, output: Any) -> list[OracleResult]:
    return [evaluate_check(case, check_id, output) for check_id in case.automatic_checks]


def oracle_coverage(cases: list[EvalCase]) -> dict[str, int]:
    capabilities = {
        "deterministic": 0,
        "structured_output": 0,
        "trace_required": 0,
        "case_fixture_required": 0,
        "semantic_required": 0,
    }
    total = 0
    for case in cases:
        for check_id in case.automatic_checks:
            total += 1
            capabilities[classify_check(check_id)] += 1
    generic = capabilities["deterministic"] + capabilities["structured_output"]
    return {
        "automatic_check_count": total,
        "generic_oracle_supported": generic,
        "case_specific_required": total - generic,
        **{f"capability_{key}": value for key, value in capabilities.items()},
    }

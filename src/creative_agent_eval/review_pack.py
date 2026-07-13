from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .evaluation.oracles import OracleCapability, classify_check
from .models import EvalCase


def load_lineage_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expand_lineage(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    global_fields = dict(manifest.get("global_fields", {}))
    expanded: dict[str, dict[str, Any]] = {}
    for group in manifest.get("groups", []):
        group_fields = {key: value for key, value in group.items() if key != "case_ids"}
        for case_id in group.get("case_ids", []):
            if case_id in expanded:
                raise ValueError(f"duplicate lineage entry: {case_id}")
            expanded[case_id] = {**global_fields, **group_fields, "case_id": case_id}
    return expanded


def validate_lineage(cases: list[EvalCase], manifest: dict[str, Any]) -> dict[str, int]:
    expanded = expand_lineage(manifest)
    case_ids = {case.case_id for case in cases}
    lineage_ids = set(expanded)
    missing = sorted(case_ids - lineage_ids)
    extra = sorted(lineage_ids - case_ids)
    if missing or extra:
        raise ValueError(f"lineage mismatch: missing={missing}, extra={extra}")
    return {
        "case_count": len(cases),
        "lineage_count": len(expanded),
        "adapted_parallel": sum(item.get("track") == "adapted_parallel" for item in expanded.values()),
        "original_diagnostic": sum(item.get("track") == "original_diagnostic" for item in expanded.values()),
    }


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def _case_markdown(case: EvalCase, lineage: dict[str, Any]) -> str:
    sections = [
        f"## {case.case_id}｜{case.title}",
        "",
        f"- Suite：`{case.suite}`",
        f"- 状态：`{case.status}`",
        f"- Track：`{lineage.get('track', 'unassigned')}`",
        f"- 首稿来源：`{lineage.get('authorship', 'unknown')}`",
        f"- 人工审定：`{lineage.get('human_review_status', 'unknown')}`",
        f"- 直接复制公开题：`{lineage.get('direct_public_item_copy', False)}`",
        f"- 参考来源：{'；'.join(lineage.get('reference_templates', []))}",
        f"- 设计目的：{lineage.get('design_intent', '')}",
        "",
        "### 题面",
        "",
        case.prompt,
        "",
        "### 构念与原始来源字段",
        "",
        _json_block({"construct_targets": case.construct_targets, "source_basis": case.source_basis, "source_policy": case.source_policy}),
        "",
        "### 工具环境",
        "",
        _json_block(case.tool_environment),
        "",
        "### Gold",
        "",
        _json_block(case.gold),
        "",
        "### Rubric",
        "",
        _json_block([item.model_dump(mode="json") for item in case.rubric]),
        "",
        "### 边界样例",
        "",
        _json_block([item.model_dump(mode="json") for item in case.boundary_examples]),
        "",
        "### 自动检查与诊断目标",
        "",
        _json_block({"automatic_checks": case.automatic_checks, "post_training_diagnostic_targets": case.post_training_diagnostic_targets}),
        "",
        "### 审定记录",
        "",
        "- 决定：待填写（保留 / 修改 / 移除 / 重做）",
        "- 题面问题：",
        "- Gold缺口：",
        "- Rubric问题：",
        "- 工具与边界样例问题：",
        "- 修改建议：",
        "",
    ]
    return "\n".join(sections)


def _requirement_instruction(capability: OracleCapability, check_id: str) -> str:
    normalized = check_id.casefold()
    if capability == "case_fixture_required":
        if any(token in normalized for token in ("inventory", "whitelist", "material")):
            return "确认完整资源白名单、材料属性、允许替代物和禁止物；注明来源与单位。"
        if any(token in normalized for token in ("state", "timeline", "order", "sequence")):
            return "定义初始状态、允许状态转移、事件顺序和明确无效转移。"
        if "relation_table" in normalized:
            return "提供目标词或对象的允许关系、排除关系、歧义说明和泄漏检查。"
        if "base_constraints" in normalized:
            return "列出变更前约束、变更后约束、不可修改约束和冲突处理规则。"
        return "补充该Case专用的事实、关系、物理参数或状态数据。"
    if capability == "trace_required":
        return "确认必须出现的Trace事件、工具调用次数、证据回写方式、失败恢复和停止条件。"
    if capability == "semantic_required":
        return "定义语义判据，并给出明确通过、边界和失败锚点；说明是否需要Judge或人工复核。"
    return "通用规则已覆盖，无需额外人工定义。"


def collect_review_requirements(cases: list[EvalCase]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in sorted(cases, key=lambda item: item.case_id):
        for check_id in case.automatic_checks:
            capability = classify_check(check_id)
            if capability in {"deterministic", "structured_output"}:
                continue
            rows.append(
                {
                    "case_id": case.case_id,
                    "suite": case.suite,
                    "title": case.title,
                    "check_id": check_id,
                    "capability": capability,
                    "required_definition": _requirement_instruction(capability, check_id),
                    "current_case_tools": [
                        tool.get("name")
                        for tool in case.tool_environment.get("tools", [])
                        if isinstance(tool, dict) and tool.get("name")
                    ],
                    "review_status": "pending",
                    "user_definition": "",
                    "source_or_evidence": "",
                    "notes": "",
                }
            )
    return rows


def _write_requirement_files(rows: list[dict[str, Any]], out_dir: Path) -> dict[str, int]:
    counts = Counter(row["capability"] for row in rows)
    payload = {
        "requirement_count": len(rows),
        "capability_counts": dict(counts),
        "requirements": rows,
    }
    (out_dir / "oracle_requirements.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    headers = [
        "case_id",
        "suite",
        "title",
        "check_id",
        "capability",
        "required_definition",
        "current_case_tools",
        "review_status",
        "user_definition",
        "source_or_evidence",
        "notes",
    ]
    with (out_dir / "oracle_requirements.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "current_case_tools": " | ".join(row["current_case_tools"])})

    fixture_rows = [row for row in rows if row["capability"] == "case_fixture_required"]
    with (out_dir / "case_fixture_requirements.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in fixture_rows:
            writer.writerow({**row, "current_case_tools": " | ".join(row["current_case_tools"])})
    return {key: counts.get(key, 0) for key in ("case_fixture_required", "trace_required", "semantic_required")}


def build_review_pack(cases: list[EvalCase], manifest: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = validate_lineage(cases, manifest)
    lineage_map = expand_lineage(manifest)
    ordered = sorted(cases, key=lambda case: case.case_id)

    full_payload = {
        "dataset_version": manifest.get("dataset_version", "unknown"),
        "provenance_summary": manifest.get("summary", {}),
        "cases": [
            {
                "provenance": lineage_map[case.case_id],
                "case": case.model_dump(mode="json"),
            }
            for case in ordered
        ],
    }
    (out_dir / "cases_full.json").write_text(
        json.dumps(full_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    markdown = [
        "# 36题完整人工审阅包",
        "",
        "本文件由仓库当前数据自动生成。题面、工具、Gold、Rubric和边界样例均为实际运行版本。",
        "",
        "当前36题均为AI助手生成首稿，尚未完成用户逐题审定或独立专家验证。公开研究用于方法和任务结构参考，没有题目被登记为公开基准原题。",
        "",
    ]
    for case in ordered:
        markdown.append(_case_markdown(case, lineage_map[case.case_id]))
    (out_dir / "cases_full.md").write_text("\n".join(markdown), encoding="utf-8")

    with (out_dir / "review_sheet.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "case_id",
            "suite",
            "title",
            "track",
            "reference_templates",
            "decision",
            "prompt_issues",
            "gold_gaps",
            "rubric_issues",
            "tool_or_boundary_issues",
            "revision_notes",
        ])
        for case in ordered:
            lineage = lineage_map[case.case_id]
            writer.writerow([
                case.case_id,
                case.suite,
                case.title,
                lineage.get("track", ""),
                " | ".join(lineage.get("reference_templates", [])),
                "待审定",
                "",
                "",
                "",
                "",
                "",
            ])

    requirement_counts = _write_requirement_files(collect_review_requirements(ordered), out_dir)
    summary["oracle_review_requirements"] = requirement_counts
    (out_dir / "provenance_summary.json").write_text(
        json.dumps({**summary, "manifest_summary": manifest.get("summary", {})}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary

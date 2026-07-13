from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

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


def build_review_pack(cases: list[EvalCase], manifest: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = validate_lineage(cases, manifest)
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

    (out_dir / "provenance_summary.json").write_text(
        json.dumps({**summary, "manifest_summary": manifest.get("summary", {})}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary

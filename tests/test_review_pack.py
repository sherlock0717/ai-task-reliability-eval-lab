from __future__ import annotations

import json
from pathlib import Path

from creative_agent_eval.registry import load_cases
from creative_agent_eval.review_pack import build_review_pack, load_lineage_manifest, validate_lineage

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmark" / "provenance" / "lineage_rules_v0_1.json"


def test_lineage_manifest_covers_all_36_cases() -> None:
    cases = load_cases()
    manifest = load_lineage_manifest(MANIFEST)
    summary = validate_lineage(cases, manifest)
    assert summary == {
        "case_count": 36,
        "lineage_count": 36,
        "adapted_parallel": 27,
        "original_diagnostic": 9,
    }
    assert manifest["summary"]["assistant_generated_first_draft"] == 36
    assert manifest["summary"]["direct_public_item_copy"] == 0
    assert manifest["summary"]["human_reviewed"] == 0
    assert manifest["summary"]["expert_validated"] == 0


def test_review_pack_contains_full_case_contracts(tmp_path: Path) -> None:
    cases = load_cases()
    manifest = load_lineage_manifest(MANIFEST)
    summary = build_review_pack(cases, manifest, tmp_path)
    assert summary["case_count"] == 36

    full_json = json.loads((tmp_path / "cases_full.json").read_text(encoding="utf-8"))
    assert len(full_json["cases"]) == 36
    assert {item["case"]["case_id"] for item in full_json["cases"]} == {case.case_id for case in cases}
    for item in full_json["cases"]:
        case = item["case"]
        assert case["prompt"]
        assert case["tool_environment"] is not None
        assert case["gold"]
        assert len(case["rubric"]) >= 4
        assert {example["label"] for example in case["boundary_examples"]} == {"pass", "borderline", "fail"}
        assert item["provenance"]["direct_public_item_copy"] is False

    markdown = (tmp_path / "cases_full.md").read_text(encoding="utf-8")
    assert markdown.count("### 题面") == 36
    assert markdown.count("### Gold") == 36
    assert markdown.count("### Rubric") == 36
    assert markdown.count("### 边界样例") == 36

    review_sheet = (tmp_path / "review_sheet.csv").read_text(encoding="utf-8-sig")
    assert review_sheet.count("\n") >= 36
    assert (tmp_path / "provenance_summary.json").exists()

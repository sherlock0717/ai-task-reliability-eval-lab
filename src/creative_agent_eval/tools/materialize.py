from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..models import EvalCase
from .fixtures import CaseFixture, write_fixture

_INVENTORY_MARKERS = ("可用物品：", "可用资源：", "可用材料：", "Available items:", "Available resources:")


def _extract_inventory(prompt: str) -> list[str]:
    items: list[str] = []
    for line in prompt.splitlines():
        stripped = line.strip()
        for marker in _INVENTORY_MARKERS:
            if marker in stripped:
                tail = stripped.split(marker, 1)[1]
                for item in re.split(r"[、，,；;]", tail):
                    cleaned = item.strip().strip("。.")
                    if cleaned and cleaned not in items:
                        items.append(cleaned)
    return items


def _tool_default(
    tool_name: str,
    case: EvalCase,
    required: list[str],
    prohibited: list[str],
    accepted: list[str],
    inventory_items: list[str],
) -> dict[str, Any]:
    normalized = tool_name.casefold()
    common = {"case_id": case.case_id, "tool": tool_name, "status": "fixture_available"}
    if "inventory" in normalized or "resource" in normalized or "material" in normalized:
        return {**common, "items": inventory_items}
    if "constraint" in normalized or "rule" in normalized:
        return {**common, "required": required, "prohibited": prohibited}
    if "risk" in normalized or "safety" in normalized or "privacy" in normalized:
        return {**common, "risk_rules": prohibited}
    if "assumption" in normalized or "evidence" in normalized or "fact" in normalized:
        return {**common, "supported": required + accepted}
    if "state" in normalized or "timeline" in normalized or "sequence" in normalized:
        return {**common, "allowed_transitions": []}
    if "count" in normalized or "capacity" in normalized or "calculate" in normalized:
        return {**common, "calculation_mode": "deterministic", "units_required": True}
    return common


def materialize_fixture(case: EvalCase) -> CaseFixture:
    """Build a deterministic baseline fixture from one case specification.

    The generated fixture makes every declared tool addressable and records the
    case's Gold boundaries. A checked-in case-specific file can still replace
    this baseline when precise physical, semantic or state-transition values are
    needed.
    """

    tool_names = {
        str(tool.get("name"))
        for tool in case.tool_environment.get("tools", [])
        if isinstance(tool, dict) and tool.get("name")
    }
    required = [str(item) for item in case.gold.get("required_elements", [])]
    prohibited = [str(item) for item in case.gold.get("prohibited_failures", [])]
    accepted = [str(item) for item in case.gold.get("accepted_strategies", [])]
    inventory_items = _extract_inventory(case.prompt)
    inventory = {
        item: {"declared_in_prompt": True, "raw_label": item}
        for item in inventory_items
    }

    data: dict[str, Any] = {
        "tools": {
            name: {
                "default": _tool_default(
                    name,
                    case,
                    required,
                    prohibited,
                    accepted,
                    inventory_items,
                )
            }
            for name in sorted(tool_names)
        },
        "inventory": inventory,
        "constraints": {
            "required_terms": required,
            "forbidden_terms": prohibited,
        },
        "accepted_strategies": accepted,
        "risk_rules": {item: "matches prohibited failure" for item in prohibited},
        "supported_assumptions": required + accepted,
        "allowed_transitions": [],
        "automatic_checks": list(case.automatic_checks),
        "source": "generated_from_case_spec",
    }
    return CaseFixture(
        case_id=case.case_id,
        fixture_version="v0.3-generated",
        allowed_tools=tool_names,
        data=data,
    )


def write_materialized_fixtures(cases: list[EvalCase], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    for case in sorted(cases, key=lambda item: item.case_id):
        fixture = materialize_fixture(case)
        path = out_dir / f"{case.case_id}.json"
        write_fixture(fixture, path)
        manifest.append(
            {
                "case_id": case.case_id,
                "fixture_version": fixture.fixture_version,
                "allowed_tools": sorted(fixture.allowed_tools),
                "path": path.name,
                "source": fixture.data.get("source"),
            }
        )
    summary = {
        "fixture_count": len(manifest),
        "cases_with_tools": sum(bool(item["allowed_tools"]) for item in manifest),
        "cases_without_tools": sum(not item["allowed_tools"] for item in manifest),
        "fixtures": manifest,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def fixture_coverage(cases: list[EvalCase]) -> dict[str, int]:
    materialized = [materialize_fixture(case) for case in cases]
    declared_tools = sum(len(item.allowed_tools) for item in materialized)
    available_tool_entries = sum(len(item.data.get("tools", {})) for item in materialized)
    return {
        "case_count": len(cases),
        "materialized_fixture_count": len(materialized),
        "cases_with_tools": sum(bool(item.allowed_tools) for item in materialized),
        "cases_without_tools": sum(not item.allowed_tools for item in materialized),
        "declared_tool_count": declared_tools,
        "available_tool_fixture_count": available_tool_entries,
    }

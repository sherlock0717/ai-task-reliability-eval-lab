from __future__ import annotations

from typing import Any

from ..models import EvalCase
from .fixtures import CaseFixture


def materialize_fixture(case: EvalCase) -> CaseFixture:
    """Build a deterministic baseline fixture from the case specification.

    Case-specific fixture files can override this generated baseline when a task
    requires precise physical, semantic, or state-transition data.
    """
    tool_names = {
        str(tool.get("name"))
        for tool in case.tool_environment.get("tools", [])
        if isinstance(tool, dict) and tool.get("name")
    }
    required = [str(item) for item in case.gold.get("required_elements", [])]
    prohibited = [str(item) for item in case.gold.get("prohibited_failures", [])]
    accepted = [str(item) for item in case.gold.get("accepted_strategies", [])]

    data: dict[str, Any] = {
        "tools": {
            name: {
                "default": {
                    "case_id": case.case_id,
                    "tool": name,
                    "status": "fixture_available",
                }
            }
            for name in sorted(tool_names)
        },
        "constraints": {
            "required_terms": required,
            "forbidden_terms": prohibited,
        },
        "accepted_strategies": accepted,
        "risk_rules": {item: "matches prohibited failure" for item in prohibited},
        "supported_assumptions": required + accepted,
        "allowed_transitions": [],
        "source": "generated_from_case_spec",
    }
    return CaseFixture(
        case_id=case.case_id,
        fixture_version="v0.2-generated",
        allowed_tools=tool_names,
        data=data,
    )


def fixture_coverage(cases: list[EvalCase]) -> dict[str, int]:
    materialized = [materialize_fixture(case) for case in cases]
    return {
        "case_count": len(cases),
        "materialized_fixture_count": len(materialized),
        "cases_with_tools": sum(bool(item.allowed_tools) for item in materialized),
        "cases_without_tools": sum(not item.allowed_tools for item in materialized),
    }

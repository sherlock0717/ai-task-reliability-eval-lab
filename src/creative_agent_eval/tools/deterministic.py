from __future__ import annotations

import json
from typing import Any

from .base import ToolContext, ToolRegistry


def _normalise_text(value: Any) -> str:
    if isinstance(value, str):
        return value.casefold()
    return json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()


def fixture_lookup(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    tool_name = str(arguments.get("tool_name", ""))
    if not tool_name:
        raise ValueError("tool_name is required")
    tools = context.fixture.get("tools", {})
    config = tools.get(tool_name)
    if config is None:
        raise KeyError(f"no fixture for tool: {tool_name}")
    response_key = str(arguments.get("response_key", "default"))
    responses = config.get("responses", {})
    if response_key in responses:
        return {"value": responses[response_key], "response_key": response_key}
    if "default" in config:
        return {"value": config["default"], "response_key": "default"}
    raise KeyError(f"no response for {tool_name}:{response_key}")


def inventory_lookup(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    item = str(arguments.get("item", ""))
    if not item:
        raise ValueError("item is required")
    inventory = context.fixture.get("inventory", {})
    if item not in inventory:
        return {"found": False, "item": item, "properties": {}}
    return {"found": True, "item": item, "properties": inventory[item]}


def constraint_check(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    plan = _normalise_text(arguments.get("plan", ""))
    constraints = context.fixture.get("constraints", {})
    forbidden = [term for term in constraints.get("forbidden_terms", []) if term.casefold() in plan]
    missing = [term for term in constraints.get("required_terms", []) if term.casefold() not in plan]
    return {"passed": not forbidden and not missing, "forbidden_hits": forbidden, "missing_required": missing}


def risk_check(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    plan = _normalise_text(arguments.get("plan", ""))
    rules = context.fixture.get("risk_rules", {})
    risks = [{"term": term, "risk": risk} for term, risk in rules.items() if term.casefold() in plan]
    return {"passed": not risks, "risks": risks}


def assumption_check(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    assumptions = [str(item) for item in arguments.get("assumptions", [])]
    supported_set = {str(item) for item in context.fixture.get("supported_assumptions", [])}
    supported = [item for item in assumptions if item in supported_set]
    unsupported = [item for item in assumptions if item not in supported_set]
    return {"supported": supported, "unsupported": unsupported}


def count_check(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    del context
    values = arguments.get("values", [])
    minimum = int(arguments.get("minimum", 0))
    maximum_raw = arguments.get("maximum")
    maximum = int(maximum_raw) if maximum_raw is not None else None
    count = len(values) if isinstance(values, list) else len(str(values))
    passed = count >= minimum and (maximum is None or count <= maximum)
    return {"passed": passed, "count": count, "minimum": minimum, "maximum": maximum}


def state_check(arguments: dict[str, Any], context: ToolContext) -> dict[str, Any]:
    transitions = arguments.get("transitions", [])
    allowed = {
        (str(pair[0]), str(pair[1]))
        for pair in context.fixture.get("allowed_transitions", [])
        if isinstance(pair, list) and len(pair) == 2
    }
    invalid: list[Any] = []
    for pair in transitions:
        if not isinstance(pair, list) or len(pair) != 2:
            invalid.append(pair)
            continue
        edge = (str(pair[0]), str(pair[1]))
        if allowed and edge not in allowed:
            invalid.append(pair)
    return {"passed": not invalid, "invalid_transitions": invalid}


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register("fixture_lookup", fixture_lookup)
    registry.register("inventory_lookup", inventory_lookup)
    registry.register("constraint_check", constraint_check)
    registry.register("risk_check", risk_check)
    registry.register("assumption_check", assumption_check)
    registry.register("count_check", count_check)
    registry.register("state_check", state_check)
    return registry

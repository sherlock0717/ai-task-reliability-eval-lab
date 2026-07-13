from creative_agent_eval.registry import load_cases, validate_registry


def test_registry_is_complete() -> None:
    summary = validate_registry()
    assert summary["case_count"] == 36
    assert summary["prompt_finalized_count"] == 36
    assert summary["pilot_count"] == 36
    assert summary["rubric_criterion_count"] >= 144


def test_each_case_has_full_pilot_material() -> None:
    for case in load_cases():
        assert case.prompt.strip()
        assert case.tool_environment["tools"]
        assert case.gold["required_elements"]
        assert case.gold["accepted_strategies"]
        assert case.gold["prohibited_failures"]
        assert {example.label for example in case.boundary_examples} == {"pass", "borderline", "fail"}

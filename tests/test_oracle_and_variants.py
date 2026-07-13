from collections import Counter

from creative_agent_eval.evaluation.oracles import evaluate_check, oracle_coverage
from creative_agent_eval.registry import load_cases
from creative_agent_eval.variants import build_variant_plan


def test_oracle_capabilities_cover_all_automatic_checks():
    coverage = oracle_coverage(load_cases())
    detailed = sum(
        coverage[f"capability_{name}"]
        for name in (
            "deterministic",
            "structured_output",
            "trace_required",
            "case_fixture_required",
            "semantic_required",
        )
    )
    assert detailed == coverage["automatic_check_count"] == 173
    assert coverage["generic_oracle_supported"] >= 70


def test_numeric_count_constraints_are_executable():
    cases = load_cases()
    use_case = next(case for case in cases if "use_count=8" in case.automatic_checks)
    passed = evaluate_check(use_case, "use_count=8", {"uses": list(range(8))})
    failed = evaluate_check(use_case, "use_count=8", {"uses": list(range(7))})
    assert passed.status == "pass"
    assert failed.status == "fail"

    accessory_case = next(case for case in cases if "accessory_count<=1" in case.automatic_checks)
    assert evaluate_check(accessory_case, "accessory_count<=1", {"accessories": []}).status == "pass"
    assert evaluate_check(accessory_case, "accessory_count<=1", {"accessories": [1, 2]}).status == "fail"


def test_variant_plan_has_six_conditions_per_case():
    plan = build_variant_plan(load_cases())
    assert plan.case_count == 36
    assert plan.variant_count == 36 * 6
    counts = Counter(item.kind for item in plan.variants)
    assert set(counts.values()) == {36}
    by_case = Counter(item.case_id for item in plan.variants)
    assert set(by_case.values()) == {6}
    assert sum(item.status == "materialized" for item in plan.variants) == 36 * 4
    assert sum(item.status == "planned" for item in plan.variants) == 36 * 2


def test_materialized_variants_preserve_problem_family_and_source_hash():
    cases = {case.case_id: case for case in load_cases()}
    plan = build_variant_plan(list(cases.values()))
    for variant in plan.variants:
        assert variant.problem_family == cases[variant.case_id].problem_family
        assert len(variant.source_prompt_hash) == 64
        if variant.status == "materialized":
            assert variant.prompt is not None
        if variant.kind == "tool_fault":
            assert variant.fault_profile["recoverable"] is True

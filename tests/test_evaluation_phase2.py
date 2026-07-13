from creative_agent_eval.evaluation.oracles import evaluate_automatic_checks, oracle_coverage
from creative_agent_eval.evaluation.scoring import score_boundary_example
from creative_agent_eval.registry import load_cases
from creative_agent_eval.tools.materialize import fixture_coverage, materialize_fixture


def test_all_cases_materialize_fixture():
    cases = load_cases()
    summary = fixture_coverage(cases)
    assert summary["case_count"] == 36
    assert summary["materialized_fixture_count"] == 36
    for case in cases:
        fixture = materialize_fixture(case)
        declared = {
            tool["name"]
            for tool in case.tool_environment.get("tools", [])
            if isinstance(tool, dict) and tool.get("name")
        }
        assert fixture.allowed_tools == declared
        assert fixture.data["source"] == "generated_from_case_spec"


def test_108_boundary_examples_have_scoring_contracts():
    cases = load_cases()
    examples = [example for case in cases for example in case.boundary_examples]
    assert len(examples) == 108
    for case in cases:
        assert {example.label for example in case.boundary_examples} == {"pass", "borderline", "fail"}
        for example in case.boundary_examples:
            scores = score_boundary_example(case, example)
            assert len(scores) == len(case.rubric)
            expected = {"pass": 2, "borderline": 1, "fail": 0}[example.label]
            assert all(item.score == expected for item in scores)


def test_automatic_checks_have_explicit_oracle_status():
    cases = load_cases()
    coverage = oracle_coverage(cases)
    assert coverage["automatic_check_count"] >= 108
    assert coverage["generic_oracle_supported"] > 0
    for case in cases:
        results = evaluate_automatic_checks(case, case.boundary_examples[0].output)
        assert len(results) == len(case.automatic_checks)
        assert all(result.status in {"pass", "fail", "needs_review"} for result in results)

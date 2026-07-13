import json

from creative_agent_eval.experiments import build_experiment_plan
from creative_agent_eval.offline import run_offline_plan
from creative_agent_eval.registry import load_cases
from creative_agent_eval.tools.materialize import write_materialized_fixtures


def test_materialize_writes_36_files_and_manifest(tmp_path):
    summary = write_materialized_fixtures(load_cases(), tmp_path)
    assert summary["fixture_count"] == 36
    assert len(list(tmp_path.glob("[A-D][0-9][0-9].json"))) == 36
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["fixture_count"] == 36


def test_default_offline_plan_has_432_runs():
    plan = build_experiment_plan(load_cases())
    assert plan.case_count == 36
    assert plan.run_count == 36 * 4 * 3
    assert len({run.run_id for run in plan.runs}) == plan.run_count


def test_offline_matrix_writes_trace_and_regression_files(tmp_path):
    cases = load_cases()
    plan = build_experiment_plan(cases)
    summary = run_offline_plan(plan, cases, tmp_path, max_runs=12)
    assert summary["executed_run_count"] == 12
    assert summary["terminal_states"] == {"completed": 12}
    assert len((tmp_path / "traces.jsonl").read_text(encoding="utf-8").splitlines()) == 12
    assert len((tmp_path / "boundary_regressions.jsonl").read_text(encoding="utf-8").splitlines()) == 12

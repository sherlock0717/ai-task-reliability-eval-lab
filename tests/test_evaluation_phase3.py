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


def test_offline_matrix_writes_trace_score_regression_and_ledger(tmp_path):
    cases = load_cases()
    plan = build_experiment_plan(cases)
    summary = run_offline_plan(plan, cases, tmp_path, max_runs=12)
    assert summary["completed_run_count"] == 12
    assert summary["terminal_states"] == {"completed": 12}
    for name in (
        "traces.jsonl",
        "boundary_regressions.jsonl",
        "case_scores.jsonl",
        "trace_evaluations.jsonl",
    ):
        assert len((tmp_path / name).read_text(encoding="utf-8").splitlines()) == 12
    assert sum(summary["criterion_verdicts"].values()) > 0
    assert set(summary["trace_oracle_statuses"]) == {"pass", "fail", "needs_review"}
    assert all(value >= 0 for value in summary["trace_oracle_statuses"].values())
    ledger = json.loads((tmp_path / "ledger.json").read_text(encoding="utf-8"))
    assert len(ledger["entries"]) == 12


def test_offline_matrix_resume_skips_completed_runs(tmp_path):
    cases = load_cases()
    plan = build_experiment_plan(cases)
    first = run_offline_plan(plan, cases, tmp_path, max_runs=5)
    second = run_offline_plan(plan, cases, tmp_path, max_runs=5, resume=True)
    assert first["completed_run_count"] == 5
    assert second["completed_run_count"] == 10
    assert second["remaining_run_count"] == plan.run_count - 10
    for name in ("traces.jsonl", "case_scores.jsonl", "trace_evaluations.jsonl"):
        assert len((tmp_path / name).read_text(encoding="utf-8").splitlines()) == 10

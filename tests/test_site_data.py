from creative_agent_eval.registry import load_cases


def test_page_data_has_all_case_ids() -> None:
    assert [case.case_id for case in load_cases()] == [f"{prefix}{number:02d}" for prefix in "ABCD" for number in range(1, 10)]

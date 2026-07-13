from creative_agent_eval.registry import validate_registry

def test_registry():
    s=validate_registry()
    assert s["case_count"]==36
    assert s["prompt_finalized_count"]==0
    assert s["status_counts"]=={"specification":36}

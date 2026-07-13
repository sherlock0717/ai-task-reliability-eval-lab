import json
from collections import Counter
from pathlib import Path
from .models import EvalCaseSpec

DEFAULT_REGISTRY = Path(__file__).resolve().parents[2] / "benchmark" / "cases" / "case_registry_v0_1.jsonl"

def load_registry(path: Path = DEFAULT_REGISTRY) -> list[EvalCaseSpec]:
    cases=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip(): cases.append(EvalCaseSpec.model_validate(json.loads(line)))
    return cases

def validate_registry(path: Path = DEFAULT_REGISTRY) -> dict:
    cases=load_registry(path)
    ids=[c.case_id for c in cases]
    dup=[k for k,v in Counter(ids).items() if v>1]
    if dup: raise ValueError(f"duplicate IDs: {dup}")
    counts=Counter(c.suite for c in cases)
    expected={"psychometric_probe":9,"constrained_problem_solving":9,"creative_artifact":9,"loop_adaptation_recovery":9}
    if dict(counts)!=expected: raise ValueError(f"unexpected suite counts: {dict(counts)}")
    return {"case_count":len(cases),"suite_counts":dict(counts),"prompt_finalized_count":sum(c.prompt_finalized for c in cases),"status_counts":dict(Counter(c.status for c in cases))}

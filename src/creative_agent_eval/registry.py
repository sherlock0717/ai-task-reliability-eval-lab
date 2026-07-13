from __future__ import annotations

from collections import Counter
from pathlib import Path
import gzip
import json

from .models import EvalCase

DEFAULT_REGISTRY_DIR = Path(__file__).resolve().parents[2] / "docs" / "data"
CASE_FILES = (
    "a1.json.gz", "a2.json.gz", "a3.json.gz",
    "b1.json.gz", "b04.json", "b05.json", "b06.json", "b3.json.gz",
    "c1.json.gz", "c2.json.gz", "c3.json.gz",
    "d01.json", "d02.json", "d03.json", "d2.json.gz", "d3.json.gz",
)


def _read_payload(path: Path) -> dict:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_cases(path: Path = DEFAULT_REGISTRY_DIR) -> list[EvalCase]:
    files = [path] if path.is_file() else [path / name for name in CASE_FILES]
    cases: list[EvalCase] = []
    for file_path in files:
        payload = _read_payload(file_path)
        cases.extend(EvalCase.model_validate(item) for item in payload["cases"])
    return cases


def validate_registry(path: Path = DEFAULT_REGISTRY_DIR) -> dict[str, object]:
    cases = load_cases(path)
    ids = [case.case_id for case in cases]
    duplicates = [case_id for case_id, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise ValueError(f"duplicate case IDs: {duplicates}")

    expected = {
        "psychometric_probe": 9,
        "creative_problem_solving": 9,
        "creative_artifact": 9,
        "loop_adaptation_recovery": 9,
    }
    counts = dict(Counter(case.suite for case in cases))
    if counts != expected:
        raise ValueError(f"unexpected suite distribution: {counts}")

    labels = {example.label for case in cases for example in case.boundary_examples}
    if labels != {"pass", "borderline", "fail"}:
        raise ValueError(f"boundary labels incomplete: {labels}")

    return {
        "case_count": len(cases),
        "suite_counts": counts,
        "prompt_finalized_count": sum(case.prompt_finalized for case in cases),
        "pilot_count": sum(case.status == "pilot" for case in cases),
        "rubric_criterion_count": sum(len(case.rubric) for case in cases),
    }

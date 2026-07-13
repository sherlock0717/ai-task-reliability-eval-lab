from __future__ import annotations

from pathlib import Path
import json

from creative_agent_eval.registry import load_cases

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "cases_v0_2_readable.json"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset_version": "v0.2",
        "cases": [case.model_dump(mode="json") for case in load_cases()],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()

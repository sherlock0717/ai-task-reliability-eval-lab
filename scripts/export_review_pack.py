from __future__ import annotations

import argparse
from pathlib import Path

from creative_agent_eval.registry import load_cases
from creative_agent_eval.review_pack import build_review_pack, load_lineage_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "benchmark" / "provenance" / "lineage_rules_v0_1.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "review_pack"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the complete 36-case human review pack.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    summary = build_review_pack(
        load_cases(),
        load_lineage_manifest(args.manifest),
        args.out_dir,
    )
    print(summary)


if __name__ == "__main__":
    main()

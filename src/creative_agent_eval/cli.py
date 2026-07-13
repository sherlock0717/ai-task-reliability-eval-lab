from __future__ import annotations

import argparse
import json
from pathlib import Path

from .registry import DEFAULT_REGISTRY_DIR, validate_registry


def main() -> None:
    parser = argparse.ArgumentParser(prog="creative-agent-eval")
    subcommands = parser.add_subparsers(dest="command", required=True)
    validate = subcommands.add_parser("validate-registry")
    validate.add_argument("--path", type=Path, default=DEFAULT_REGISTRY_DIR)
    args = parser.parse_args()

    if args.command == "validate-registry":
        print(json.dumps(validate_registry(args.path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

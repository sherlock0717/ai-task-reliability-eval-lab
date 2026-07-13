from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CaseFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    fixture_version: str = "v0.1"
    allowed_tools: set[str] = Field(default_factory=set)
    data: dict[str, Any] = Field(default_factory=dict)


def load_fixture(path: Path) -> CaseFixture:
    return CaseFixture.model_validate_json(path.read_text(encoding="utf-8"))


def write_fixture(fixture: CaseFixture, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(fixture.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

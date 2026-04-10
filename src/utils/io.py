"""Filesystem and structured file helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def read_text(path: Path, *, encoding: str = "utf-8") -> str:
    """Read entire text file."""
    return Path(path).read_text(encoding=encoding)


def read_json(path: Path, *, encoding: str = "utf-8") -> Any:
    """Load JSON from file (object or array)."""
    raw = Path(path).read_text(encoding=encoding)
    return json.loads(raw)


def write_json(path: Path, data: Any, *, encoding: str = "utf-8", indent: int = 2) -> None:
    """Write pretty-printed JSON (creates parent directories)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + "\n", encoding=encoding)


def resolve_repo_path(repo_root: Path, maybe_relative: Union[str, Path]) -> Path:
    """Resolve a path that may be relative to repo root."""
    p = Path(maybe_relative)
    if p.is_absolute():
        return p
    return (Path(repo_root) / p).resolve()


def read_json_if_exists(path: Path) -> Optional[Any]:
    """Return parsed JSON or None if file does not exist."""
    p = Path(path)
    if not p.is_file():
        return None
    return read_json(p)


def build_input_snapshot(task: Dict[str, Any], repo_root: Path) -> Dict[str, Any]:
    """Resolve input_files for trace storage (content or error per file)."""
    repo_root = Path(repo_root)
    resolved: List[Dict[str, Any]] = []
    for spec in task.get("input_files") or []:
        rel = spec.get("path")
        if not rel:
            continue
        role = spec.get("role", "")
        path = (repo_root / rel).resolve()
        entry: Dict[str, Any] = {"path": rel, "role": role}
        try:
            entry["content"] = read_text(path)
        except OSError as exc:
            entry["error"] = str(exc)
        resolved.append(entry)
    return {"task": task, "resolved_files": resolved}

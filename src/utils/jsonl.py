"""JSONL read/write helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, TextIO


def read_jsonl(path: Path, *, encoding: str = "utf-8") -> List[Dict[str, Any]]:
    """Read a JSONL file; each line must be one JSON object."""
    path = Path(path)
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding=encoding, newline="") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_no}") from exc
            if not isinstance(obj, dict):
                raise TypeError(f"Expected object per line in {path}:{line_no}")
            rows.append(obj)
    return rows


def iter_jsonl(path: Path, *, encoding: str = "utf-8") -> Iterator[Dict[str, Any]]:
    """Stream JSONL objects line by line."""
    path = Path(path)
    with path.open("r", encoding=encoding, newline="") as f:
        yield from iter_jsonl_file(f, path_hint=str(path))


def iter_jsonl_file(
    f: TextIO, *, path_hint: str = "<stream>"
) -> Iterator[Dict[str, Any]]:
    for line_no, line in enumerate(f, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON at {path_hint}:{line_no}") from exc
        if not isinstance(obj, dict):
            raise TypeError(f"Expected object per line in {path_hint}:{line_no}")
        yield obj


def append_jsonl(path: Path, record: Dict[str, Any], *, encoding: str = "utf-8") -> None:
    """Append one JSON object as a single line (creates parent dirs)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    with path.open("a", encoding=encoding, newline="") as f:
        f.write(line)


def write_jsonl(
    path: Path,
    records: Iterable[Dict[str, Any]],
    *,
    encoding: str = "utf-8",
) -> None:
    """Overwrite path with one JSON object per line."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")


def dump_jsonl(
    path: Path,
    records: Iterable[Dict[str, Any]],
    *,
    encoding: str = "utf-8",
    transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
) -> None:
    """Write records with optional per-row transform."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as f:
        for rec in records:
            out = transform(rec) if transform else rec
            f.write(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")

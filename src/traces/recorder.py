"""Append and load trace records as JSONL."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.jsonl import append_jsonl, read_jsonl

from .schema import TraceRecord, trace_from_dict, trace_to_dict

logger = logging.getLogger(__name__)


def append_trace(path: Path, record: TraceRecord, *, encoding: str = "utf-8") -> None:
    """Serialize one trace to JSONL; creates parent directories."""
    path = Path(path)
    try:
        payload = trace_to_dict(record)
        append_jsonl(path, payload, encoding=encoding)
    except OSError as exc:
        logger.exception("Failed to write trace to %s", path)
        raise RuntimeError(f"Could not append trace to {path}") from exc
    except (TypeError, ValueError) as exc:
        logger.exception("Trace serialization failed for %s", path)
        raise RuntimeError("Trace record could not be serialized") from exc


def load_traces(path: Path, *, encoding: str = "utf-8") -> List[TraceRecord]:
    """Load all trace rows from a JSONL file."""
    path = Path(path)
    if not path.is_file():
        return []
    try:
        rows: List[Dict[str, Any]] = read_jsonl(path, encoding=encoding)
    except (OSError, ValueError, TypeError) as exc:
        logger.exception("Failed to read traces from %s", path)
        raise RuntimeError(f"Could not load traces from {path}") from exc
    out: List[TraceRecord] = []
    for i, row in enumerate(rows):
        try:
            out.append(trace_from_dict(row))
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Skipping invalid trace row %s in %s: %s", i, path, exc)
    return out


def load_traces_safe(path: Path, *, encoding: str = "utf-8") -> List[TraceRecord]:
    """Like load_traces but returns partial results on row errors (logged)."""
    path = Path(path)
    if not path.is_file():
        return []
    out: List[TraceRecord] = []
    try:
        rows = read_jsonl(path, encoding=encoding)
    except (OSError, ValueError, TypeError) as exc:
        logger.error("Failed to read %s: %s", path, exc)
        return []
    for i, row in enumerate(rows):
        try:
            out.append(trace_from_dict(row))
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Skipping trace row %s: %s", i, exc)
    return out

"""Trace record definitions for experiment runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Union


def trace_to_dict(record: "TraceRecord") -> Dict[str, Any]:
    """Serialize a TraceRecord to a JSON-friendly dict."""
    return asdict(record)


def trace_from_dict(data: Mapping[str, Any]) -> "TraceRecord":
    """Deserialize a mapping into TraceRecord (best-effort for loaded JSON)."""
    return TraceRecord(
        run_id=str(data["run_id"]),
        task_id=str(data["task_id"]),
        candidate_id=str(data["candidate_id"]),
        status=str(data["status"]),
        input_snapshot=dict(data["input_snapshot"]),
        raw_output=data["raw_output"],
        normalized_output=data["normalized_output"],
        intermediate_steps=list(data.get("intermediate_steps") or []),
        tool_calls=list(data.get("tool_calls") or []),
        human_interventions=list(data.get("human_interventions") or []),
        error_log=list(data.get("error_log") or []),
        latency_ms=float(data["latency_ms"]),
        token_usage=dict(data.get("token_usage") or {}),
        estimated_cost=data.get("estimated_cost"),
        started_at=str(data["started_at"]),
        finished_at=str(data["finished_at"]),
        provider=str(data.get("provider") or ""),
        model_name=str(data.get("model_name") or ""),
        is_mock=bool(data.get("is_mock", True)),
    )


@dataclass
class TraceRecord:
    """Single task execution trace (one row in traces JSONL)."""

    run_id: str
    task_id: str
    candidate_id: str
    status: str
    input_snapshot: Dict[str, Any]
    raw_output: str
    normalized_output: Union[str, Dict[str, Any], List[Any], None]
    intermediate_steps: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    human_interventions: List[Dict[str, Any]] = field(default_factory=list)
    error_log: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    estimated_cost: Optional[float] = None
    started_at: str = ""
    finished_at: str = ""
    provider: str = ""
    model_name: str = ""
    is_mock: bool = True

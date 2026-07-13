from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

EventType = Literal[
    "run_started",
    "model_requested",
    "model_responded",
    "candidate_created",
    "critique_created",
    "revision_created",
    "candidate_selected",
    "tool_plan_created",
    "tool_requested",
    "tool_returned",
    "tool_failed",
    "tool_retry",
    "event_acknowledged",
    "revalidation_started",
    "revalidation_completed",
    "stop_decision",
    "criterion_checked",
    "run_completed",
    "run_failed",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int = Field(ge=0)
    event_type: EventType
    timestamp: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class RunTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str
    case_id: str
    loop_id: str
    provider_id: str
    seed: int
    started_at: datetime
    ended_at: datetime | None = None
    terminal_state: Literal["running", "completed", "failed"] = "running"
    events: list[TraceEvent] = Field(default_factory=list)
    final_output: Any = None
    error: str | None = None

    def events_of(self, event_type: EventType) -> list[TraceEvent]:
        return [event for event in self.events if event.event_type == event_type]

    def has_event(self, event_type: EventType) -> bool:
        return any(event.event_type == event_type for event in self.events)


class TraceRecorder:
    def __init__(self, case_id: str, loop_id: str, provider_id: str, seed: int) -> None:
        self.trace = RunTrace(
            run_id=str(uuid4()),
            case_id=case_id,
            loop_id=loop_id,
            provider_id=provider_id,
            seed=seed,
            started_at=utc_now(),
        )

    def emit(self, event_type: EventType, payload: dict[str, Any] | None = None) -> None:
        self.trace.events.append(
            TraceEvent(
                index=len(self.trace.events),
                event_type=event_type,
                timestamp=utc_now(),
                payload=payload or {},
            )
        )

    def complete(self, final_output: Any) -> RunTrace:
        self.trace.final_output = final_output
        self.trace.terminal_state = "completed"
        self.trace.ended_at = utc_now()
        self.emit("stop_decision", {"decision": "stop", "reason": "final_output_ready"})
        self.emit("run_completed", {"has_output": final_output is not None})
        return self.trace

    def fail(self, error: Exception | str) -> RunTrace:
        self.trace.error = str(error)
        self.trace.terminal_state = "failed"
        self.trace.ended_at = utc_now()
        self.emit("stop_decision", {"decision": "stop", "reason": "run_failed"})
        self.emit("run_failed", {"error": self.trace.error})
        return self.trace

    def append_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(self.trace.model_dump_json() + "\n")

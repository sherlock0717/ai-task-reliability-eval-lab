"""Abstract workflow adapter — extend for direct / retrieve / planexec / humangate."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class WorkflowAdapter(ABC):
    """Unified interface for task execution strategies (workflow policies).

    Subclasses implement a concrete candidate (e.g. direct LLM, RAG, planner).
    Return dicts must be JSON-serializable where possible; raw_output is always str.
    """

    @property
    @abstractmethod
    def candidate_id(self) -> str:
        """Stable id for traces and scoring (e.g. direct-v0.1)."""

    @abstractmethod
    def run_task(self, task: Dict[str, Any], *, repo_root: Path) -> Dict[str, Any]:
        """Execute one task.

        Expected keys in the returned dict (runners may add more):
        - status: "success" | "failed"
        - raw_output: str (model text)
        - normalized_output: str | dict | list | None (parsed or trimmed)
        - intermediate_steps: list (optional)
        - tool_calls: list (optional)
        - human_interventions: list (optional)
        - error_log: list[str]
        - latency_ms: float
        - token_usage: dict (e.g. prompt/completion/total)
        - estimated_cost: float | None
        """

    def validate_task_schema(
        self,
        task: Dict[str, Any],
        *,
        schema_path: Optional[Path] = None,
    ) -> None:
        """Optional hook: validate task against JSON Schema if jsonschema is available."""
        if schema_path is None:
            return
        try:
            import jsonschema  # type: ignore
        except ImportError:
            return
        from src.utils.io import read_json

        schema = read_json(Path(schema_path))
        jsonschema.validate(instance=task, schema=schema)

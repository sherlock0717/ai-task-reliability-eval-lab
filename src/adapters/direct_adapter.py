"""Direct (single-turn) baseline — no retrieval, planning, or human gate."""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from .base import WorkflowAdapter


class TextGenerator(Protocol):
    """Pluggable LLM / local model interface for a later real implementation."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        task: Dict[str, Any],
    ) -> str:
        ...


@dataclass
class MockTextGenerator:
    """Deterministic, task-shaped placeholder output until a real API is wired."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        task: Dict[str, Any],
    ) -> str:
        _ = system_prompt
        if task_type == "extraction":
            return self._mock_extraction(user_prompt, task)
        if task_type == "rewrite":
            return self._mock_rewrite(user_prompt, task)
        if task_type == "qa":
            return self._mock_qa(user_prompt, task)
        return self._mock_generic(user_prompt, task)

    def _mock_extraction(self, user_prompt: str, task: Dict[str, Any]) -> str:
        has_go = "Go" in user_prompt or "go" in user_prompt
        has_java = "Java" in user_prompt
        lines = [
            "公司/团队：未提及",
            "岗位名称：高级后端工程师（支付清算方向）",
            "工作地点与是否远程：上海陆家嘴；每周 2 天现场，其余可远程；入职首月全周现场",
            "经验年限要求：5 年及以上后端经验，其中至少 3 年高并发交易或账务类系统经验",
            "学历要求：本科及以上学历",
            f"必备技术栈：熟练掌握 Go 或 Java 之一；分布式事务；消息队列；MySQL/PostgreSQL（检测到 Go 提及：{'是' if has_go else '未明确'}；Java：{'是' if has_java else '未明确'}）",
            "加分项：支付/清算/对账经验；监管报送与审计留痕",
            "薪资或福利：薪资面议；年度体检；补充医疗保险；弹性工时（清算窗口外）",
            "申请方式或链接：talent@example-corp.invalid（邮件标题注明「后端-清算-姓名」）",
        ]
        return "\n".join(lines)

    def _mock_rewrite(self, user_prompt: str, task: Dict[str, Any]) -> str:
        _ = task
        bullets = [
            "- 主导数据平台整合，将多业务线脚本收敛为统一数据管道，显著缩短报表产出周期（由原一至两天缩短至当日可见）。",
            "- 设计并落地数据质量校验与告警机制，降低坏数据流入与下游运营投诉。",
            "- 基于 Spark 与公司自研调度构建可运维流水线，并完成与云平台的权限与配额对接。",
        ]
        body = "\n".join(bullets)
        return f"## 简历要点（共 3 条）\n{body}\n\n（Mock：基于输入材料改写，未调用真实模型。）\n"

    def _mock_qa(self, user_prompt: str, task: Dict[str, Any]) -> str:
        _ = task
        # Simple heuristic aligned with reference policy task
        answer_days = 0
        if "7 月 1 日入职" in user_prompt or "7月1日" in user_prompt:
            answer_days = 0
        obj = {
            "answer_days": answer_days,
            "rule_refs": ["R1"],
            "reasoning": "Mock：当年 7 月入职，司龄在当年不满一年，按规则不享受带薪年假。",
        }
        return json.dumps(obj, ensure_ascii=False)

    def _mock_generic(self, user_prompt: str, task: Dict[str, Any]) -> str:
        tid = task.get("task_id", "unknown")
        return (
            f"【Mock 直答】task={tid}\n\n"
            f"{user_prompt[:1200]}\n\n"
            "（以上为占位：接入真实 LLM 后替换 MockTextGenerator。）"
        )


class DirectAdapter(WorkflowAdapter):
    """Single-turn completion; swap `generator` for production LLM calls."""

    def __init__(self, generator: Optional[TextGenerator] = None) -> None:
        self._generator: TextGenerator = generator or MockTextGenerator()

    @property
    def candidate_id(self) -> str:
        return "direct-v0.1"

    def run_task(self, task: Dict[str, Any], *, repo_root: Path) -> Dict[str, Any]:
        started = time.perf_counter()
        error_log: List[str] = []
        task_type = str(task.get("task_type", "unknown"))

        user_prompt, file_note = _build_user_prompt(task, repo_root)
        system_prompt = (
            "You are a careful assistant for office and knowledge-work tasks. "
            "Follow the user instructions and constraints. "
            "This is a mock direct baseline when no real API is configured."
        )

        raw_output = ""
        status = "success"
        try:
            raw_output = self._generator.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                task_type=task_type,
                task=task,
            )
        except Exception as exc:  # noqa: BLE001 — surface to trace
            status = "failed"
            error_log.append(str(exc))
            raw_output = ""

        normalized_output: Any = _normalize_output(
            raw_output, expected_type=str(task.get("expected_output_type", "text"))
        )
        if status == "success" and task.get("expected_output_type") == "json":
            if isinstance(normalized_output, str):
                try:
                    normalized_output = json.loads(normalized_output)
                except json.JSONDecodeError:
                    error_log.append("normalized_output: JSON parse failed after generation")
                    status = "failed"

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return {
            "status": status,
            "raw_output": raw_output,
            "normalized_output": normalized_output,
            "intermediate_steps": [{"step": "direct_single_turn", "detail": file_note}],
            "tool_calls": [],
            "human_interventions": [],
            "error_log": error_log,
            "latency_ms": elapsed_ms,
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "estimated_cost": None,
        }


def _build_user_prompt(task: Dict[str, Any], repo_root: Path) -> tuple[str, str]:
    """Concatenate task prompt with resolved file contents."""
    parts: List[str] = [str(task.get("prompt", "")).strip()]
    notes: List[str] = []
    for spec in task.get("input_files") or []:
        rel = spec.get("path")
        if not rel:
            continue
        path = (repo_root / rel).resolve()
        try:
            text = path.read_text(encoding="utf-8")
            parts.append(f"\n--- 文件: {rel} ---\n{text}")
            notes.append(f"loaded {rel} ({len(text)} chars)")
        except OSError as exc:
            parts.append(f"\n--- 文件: {rel} (读取失败) ---\n[{exc}]")
            notes.append(f"failed {rel}: {exc}")
    return "\n".join(parts), "; ".join(notes) if notes else "no input_files"


def _normalize_output(raw: str, *, expected_type: str) -> Any:
    text = raw.strip()
    if expected_type == "json":
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return text
        return text
    return text


def new_run_id() -> str:
    """UUID for trace / output grouping."""
    return str(uuid.uuid4())

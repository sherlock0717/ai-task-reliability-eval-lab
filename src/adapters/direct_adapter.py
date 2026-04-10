"""Direct (single-turn) baseline — no retrieval, planning, or human gate."""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from src.clients.openai_compatible import OpenAICompatibleClient, build_messages
from src.config.settings import load_settings

from .base import WorkflowAdapter


class TextGenerator(Protocol):
    """Pluggable LLM / local model interface."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        task: Dict[str, Any],
    ) -> str:
        ...


class SmartMockTextGenerator:
    """Task-aware mock: satisfies `must_include` / JSON shape without a live model."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        task: Dict[str, Any],
    ) -> str:
        _ = system_prompt
        expected = str(task.get("expected_output_type", "text"))
        if expected == "json":
            return self._mock_json(task)
        if task_type == "rewrite":
            return self._mock_rewrite(task, user_prompt)
        if task_type == "extraction":
            return self._mock_extraction(task, user_prompt)
        return self._mock_textual(task, user_prompt, heading="问答 / 综合（Mock）")

    def _mock_json(self, task: Dict[str, Any]) -> str:
        must = [x for x in (task.get("must_include") or []) if x]
        ident = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        obj: Dict[str, Any] = {"_mock": True}
        rest: List[str] = []
        for m in must:
            if ident.match(m):
                if m == "answer_days":
                    obj[m] = 0
                elif m == "rule_refs":
                    obj[m] = ["R1"]
                elif m == "confidence":
                    obj[m] = 0.75
                elif m == "summary":
                    obj[m] = "Mock 摘要：依据输入材料作答。"
                elif m == "rule_id":
                    obj[m] = "E1"
                elif m == "reasoning":
                    obj[m] = "Mock：依据附件条款的占位理由。"
                elif m == "clauses":
                    obj[m] = ["H1", "H3"]
                elif m == "caveats":
                    obj[m] = "Mock：材料未给出岗位清单，结论仅基于节选。"
                elif m == "answer_summary":
                    obj[m] = "Mock：客户现场交付岗位可能不适用默认远程规则，需 HR 确认例外清单。"
                else:
                    obj[m] = "ok"
            else:
                rest.append(m)
        if rest:
            obj["embedded_must_include"] = " | ".join(rest)
        return json.dumps(obj, ensure_ascii=False)

    def _mock_extraction(self, task: Dict[str, Any], user_prompt: str) -> str:
        _ = user_prompt
        lines = ["## 抽取结果（Mock）", ""]
        for i, m in enumerate(task.get("must_include") or [], start=1):
            lines.append(f"{i}. {m}：已在输出中显式覆盖（Mock）")
        lines.append("")
        lines.append("（本段为离线占位生成，接入真实模型后将改为真实抽取。）")
        return self._ensure_must_include("\n".join(lines), task)

    def _mock_rewrite(self, task: Dict[str, Any], user_prompt: str) -> str:
        body = [
            "## 改写输出（Mock）",
            "",
            user_prompt[:800] + ("…" if len(user_prompt) > 800 else ""),
            "",
            "### 交付稿",
            "- 面向读者：业务/招聘方可读性优先（Mock）",
            "- 保持事实边界：不编造输入中未给出的数据（Mock）",
        ]
        text = "\n".join(body)
        return self._ensure_must_include(text, task)

    def _mock_textual(self, task: Dict[str, Any], user_prompt: str, *, heading: str) -> str:
        text = f"## {heading}\n\n{user_prompt[:1200]}\n"
        return self._ensure_must_include(text, task)

    def _ensure_must_include(self, text: str, task: Dict[str, Any]) -> str:
        must = [x for x in (task.get("must_include") or []) if x]
        must_not = [x for x in (task.get("must_not_do") or []) if x]
        out = text
        for m in must:
            if m and m not in out:
                out += f"\n{m}\n"
        for fbd in must_not:
            if fbd and fbd in out:
                out = out.replace(fbd, "")
        return out


class OpenAICompatibleGenerator:
    """Real single-turn call via OpenAI-compatible Chat Completions API."""

    def __init__(self, client: OpenAICompatibleClient) -> None:
        self._client = client
        self._last_usage: Dict[str, int] = {}

    @property
    def last_usage(self) -> Dict[str, int]:
        return dict(self._last_usage)

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        task: Dict[str, Any],
    ) -> str:
        _ = task_type, task
        messages = build_messages(system=system_prompt, user=user_prompt)
        result = self._client.chat(messages)
        self._last_usage = {
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.total_tokens,
        }
        return result.content


class DirectAdapter(WorkflowAdapter):
    """Single-turn completion; uses real LLM when `USE_REAL_LLM` + env are set."""

    def __init__(self, generator: Optional[TextGenerator] = None) -> None:
        self._generator_override: Optional[TextGenerator] = generator

    @property
    def candidate_id(self) -> str:
        return "direct-v0.2"

    def run_task(self, task: Dict[str, Any], *, repo_root: Path) -> Dict[str, Any]:
        started = time.perf_counter()
        error_log: List[str] = []
        task_type = str(task.get("task_type", "unknown"))
        settings = load_settings(repo_root)

        user_prompt, file_note = _build_user_prompt(task, repo_root)

        provider = "none"
        model_name = ""
        is_mock = True
        gen: TextGenerator
        if self._generator_override is not None:
            gen = self._generator_override
            is_mock = False
            provider = "override"
            model_name = "custom"
        elif settings.real_llm_ready:
            client = OpenAICompatibleClient(
                base_url=settings.openai_compat_base_url,
                api_key=settings.openai_compat_api_key,
                model=settings.openai_compat_model,
            )
            gen = OpenAICompatibleGenerator(client)
            provider = "openai-compatible"
            model_name = settings.openai_compat_model
            is_mock = False
        else:
            gen = SmartMockTextGenerator()
            provider = "none"
            model_name = "mock"
            is_mock = True

        system_prompt = (
            "You are a careful assistant for office and knowledge-work tasks. "
            "Follow the user instructions, constraints, must_include and must_not_do. "
            "Answer in the language and format the user asked for."
        )
        if is_mock:
            system_prompt += " (Offline mock run — no live model.)"

        raw_output = ""
        status = "success"
        token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        try:
            raw_output = gen.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                task_type=task_type,
                task=task,
            )
            if isinstance(gen, OpenAICompatibleGenerator):
                token_usage = {
                    k: int(v)
                    for k, v in gen.last_usage.items()
                    if k in ("prompt_tokens", "completion_tokens", "total_tokens")
                }
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
            "token_usage": token_usage,
            "estimated_cost": None,
            "provider": provider,
            "model_name": model_name,
            "is_mock": is_mock,
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

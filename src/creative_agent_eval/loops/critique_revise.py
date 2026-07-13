from __future__ import annotations

from dataclasses import dataclass
import json

from ..models import EvalCase
from ..providers import ModelProvider, ProviderRequest
from ..runtime import RunTrace, TraceRecorder


@dataclass(frozen=True)
class CritiqueReviseLoop:
    loop_id: str = "L1"

    def run(self, case: EvalCase, provider: ModelProvider, seed: int = 0) -> RunTrace:
        recorder = TraceRecorder(case.case_id, self.loop_id, provider.provider_id, seed)
        recorder.emit("run_started", {"title": case.title})
        try:
            draft = provider.generate(
                ProviderRequest(case_id=case.case_id, stage="draft", prompt=case.prompt, seed=seed)
            )
            recorder.emit("model_responded", {"stage": "draft", "model": draft.model})
            recorder.emit("candidate_created", {"candidate_index": 0, "content": draft.content})
            critique_prompt = (
                "请根据题目、硬约束和交付要求检查下面的草稿，指出具体问题。\n"
                f"题目：{case.prompt}\n草稿：{json.dumps(draft.content, ensure_ascii=False)}"
            )
            critique = provider.generate(
                ProviderRequest(case_id=case.case_id, stage="critique", prompt=critique_prompt, seed=seed)
            )
            recorder.emit("model_responded", {"stage": "critique", "model": critique.model})
            recorder.emit("critique_created", {"content": critique.content})
            revision_prompt = (
                "请依据批评修订草稿并输出最终结果。\n"
                f"题目：{case.prompt}\n草稿：{json.dumps(draft.content, ensure_ascii=False)}\n"
                f"批评：{json.dumps(critique.content, ensure_ascii=False)}"
            )
            revision = provider.generate(
                ProviderRequest(case_id=case.case_id, stage="revision", prompt=revision_prompt, seed=seed)
            )
            recorder.emit("model_responded", {"stage": "revision", "model": revision.model})
            recorder.emit("revision_created", {"content": revision.content})
            return recorder.complete(revision.content)
        except Exception as exc:
            return recorder.fail(exc)

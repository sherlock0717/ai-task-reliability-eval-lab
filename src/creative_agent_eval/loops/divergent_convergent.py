from __future__ import annotations

from dataclasses import dataclass
import json

from ..models import EvalCase
from ..providers import ModelProvider, ProviderRequest
from ..runtime import RunTrace, TraceRecorder


@dataclass(frozen=True)
class DivergentConvergentLoop:
    candidate_count: int = 3
    loop_id: str = "L2"

    def run(self, case: EvalCase, provider: ModelProvider, seed: int = 0) -> RunTrace:
        if self.candidate_count < 2:
            raise ValueError("candidate_count must be at least 2")
        recorder = TraceRecorder(case.case_id, self.loop_id, provider.provider_id, seed)
        recorder.emit("run_started", {"title": case.title, "candidate_count": self.candidate_count})
        try:
            candidates = []
            for index in range(self.candidate_count):
                response = provider.generate(
                    ProviderRequest(
                        case_id=case.case_id,
                        stage=f"candidate_{index + 1}",
                        prompt=f"{case.prompt}\n请给出一个与已有方案机制不同的候选方案。",
                        seed=seed + index,
                    )
                )
                candidates.append(response.content)
                recorder.emit("model_responded", {"stage": f"candidate_{index + 1}", "model": response.model})
                recorder.emit("candidate_created", {"candidate_index": index, "content": response.content})
            synthesis_prompt = (
                "请比较候选方案的机制差异、适用性和约束满足情况，选择或整合最终结果。\n"
                f"题目：{case.prompt}\n候选：{json.dumps(candidates, ensure_ascii=False)}"
            )
            synthesis = provider.generate(
                ProviderRequest(case_id=case.case_id, stage="synthesis", prompt=synthesis_prompt, seed=seed)
            )
            recorder.emit("model_responded", {"stage": "synthesis", "model": synthesis.model})
            recorder.emit("candidate_selected", {"content": synthesis.content})
            return recorder.complete(synthesis.content)
        except Exception as exc:
            return recorder.fail(exc)

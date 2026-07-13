from __future__ import annotations

from dataclasses import dataclass

from ..models import EvalCase
from ..providers import ModelProvider, ProviderRequest
from ..runtime import RunTrace, TraceRecorder


@dataclass(frozen=True)
class OneShotLoop:
    loop_id: str = "L0"

    def run(self, case: EvalCase, provider: ModelProvider, seed: int = 0) -> RunTrace:
        recorder = TraceRecorder(case.case_id, self.loop_id, provider.provider_id, seed)
        recorder.emit("run_started", {"title": case.title})
        request = ProviderRequest(case_id=case.case_id, stage="final", prompt=case.prompt, seed=seed)
        recorder.emit("model_requested", {"stage": request.stage})
        try:
            response = provider.generate(request)
            recorder.emit(
                "model_responded",
                {"stage": request.stage, "model": response.model, "usage": response.usage},
            )
            return recorder.complete(response.content)
        except Exception as exc:
            return recorder.fail(exc)

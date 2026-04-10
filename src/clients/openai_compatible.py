"""OpenAI-compatible Chat Completions API (sync, stdlib HTTP)."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class ChatResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    raw_response: Dict[str, Any]


class OpenAICompatibleClient:
    """Minimal client for `/v1/chat/completions` on any OpenAI-compatible server."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_s: float = 120.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_s = timeout_s

    def chat(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> ChatResult:
        url = f"{self._base}/v1/chat/completions"
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": list(messages),
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s, context=ctx) as resp:
                raw_text = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Chat API HTTP {exc.code}: {err_body[:2000]}") from exc
        except OSError as exc:
            raise RuntimeError(f"Chat API request failed: {exc}") from exc

        data = json.loads(raw_text)
        choice0 = (data.get("choices") or [{}])[0]
        msg = choice0.get("message") or {}
        content = (msg.get("content") or "").strip()
        usage = data.get("usage") or {}
        pt = int(usage.get("prompt_tokens") or 0)
        ct = int(usage.get("completion_tokens") or 0)
        tt = int(usage.get("total_tokens") or (pt + ct))
        return ChatResult(
            content=content,
            prompt_tokens=pt,
            completion_tokens=ct,
            total_tokens=tt,
            raw_response=data,
        )


def build_messages(*, system: str, user: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

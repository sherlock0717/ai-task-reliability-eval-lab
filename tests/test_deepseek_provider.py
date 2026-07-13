import httpx

from creative_agent_eval.providers.base import ProviderRequest
from creative_agent_eval.providers.deepseek import DeepSeekConfig, DeepSeekProvider


def test_deepseek_provider_builds_safe_request() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("Authorization")
        captured["json"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            json={
                "model": "deepseek-v4-flash",
                "choices": [{"message": {"content": "ok", "tool_calls": []}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 2},
            },
        )

    client = httpx.Client(
        base_url="https://api.deepseek.com",
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer secret"},
    )
    provider = DeepSeekProvider(
        config=DeepSeekConfig(model="deepseek-v4-flash", thinking=True),
        api_key="secret",
        client=client,
    )
    response = provider.generate(
        ProviderRequest(case_id="A01", stage="final", prompt="hello")
    )
    assert response.content == "ok"
    assert response.usage["prompt_tokens"] == 10
    assert captured["authorization"] == "Bearer secret"
    assert "secret" not in captured["json"]
    assert '"thinking":{"type":"enabled"}' in captured["json"]

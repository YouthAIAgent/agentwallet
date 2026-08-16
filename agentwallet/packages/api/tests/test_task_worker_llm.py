"""Tests for TaskWorker LLM rate-limit handling."""


import httpx
import pytest
from agentwallet.workers.task_worker import LLMRateLimitedError, _call_llm


class FakeTransport(httpx.AsyncBaseTransport):
    """Returns a canned response for every request."""

    def __init__(self, status_code: int, json_body: dict | None = None, retry_after: str | None = None):
        self.status_code = status_code
        self.json_body = json_body
        self.retry_after = retry_after

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            self.status_code,
            headers={"Retry-After": self.retry_after} if self.retry_after else {},
            json=self.json_body,
            request=request,
        )


def _patch_transport(monkeypatch, status_code, json_body=None, retry_after=None):
    """Monkeypatch httpx.AsyncClient to use the fake transport."""
    import httpx as _httpx

    class FakeClient(_httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = FakeTransport(status_code, json_body, retry_after)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(_httpx, "AsyncClient", FakeClient)


@pytest.mark.asyncio
async def test_200_returns_openai_compatible(monkeypatch):
    _patch_transport(
        monkeypatch,
        200,
        {"choices": [{"message": {"content": "Real AI answer"}}]},
    )
    provider, model, content = await _call_llm("hello", "general")
    assert provider == "openai-compatible"
    assert content == "Real AI answer"


@pytest.mark.asyncio
async def test_no_key_falls_back_to_demo(monkeypatch):
    monkeypatch.delenv("X402_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("X402_LLM_KEY", raising=False)
    monkeypatch.delenv("OPENAI_COMPAT_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_COMPAT_API_KEY", raising=False)
    provider, model, content = await _call_llm("hello", "general")
    assert provider == "demo"
    assert "demo AI" in content


@pytest.mark.asyncio
async def test_429_after_retries_raises_rate_limited(monkeypatch):
    monkeypatch.setenv("X402_LLM_BASE_URL", "https://llm.test/v1")
    monkeypatch.setenv("X402_LLM_KEY", "test-key")
    monkeypatch.setenv("X402_LLM_MAX_ATTEMPTS", "3")
    # Always 429 → after 3 attempts must raise, never demo
    _patch_transport(monkeypatch, 429, retry_after="1")
    with pytest.raises(LLMRateLimitedError, match="rate-limited after 3 attempts"):
        await _call_llm("hello", "general")


@pytest.mark.asyncio
async def test_retry_then_success(monkeypatch):
    monkeypatch.setenv("X402_LLM_BASE_URL", "https://llm.test/v1")
    monkeypatch.setenv("X402_LLM_KEY", "test-key")
    monkeypatch.setenv("X402_LLM_MAX_ATTEMPTS", "3")

    import httpx as _httpx

    calls = {"n": 0}

    class RetryTransport(_httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: _httpx.Request) -> _httpx.Response:
            calls["n"] += 1
            if calls["n"] < 3:
                return _httpx.Response(429, request=request)
            body = {"choices": [{"message": {"content": "OK after retries"}}]}
            return _httpx.Response(200, json=body, request=request)

    class FakeClient(_httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = RetryTransport()
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(_httpx, "AsyncClient", FakeClient)

    provider, model, content = await _call_llm("hello", "general")
    assert provider == "openai-compatible"
    assert content == "OK after retries"
    assert calls["n"] == 3

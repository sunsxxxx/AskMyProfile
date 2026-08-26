from types import SimpleNamespace
from uuid import uuid4

import httpx
from fastapi import FastAPI

from app.api.routes import router
from app.core.config import Settings
from app.core.rate_limit import RateLimitResult
from app.core.security import ClientIPResolver


class FakeRedis:
    async def ping(self):
        return True


class AllowLimiter:
    async def check(self, _ip):
        return RateLimitResult(True, 0, 1)


class DenyLimiter:
    async def check(self, _ip):
        return RateLimitResult(False, 32, 5)


class FakeChatService:
    async def stream(self, message, thread_id):
        yield "intermediate", "我先查一下资料。"
        yield "token", "我"
        yield "token", "可以回答。"
        yield "sources", [
            {"title": "项目", "source": "projects/p.md", "section": "职责", "category": "project"}
        ]


def make_app(limiter=None, *, max_length=2000):
    app = FastAPI()
    app.include_router(router)
    app.state.settings = Settings(
        _env_file=None,
        llm_api_key="test",
        llm_model="test-model",
        dashscope_api_key="test",
        max_message_length=max_length,
    )
    app.state.redis = FakeRedis()
    app.state.ip_resolver = ClientIPResolver()
    app.state.rate_limiter = limiter or AllowLimiter()
    app.state.chat_service = FakeChatService()
    return app


async def request(app, method, path, **kwargs):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        return await client.request(method, path, **kwargs)


async def test_health():
    response = await request(make_app(), "GET", "/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "redis": "ok"}


async def test_input_validation():
    app = make_app(max_length=4)
    base = {"thread_id": str(uuid4())}
    assert (await request(app, "POST", "/api/chat/stream", json={**base, "message": " "})).status_code == 422
    assert (await request(app, "POST", "/api/chat/stream", json={**base, "message": "12345"})).status_code == 422
    assert (
        await request(app, "POST", "/api/chat/stream", json={"message": "ok", "thread_id": "bad"})
    ).status_code == 422


async def test_rate_limit_response():
    response = await request(
        make_app(DenyLimiter()),
        "POST",
        "/api/chat/stream",
        json={"message": "test", "thread_id": str(uuid4())},
    )
    assert response.status_code == 429
    assert response.headers["retry-after"] == "32"
    assert response.json()["code"] == "RATE_LIMIT_EXCEEDED"


async def test_normal_sse_stream():
    response = await request(
        make_app(),
        "POST",
        "/api/chat/stream",
        json={"message": "介绍项目", "thread_id": str(uuid4())},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'event: status\ndata: {"message":"正在处理问题..."}' in response.text
    assert 'event: intermediate\ndata: {"content":"我先查一下资料。"}' in response.text
    assert "event: token\ndata: {\"content\":\"我\"}" in response.text
    assert "event: sources" in response.text
    assert "event: done" in response.text

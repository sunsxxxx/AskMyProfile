from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.models.chat import ChatRequest


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def sse_event(event: str, data: object | None = None) -> bytes:
    payload = "" if data is None else json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    redis_status = "unavailable"
    try:
        if await request.app.state.redis.ping():
            redis_status = "ok"
    except Exception:
        pass
    status = "ok" if redis_status == "ok" else "degraded"
    return JSONResponse({"status": status, "redis": redis_status}, status_code=200 if status == "ok" else 503)


@router.post("/chat/stream")
async def chat_stream(payload: ChatRequest, request: Request) -> Response:
    settings = request.app.state.settings
    if len(payload.message) > settings.max_message_length:
        raise HTTPException(status_code=422, detail=f"message must be at most {settings.max_message_length} characters")

    client_ip = request.app.state.ip_resolver.resolve(request)
    try:
        rate = await request.app.state.rate_limiter.check(client_ip)
    except Exception as exc:
        logger.exception("rate_limit_unavailable endpoint=/api/chat/stream")
        raise HTTPException(
            status_code=503,
            detail={"code": "RATE_LIMIT_UNAVAILABLE", "message": "服务暂时不可用，请稍后再试"},
        ) from exc
    if not rate.allowed:
        logger.warning("rate_limit_hit endpoint=/api/chat/stream")
        return JSONResponse(
            {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "请求过于频繁，请稍后再试",
                "retry_after": rate.retry_after,
            },
            status_code=429,
            headers={"Retry-After": str(rate.retry_after)},
        )

    missing = settings.missing_chat_settings()
    service = getattr(request.app.state, "chat_service", None)
    if missing or service is None:
        message = (
            f"缺少配置：{', '.join(missing)}"
            if missing
            else "聊天服务尚未就绪，请检查 Redis 连接和向量索引配置"
        )
        raise HTTPException(
            status_code=503,
            detail={"code": "CHAT_NOT_CONFIGURED", "message": message},
        )

    request_id = str(uuid.uuid4())
    started = time.perf_counter()

    async def generate() -> AsyncIterator[bytes]:
        yield sse_event("start", {"request_id": request_id})
        yield sse_event("status", {"message": "正在查找相关资料..."})
        try:
            async for event, data in service.stream(payload.message, str(payload.thread_id)):
                if await request.is_disconnected():
                    break
                if event == "token":
                    yield sse_event("token", {"content": data})
                elif event == "intermediate":
                    yield sse_event("intermediate", {"content": data})
                elif event == "status":
                    yield sse_event("status", {"message": data})
                elif event == "sources":
                    yield sse_event("sources", data)
            yield sse_event("done", {})
        except Exception:
            logger.exception("chat_stream_failed request_id=%s", request_id)
            yield sse_event("error", {"message": "回答生成失败，请稍后重试。"})
        finally:
            logger.info(
                "request_complete request_id=%s endpoint=/api/chat/stream duration_ms=%d",
                request_id,
                int((time.perf_counter() - started) * 1000),
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

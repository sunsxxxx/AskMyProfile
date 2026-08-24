from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from app.agent.graph import build_graph
from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.rate_limit import SlidingWindowRateLimiter
from app.core.redis import create_redis_client
from app.core.security import ClientIPResolver
from app.github.client import GitHubClient
from app.rag.embeddings import create_embeddings
from app.rag.retriever import RetrieverService
from app.rag.vector_store import create_vector_store
from app.services.chat import GraphChatService


logger = logging.getLogger(__name__)


def configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    file_handler = RotatingFileHandler(
        log_dir / "backend.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.set_name("backend-file")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Lifespan can run more than once in tests; replace only our own handler.
    for handler in list(root_logger.handlers):
        if handler.get_name() == "backend-file":
            root_logger.removeHandler(handler)
            handler.close()
    root_logger.addHandler(file_handler)

    # Uvicorn normally installs a console handler. Keep standalone/test runs useful too.
    has_console_handler = any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in root_logger.handlers
    )
    if not has_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging(configured.log_level)
        redis = create_redis_client(configured)
        app.state.settings = configured
        app.state.redis = redis
        app.state.ip_resolver = ClientIPResolver(configured.trusted_proxies)
        app.state.rate_limiter = SlidingWindowRateLimiter(
            redis,
            max_requests=configured.rate_limit_max_requests,
            window_seconds=configured.rate_limit_window_seconds,
            key_ttl_seconds=configured.rate_limit_key_ttl_seconds,
        )
        app.state.chat_service = None
        github: GitHubClient | None = None
        checkpointer_context: Any = None
        try:
            redis_available = False
            try:
                redis_available = bool(await redis.ping())
            except Exception:
                logger.exception("Redis is unavailable during startup")

            missing = configured.missing_chat_settings()
            if missing:
                logger.warning("Chat is not configured; missing: %s", ", ".join(missing))
            elif redis_available:
                try:
                    embeddings = create_embeddings(configured)
                    vector_store = create_vector_store(configured, embeddings)
                    retriever = RetrieverService(vector_store, top_k=configured.retriever_top_k)
                    github = GitHubClient(
                        username=configured.github_username,
                        token=configured.github_token,
                        redis=redis,
                        cache_ttl=configured.github_cache_ttl,
                        timeout=configured.github_timeout_seconds,
                    )
                    checkpointer_context = AsyncRedisSaver.from_conn_string(
                        configured.redis_url,
                        connection_args={
                            "socket_connect_timeout": configured.redis_connect_timeout_seconds,
                            "socket_timeout": configured.redis_connect_timeout_seconds,
                        },
                    )
                    checkpointer = await checkpointer_context.__aenter__()
                    await checkpointer.asetup()
                    graph = build_graph(configured, retriever, github, checkpointer)
                    app.state.chat_service = GraphChatService(graph)
                except Exception:
                    logger.exception("Chat service initialization failed")
            yield
        finally:
            if checkpointer_context is not None:
                await checkpointer_context.__aexit__(None, None, None)
            if github is not None:
                await github.close()
            await redis.aclose()

    app = FastAPI(title="Personal Interview AI Agent", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def request_logging(request: Request, call_next: Any):
        request_id = str(uuid.uuid4())
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed request_id=%s endpoint=%s duration_ms=%d",
                request_id,
                request.url.path,
                int((time.perf_counter() - started) * 1000),
            )
            raise
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_complete request_id=%s endpoint=%s status=%d duration_ms=%d",
            request_id,
            request.url.path,
            response.status_code,
            int((time.perf_counter() - started) * 1000),
        )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[configured.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )
    app.include_router(router)
    return app


app = create_app()

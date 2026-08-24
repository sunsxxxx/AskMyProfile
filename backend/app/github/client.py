from __future__ import annotations

import json
import logging
import time
from typing import Any
from urllib.parse import quote

import httpx
from redis.asyncio import Redis


logger = logging.getLogger(__name__)


class GitHubUnavailableError(RuntimeError):
    pass


class GitHubClient:
    def __init__(
        self,
        *,
        username: str,
        redis: Redis,
        token: str = "",
        cache_ttl: int = 600,
        timeout: float = 10,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.username = username.strip()
        self.redis = redis
        self.cache_ttl = cache_ttl
        self._owns_client = http_client is None
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "personal-interview-ai-agent",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.http = http_client or httpx.AsyncClient(
            base_url="https://api.github.com",
            headers=headers,
            timeout=httpx.Timeout(timeout),
        )

    async def close(self) -> None:
        if self._owns_client:
            await self.http.aclose()

    async def profile(self) -> dict[str, Any]:
        self._ensure_username()
        data = await self._get_json(f"/users/{quote(self.username)}", "profile")
        allowed = ("login", "name", "bio", "html_url", "public_repos", "followers", "following")
        return {key: data.get(key) for key in allowed}

    async def repositories(self) -> list[dict[str, Any]]:
        self._ensure_username()
        rows = await self._get_json(
            f"/users/{quote(self.username)}/repos?sort=updated&per_page=100&type=public",
            "repositories",
        )
        return [self._repository_summary(row) for row in rows if not row.get("private")]

    async def repository(self, name: str, *, include_readme: bool = True) -> dict[str, Any]:
        self._ensure_username()
        safe_name = quote(name, safe="")
        repo = await self._get_json(f"/repos/{quote(self.username)}/{safe_name}", f"repo:{name}")
        languages = await self._get_json(
            f"/repos/{quote(self.username)}/{safe_name}/languages", f"languages:{name}"
        )
        result = self._repository_summary(repo)
        result["languages"] = languages
        if include_readme:
            result["readme"] = await self._readme(name)
        return result

    async def search(self, query: str, repository_name: str | None = None) -> dict[str, Any]:
        try:
            if repository_name:
                return {"profile": await self.profile(), "repository": await self.repository(repository_name)}
            repositories = await self.repositories()
            lowered = query.casefold()
            matched = [
                repo
                for repo in repositories
                if repo["name"].casefold() in lowered
                or (repo.get("description") and str(repo["description"]).casefold() in lowered)
            ]
            if len(matched) == 1:
                detail = await self.repository(str(matched[0]["name"]))
                return {"profile": await self.profile(), "repositories": repositories, "matched": detail}
            return {"profile": await self.profile(), "repositories": repositories}
        except (httpx.HTTPError, ValueError) as exc:
            raise GitHubUnavailableError("暂时无法获取 GitHub 信息。") from exc

    async def _readme(self, name: str) -> str:
        cache_key = self._cache_key(f"readme:{name}")
        cached = await self.redis.get(cache_key)
        if cached is not None:
            return str(cached)
        response = await self.http.get(
            f"/repos/{quote(self.username)}/{quote(name, safe='')}/readme",
            headers={"Accept": "application/vnd.github.raw+json"},
        )
        if response.status_code == 404:
            return ""
        response.raise_for_status()
        text = response.text[:50_000]
        await self.redis.set(cache_key, text, ex=self.cache_ttl)
        return text

    async def _get_json(self, path: str, cache_suffix: str) -> Any:
        cache_key = self._cache_key(cache_suffix)
        cached = await self.redis.get(cache_key)
        if cached is not None:
            return json.loads(str(cached))
        started = time.perf_counter()
        response = await self.http.get(path)
        response.raise_for_status()
        data = response.json()
        await self.redis.set(cache_key, json.dumps(data, ensure_ascii=False), ex=self.cache_ttl)
        logger.info(
            "github_request_complete resource=%s duration_ms=%d",
            cache_suffix.split(":", 1)[0],
            int((time.perf_counter() - started) * 1000),
        )
        return data

    def _cache_key(self, suffix: str) -> str:
        return f"portfolio:github:{self.username.casefold()}:{suffix}"

    def _ensure_username(self) -> None:
        if not self.username:
            raise GitHubUnavailableError("尚未配置 GITHUB_USERNAME。")

    @staticmethod
    def _repository_summary(repo: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": repo.get("name"),
            "description": repo.get("description"),
            "html_url": repo.get("html_url"),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language"),
            "topics": repo.get("topics", []),
            "created_at": repo.get("created_at"),
            "updated_at": repo.get("updated_at"),
        }

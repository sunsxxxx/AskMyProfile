import json

import httpx

from app.github.client import GitHubClient


class MemoryRedis:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.data[key] = value
        return True


async def test_github_profile_repositories_detail_and_cache():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        routes = {
            "/users/candidate": {"login": "candidate", "name": "Candidate", "public_repos": 1},
            "/users/candidate/repos": [
                {
                    "name": "agent-demo",
                    "description": "RAG agent",
                    "html_url": "https://github.com/candidate/agent-demo",
                    "stargazers_count": 2,
                    "forks_count": 1,
                    "language": "Python",
                    "topics": ["rag"],
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-02-01T00:00:00Z",
                    "private": False,
                }
            ],
            "/repos/candidate/agent-demo": {
                "name": "agent-demo",
                "description": "RAG agent",
                "html_url": "https://github.com/candidate/agent-demo",
                "stargazers_count": 2,
                "forks_count": 1,
                "language": "Python",
                "topics": ["rag"],
            },
            "/repos/candidate/agent-demo/languages": {"Python": 1000, "Vue": 500},
        }
        if request.url.path.endswith("/readme"):
            return httpx.Response(200, text="# Agent Demo")
        return httpx.Response(200, json=routes[request.url.path])

    redis = MemoryRedis()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.github.com"
    ) as http:
        client = GitHubClient(username="candidate", redis=redis, http_client=http)
        result = await client.repository("agent-demo")
        again = await client.repository("agent-demo")

    assert result["languages"] == {"Python": 1000, "Vue": 500}
    assert result["readme"] == "# Agent Demo"
    assert again == result
    assert calls.count("/repos/candidate/agent-demo") == 1
    assert any(key.startswith("portfolio:github:candidate") for key in redis.data)


async def test_repository_list_is_sanitized():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "name": "public",
                    "private": False,
                    "description": None,
                    "html_url": "https://example.test/public",
                    "stargazers_count": 0,
                    "forks_count": 0,
                    "language": None,
                    "topics": [],
                },
                {"name": "private", "private": True},
            ],
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.github.com"
    ) as http:
        repos = await GitHubClient(
            username="candidate", redis=MemoryRedis(), http_client=http
        ).repositories()
    assert [repo["name"] for repo in repos] == ["public"]
    assert "private" not in json.dumps(repos)


from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import BaseTool, tool

from app.github.client import GitHubClient, GitHubUnavailableError
from app.rag.retriever import RetrieverService


def _serialize(value: Any) -> str:
    if isinstance(value, list):
        value = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in value]
    return json.dumps(value, ensure_ascii=False)


def build_tools(retriever: RetrieverService, github: GitHubClient) -> list[BaseTool]:
    @tool
    async def search_resume(query: str) -> str:
        """Search verified profile, education, internship, and work-experience records."""
        return _serialize(
            await retriever.search(query, categories=("profile", "education", "experience", "interview"))
        )

    @tool
    async def search_project(query: str, project_name: str | None = None) -> str:
        """Search verified project records. Use project_name only when its stored slug is known."""
        return _serialize(
            await retriever.search(query, categories=("project",), project_name=project_name)
        )

    @tool
    async def search_skill(query: str) -> str:
        """Search verified candidate skill records; this is about personal usage, not encyclopedic facts."""
        return _serialize(await retriever.search(query, categories=("skill",)))

    @tool
    async def search_github(query: str, repository_name: str | None = None) -> str:
        """Fetch current public GitHub profile, repositories, languages, topics, and README on demand."""
        try:
            return _serialize(await github.search(query, repository_name))
        except GitHubUnavailableError as exc:
            return _serialize({"error": str(exc)})

    return [search_resume, search_project, search_skill, search_github]


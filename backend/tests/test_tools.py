import json

from app.agent.tools import build_tools
from app.models.chat import ToolSearchResult


class FakeRetriever:
    def __init__(self):
        self.calls = []

    async def search(self, query, *, categories, project_name=None, top_k=None):
        self.calls.append((query, tuple(categories), project_name))
        return [
            ToolSearchResult(
                content="verified",
                source="projects/example.md",
                category=tuple(categories)[0],
                title="Example",
                section="职责",
            )
        ]


class FakeGitHub:
    async def search(self, query, repository_name=None):
        return {"profile": {"login": "candidate"}, "query": query, "repo": repository_name}


async def test_all_portfolio_tools():
    retriever = FakeRetriever()
    tools = {item.name: item for item in build_tools(retriever, FakeGitHub())}

    resume = json.loads(await tools["search_resume"].ainvoke({"query": "经历"}))
    project = json.loads(
        await tools["search_project"].ainvoke({"query": "Redis", "project_name": "erp"})
    )
    skill = json.loads(await tools["search_skill"].ainvoke({"query": "Redis"}))
    github = json.loads(
        await tools["search_github"].ainvoke({"query": "仓库", "repository_name": None})
    )

    assert resume[0]["category"] == "profile"
    assert project[0]["category"] == "project"
    assert skill[0]["category"] == "skill"
    assert github["profile"]["login"] == "candidate"
    assert retriever.calls[1][2] == "erp"


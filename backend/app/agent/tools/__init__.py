from langchain_core.tools import BaseTool

from app.github.client import GitHubClient
from app.rag.retriever import RetrieverService
from app.agent.tools.memory import load_conversation_memory
from app.agent.tools.portfolio import build_tools as build_portfolio_tools


def build_tools(retriever: RetrieverService, github: GitHubClient) -> list[BaseTool]:
    return [*build_portfolio_tools(retriever, github), load_conversation_memory]

__all__ = ["build_tools"]

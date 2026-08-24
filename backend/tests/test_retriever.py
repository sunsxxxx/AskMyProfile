from langchain_core.documents import Document

from app.rag.retriever import RetrieverService


class FakeVectorStore:
    def __init__(self):
        self.calls = []

    def similarity_search_with_score(self, query, *, k, filter=None):
        self.calls.append({"query": query, "k": k, "filter": filter})
        return [
            (
                Document(
                    page_content="我在项目中使用 Redis。",
                    metadata={
                        "source": "skills/redis.md",
                        "category": "skill",
                        "title": "Redis",
                        "section": "实际使用",
                        "path": "skills/redis.md",
                        "project": "",
                    },
                ),
                0.12,
            )
        ]


async def test_retriever_returns_structured_results_and_filter():
    store = FakeVectorStore()
    service = RetrieverService(store, top_k=4)
    results = await service.search("Redis 经验", categories=("skill",))
    assert results[0].source == "skills/redis.md"
    assert results[0].score == 0.12
    assert store.calls[0]["k"] == 4
    assert store.calls[0]["filter"] is not None


async def test_project_filter_is_added():
    store = FakeVectorStore()
    service = RetrieverService(store)
    await service.search("为什么用 Redis", categories=("project",), project_name="tourism-erp")
    assert store.calls[0]["filter"] is not None


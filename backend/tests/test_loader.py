from pathlib import Path

from app.rag.loader import MarkdownKnowledgeLoader


def test_markdown_header_split_and_metadata(tmp_path: Path):
    project_dir = tmp_path / "projects"
    project_dir.mkdir()
    source = project_dir / "tourism-erp.md"
    source.write_text(
        "# 旅游 ERP\n\n## 项目背景\n真实背景。\n\n## Redis\n用于真实缓存场景。",
        encoding="utf-8",
    )

    documents = MarkdownKnowledgeLoader(tmp_path, chunk_size=80, chunk_overlap=10).load()

    assert len(documents) >= 2
    redis_chunk = next(item for item in documents if item.metadata["section"] == "Redis")
    assert redis_chunk.metadata == {
        "source": "projects/tourism-erp.md",
        "path": "projects/tourism-erp.md",
        "category": "project",
        "title": "旅游 ERP",
        "project": "tourism-erp",
        "section": "Redis",
    }
    assert "D:" not in redis_chunk.metadata["source"]


def test_readme_is_not_indexed(tmp_path: Path):
    (tmp_path / "README.md").write_text("# Instructions", encoding="utf-8")
    assert MarkdownKnowledgeLoader(tmp_path).scan() == []


from __future__ import annotations

import logging
import sys

from app.core.config import get_settings
from app.rag.embeddings import create_embeddings
from app.rag.loader import MarkdownKnowledgeLoader
from app.rag.vector_store import create_vector_store, drop_application_index


logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    if not settings.dashscope_api_key:
        logger.error("索引失败：缺少 DASHSCOPE_API_KEY")
        return 2
    loader = MarkdownKnowledgeLoader(settings.knowledge_dir)
    files = loader.scan()
    logger.info("读取 Markdown 文件：%d", len(files))
    documents = loader.load()
    logger.info("生成 chunks：%d", len(documents))
    if not documents:
        logger.error("索引失败：knowledge/ 中没有可索引的 Markdown 内容")
        return 2
    try:
        removed = drop_application_index(settings)
        logger.info("旧应用索引：%s", "已删除" if removed else "不存在")
        embeddings = create_embeddings(settings)
        vector_store = create_vector_store(settings, embeddings)
        ids = vector_store.add_documents(documents)
        logger.info("Embedding 成功，写入 vectors：%d", len(ids))
        return 0
    except Exception as exc:
        logger.exception("重新索引失败：%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

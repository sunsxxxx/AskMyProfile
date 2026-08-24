from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


CATEGORY_BY_DIRECTORY = {
    "profile": "profile",
    "education": "education",
    "experience": "experience",
    "projects": "project",
    "skills": "skill",
    "interview": "interview",
    "examples": "example",
}


class MarkdownKnowledgeLoader:
    def __init__(self, knowledge_dir: Path, *, chunk_size: int = 1000, chunk_overlap: int = 120) -> None:
        self.knowledge_dir = knowledge_dir.resolve()
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
            strip_headers=False,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "；", ". ", " ", ""],
        )

    def scan(self) -> list[Path]:
        return sorted(
            path for path in self.knowledge_dir.rglob("*.md") if path.name.lower() != "readme.md"
        )

    def load(self) -> list[Document]:
        documents: list[Document] = []
        for path in self.scan():
            documents.extend(self.load_file(path))
        return documents

    def load_file(self, path: Path) -> list[Document]:
        resolved = path.resolve()
        if self.knowledge_dir not in resolved.parents:
            raise ValueError("Knowledge file must stay inside knowledge directory")
        text = resolved.read_text(encoding="utf-8")
        relative = PurePosixPath(resolved.relative_to(self.knowledge_dir).as_posix())
        category = CATEGORY_BY_DIRECTORY.get(relative.parts[0], relative.parts[0])
        title = self._first_title(text) or resolved.stem.replace("-", " ").title()
        project = resolved.stem if category == "project" else ""
        base = {
            "source": relative.as_posix(),
            "path": relative.as_posix(),
            "category": category,
            "title": title,
            "project": project,
        }

        header_docs = self.header_splitter.split_text(text)
        output: list[Document] = []
        for header_doc in header_docs:
            metadata = {**base, **header_doc.metadata}
            metadata["section"] = metadata.get("h3") or metadata.get("h2") or metadata.get("h1") or title
            metadata.pop("h1", None)
            metadata.pop("h2", None)
            metadata.pop("h3", None)
            for chunk in self.text_splitter.split_documents(
                [Document(page_content=header_doc.page_content, metadata=metadata)]
            ):
                if chunk.page_content.strip():
                    output.append(chunk)
        return output

    @staticmethod
    def _first_title(text: str) -> str:
        match = re.search(r"^#\s+(.+?)\s*$", text, flags=re.MULTILINE)
        return match.group(1).strip() if match else ""


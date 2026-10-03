"""Split parsed pages into chunks with source/page metadata and stable IDs."""

from dataclasses import dataclass

from app.rag.parser import Page


@dataclass
class Chunk:
    chunk_id: str
    source: str
    page: int | None
    text: str


def _split(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        piece = words[start:start + chunk_size]
        chunks.append(" ".join(piece))
        if start + chunk_size >= len(words):
            break
    return chunks


def chunk_pages(pages: list[Page], chunk_size: int = 200, overlap: int = 40) -> list[Chunk]:
    chunks = []
    for page in pages:
        for i, text in enumerate(_split(page.text, chunk_size, overlap)):
            page_part = page.page if page.page is not None else 0
            chunk_id = f"{page.source}:{page_part}:{i}"
            chunks.append(Chunk(chunk_id=chunk_id, source=page.source, page=page.page, text=text))
    return chunks

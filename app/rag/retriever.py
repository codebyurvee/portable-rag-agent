"""Tie embeddings + Qdrant together: ingest documents and retrieve chunks."""

from pathlib import Path

from app.rag.parser import parse_file
from app.rag.chunker import chunk_pages, Chunk
from app.rag.embeddings import Embedder
from app.rag.vector_store import VectorStore


class Retriever:
    def __init__(self, embedder: Embedder | None = None, store: VectorStore | None = None):
        self.embedder = embedder or Embedder()
        self.store = store or VectorStore(dim=self.embedder.dim)

    def ingest_chunks(self, chunks: list[Chunk]):
        if not chunks:
            return
        vectors = self.embedder.embed([c.text for c in chunks])
        self.store.add(chunks, vectors)

    def ingest_file(self, path: str | Path):
        chunks = chunk_pages(parse_file(path))
        self.ingest_chunks(chunks)
        return len(chunks)

    def ingest_dir(self, directory: str | Path):
        directory = Path(directory)
        total = 0
        for path in sorted(directory.iterdir()):
            if path.suffix.lower() in (".pdf", ".txt", ".md"):
                total += self.ingest_file(path)
        return total

    def retrieve(self, query: str, top_k: int = 4) -> list[dict]:
        vector = self.embedder.embed_one(query)
        return self.store.search(vector, top_k=top_k)

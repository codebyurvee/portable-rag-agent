"""Qdrant vector store: upsert chunk vectors with metadata and search."""

import os
import uuid

from qdrant_client import QdrantClient, models

from app.rag.chunker import Chunk


COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")


def _client_from_env() -> QdrantClient:
    url = os.getenv("QDRANT_URL")
    if url:
        return QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY") or None)
    return QdrantClient(":memory:")


class VectorStore:
    def __init__(self, dim: int, client: QdrantClient | None = None, collection: str = COLLECTION):
        self.client = client or _client_from_env()
        self.collection = collection
        self.dim = dim
        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(size=self.dim, distance=models.Distance.COSINE),
            )

    def add(self, chunks: list[Chunk], vectors: list[list[float]]):
        points = []
        for chunk, vector in zip(chunks, vectors):
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "source": chunk.source,
                        "page": chunk.page,
                        "text": chunk.text,
                    },
                )
            )
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, vector: list[float], top_k: int = 4) -> list[dict]:
        hits = self.client.query_points(
            collection_name=self.collection, query=vector, limit=top_k, with_payload=True
        ).points
        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                {
                    "score": hit.score,
                    "chunk_id": payload.get("chunk_id"),
                    "source": payload.get("source"),
                    "page": payload.get("page"),
                    "text": payload.get("text"),
                }
            )
        return results

"""Text embeddings using fastembed (local ONNX model, no API keys)."""

import os


DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
# Deterministic cache path: set to /app/.fastembed_cache in Docker so the model
# baked at build time is found at runtime without a re-download.
FASTEMBED_CACHE_PATH = os.getenv("FASTEMBED_CACHE_PATH")


class Embedder:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        from fastembed import TextEmbedding

        self.model_name = model_name
        kwargs = {"cache_dir": FASTEMBED_CACHE_PATH} if FASTEMBED_CACHE_PATH else {}
        self._model = TextEmbedding(model_name, **kwargs)
        self.dim = len(next(self._model.embed(["dimension probe"])).tolist())

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.embed(texts)]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

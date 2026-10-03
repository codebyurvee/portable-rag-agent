import hashlib
from pathlib import Path

import pytest

from app.rag.parser import parse_file, Page
from app.rag.chunker import chunk_pages
from app.rag.vector_store import VectorStore

FIXTURE = Path(__file__).parent / "fixtures" / "sample.pdf"


class FakeEmbedder:
    """Deterministic bag-of-words embedder so Qdrant tests run offline."""

    VOCAB = ["deadline", "october", "qdrant", "vectors", "project", "document"]
    dim = len(VOCAB)

    def embed(self, texts):
        out = []
        for t in texts:
            low = t.lower()
            out.append([float(low.count(w)) + 0.01 for w in self.VOCAB])
        return out

    def embed_one(self, text):
        return self.embed([text])[0]


def test_parse_pdf_preserves_pages():
    pages = parse_file(FIXTURE)
    assert len(pages) == 2
    assert pages[0].page == 1
    assert pages[1].page == 2
    assert pages[0].source == "sample.pdf"
    assert "deadline" in pages[0].text.lower()


def test_parse_rejects_unsupported_type(tmp_path):
    bad = tmp_path / "image.png"
    bad.write_bytes(b"\x89PNG")
    with pytest.raises(ValueError):
        parse_file(bad)


def test_chunker_preserves_metadata_and_ids():
    pages = [Page(source="doc.pdf", page=1, text="alpha beta gamma delta epsilon")]
    chunks = chunk_pages(pages, chunk_size=2, overlap=0)
    assert len(chunks) == 3
    assert chunks[0].source == "doc.pdf"
    assert chunks[0].page == 1
    assert chunks[0].chunk_id == "doc.pdf:1:0"
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))  # stable and unique


def test_chunker_handles_missing_page():
    pages = [Page(source="notes.txt", page=None, text="one two three four")]
    chunks = chunk_pages(pages, chunk_size=2, overlap=0)
    assert chunks[0].page is None
    assert chunks[0].chunk_id.startswith("notes.txt:0:")


def test_vector_store_search_returns_traceable_evidence():
    embedder = FakeEmbedder()
    store = VectorStore(dim=embedder.dim, collection="test_docs")
    pages = parse_file(FIXTURE)
    chunks = chunk_pages(pages, chunk_size=50, overlap=10)
    store.add(chunks, embedder.embed([c.text for c in chunks]))

    results = store.search(embedder.embed_one("when is the deadline"), top_k=2)
    assert results
    top = results[0]
    assert "deadline" in top["text"].lower()
    # evidence must trace back to the real document
    assert top["source"] == "sample.pdf"
    assert top["page"] == 1
    assert top["chunk_id"]
    assert top["text"]


def test_embedder_output_shape():
    pytest.importorskip("fastembed")
    try:
        from app.rag.embeddings import Embedder
        embedder = Embedder()
    except Exception as e:
        pytest.skip(f"fastembed model unavailable (needs download/network): {e}")
    vecs = embedder.embed(["hello world", "second text"])
    assert len(vecs) == 2
    assert len(vecs[0]) == embedder.dim
    assert all(isinstance(x, float) for x in vecs[0])

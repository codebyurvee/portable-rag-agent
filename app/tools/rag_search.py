"""RAG search tool: wraps the Retriever and returns traceable evidence."""

from app.agent.schemas import Evidence
from app.rag.retriever import Retriever


class RagSearchTool:
    name = "rag_search"

    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    def run(self, query: str, top_k: int = 4) -> dict:
        hits = self.retriever.retrieve(query, top_k=top_k)
        evidence = [
            Evidence(
                source=h["source"],
                text=h["text"],
                page=h["page"],
                chunk_id=h["chunk_id"],
            )
            for h in hits
            if h.get("source") and h.get("text")
        ]
        status = "success" if evidence else "no_answer"
        return {"evidence": evidence, "status": status}

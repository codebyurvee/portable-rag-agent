# Agent Passport — Product Requirements Document

## Project
**Portable RAG Research Agent — Agent Passport**

We are building a modular AI research agent that answers questions from a controlled document collection using RAG. The key challenge is portability: the same external behavior, tools, input/output contract, evidence format, and verification tests must work across two implementations:

- LangGraph
- LlamaIndex

Planned model: Qwen3-8B through a compatible API provider such as Hugging Face or OpenRouter. Provider configuration must be environment-based.

## Core Flow
User Query → Agent → Decide Action → Tool → Retrieve/Process → Generate Answer → Evidence → Verification

## MVP Scope
- PDF/document ingestion and parsing
- Chunking with source/page metadata
- Embeddings
- Qdrant vector storage and retrieval
- RAG Search tool
- Web Search tool where practical
- Calculator tool
- Qwen3-8B
- Agentic tool selection
- Answer + evidence
- LangGraph implementation
- LlamaIndex implementation
- Shared Agent Contract
- Same verification tests for both implementations
- Simple Streamlit UI
- FastAPI backend if required/time permits
- Minimal SQLite if required
- Docker if time permits
- Agent Passport documentation

## Principles
- Keep framework-specific code isolated.
- Keep tool interfaces framework-independent.
- Keep the external request/response contract identical.
- Prefer a simple working implementation over unnecessary complexity.
- Evidence must be traceable to a real source/page when available.
- Never invent evidence.
- If documents do not contain the answer, say so.
- Never expose secrets.
- Use environment variables for credentials/configuration.
- Keep the system reproducible and testable.

## Target Architecture
```text
User → Streamlit → FastAPI → Agent Contract
                              ├─ LangGraph
                              └─ LlamaIndex
                                      ↓
                         RAG / Web Search / Calculator
                                      ↓
                                   Qdrant
                                      ↓
                                  Documents
                                      ↓
                              Answer + Evidence
```

## Stack
Python 3.11, Qwen3-8B, LangGraph, LlamaIndex, Qdrant, Streamlit, FastAPI, SQLite (minimal if needed), Pytest, Docker, Git/GitHub, `.env`.

## Repository
```text
portable-rag-agent/
├── app/
│   ├── agent/
│   ├── rag/
│   ├── tools/
│   └── frameworks/
│       ├── langgraph/
│       └── llamaindex/
├── api/
├── ui/
├── database/
├── documents/
├── tests/
│   ├── contract/
│   ├── rag/
│   ├── tools/
│   ├── frameworks/
│   └── integration/
├── docs/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── Dockerfile
```

## Agent Contract
The portability boundary must be framework-independent.

Expected concepts:
- `AgentRequest`
- `AgentResponse`
- `Evidence`
- `ToolCall`
- `AgentStatus`

Conceptual response:
```json
{
  "answer": "The project deadline is October 3, 2026.",
  "evidence": [{"source": "challenge_rules.pdf", "page": 4, "text": "..."}],
  "tools_used": ["rag_search"],
  "status": "success"
}
```

Exact schemas are finalized during implementation. Do not create incompatible framework-specific response formats.

## RAG
Preserve filename/source, page number when available, chunk ID and text. Retrieval must return context plus metadata sufficient for evidence generation. Qdrant is the vector database. LlamaIndex may assist with document/indexing utilities, but the external RAG tool interface stays framework-independent.

## Tools
**RAG Search:** query → relevant context + evidence metadata + status.

**Web Search:** use when external/current information is required and the project allows it.

**Calculator:** perform arithmetic reliably instead of relying on LLM arithmetic.

## Agent Behavior
1. Receive query.
2. Decide whether document retrieval, web search, calculator, or direct response is appropriate.
3. Call the selected tool.
4. Process result.
5. Generate concise answer.
6. Include evidence when relying on retrieved information.
7. Avoid unsupported claims.
8. Return standardized response.
9. Handle failures safely.

## Portability
Both implementations must use the same input schema, output schema, tool contracts, representative questions, behavior rules and evidence requirements. Do not require identical generated wording; require contract and behavioral compliance.

## Verification
Test categories:
- Contract
- RAG retrieval
- Tools
- Error handling
- LangGraph
- LlamaIndex
- Portability
- End-to-end integration

Example required behavior for a document question:
- use document retrieval
- retrieve relevant content
- answer from retrieved content
- provide source/page evidence
- satisfy `AgentResponse`

## UI
Simple UI showing question, answer, evidence/source, tools used, status/errors, and optionally selected framework. Avoid spending time on visual polish.

## Non-goals for the rapid MVP
Authentication, complex user management, sophisticated memory, elaborate frontend, microservices, production observability, and complex deployment.

## Definition of Done
Documents ingest; Qdrant retrieval works; tools work; Qwen works; both frameworks work; both satisfy the same contract; evidence is returned; verification passes; UI demonstrates the system; no secrets are committed; setup is reproducible.

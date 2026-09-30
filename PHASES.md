# Agent Passport — Development Phases

## Kiro Working Rules
Kiro must work in small, controlled increments.

For every task:
1. Inspect the current repository.
2. Read `PRD.md`, `PHASES.md`, and `SECURITY.md`.
3. Implement only the requested task.
4. Do not rewrite unrelated files.
5. Run relevant tests.
6. Report files changed, commands run, results and known issues.
7. Stop and wait for the next instruction.

The human project lead decides when to move forward.

## Phase 0 — Existing Setup
Completed:
- GitHub repository
- Python environment
- base folder structure

Do not recreate or unnecessarily restructure it.

## Phase 1 — Agent Contract
Owner: Project Lead + Kiro.

Create:
```text
app/agent/
├── contract.py
├── schemas.py
└── passport.py
```
Define AgentRequest, AgentResponse, Evidence, ToolCall, AgentStatus and Agent Passport metadata. No framework dependencies. Add basic tests. Then Person 3 verifies.

## Phase 2 — Test Foundation
Owner: Person 3.

Prepare:
```text
tests/contract/
tests/rag/
tests/tools/
tests/frameworks/
tests/integration/
```
Create reusable contract tests. Pytest must run.

## Phase 3 — Document Preparation
Owner: Project Lead.

Prepare the agreed document collection, verify readability/extraction, preserve source/page information and prepare representative questions.

## Phase 4 — RAG
Owner: Project Lead.

Build:
```text
documents → parser → chunker → metadata → embeddings → Qdrant → retriever
```
LlamaIndex may be used for document/indexing utilities. The external RAG tool interface stays independent.

Person 3 verifies ingestion, retrieval and metadata.

## Phase 5 — Tools
Owner: Project Lead.

Implement RAG Search, Calculator and Web Search if practical. Stable input/output interfaces. Person 3 tests.

## Phase 6 — Qwen3-8B
Owner: Project Lead.

Connect through selected provider. Use environment variables for key, base URL and model. Create a minimal model adapter. Person 3 verifies.

## Phase 7 — Agent Core
Owner: Project Lead.

Implement:
```text
query → decide → tool → process → answer → evidence → AgentResponse
```
Person 3 verifies representative cases.

## Phase 8 — LangGraph
Owner: Project Lead.

Implement under `app/frameworks/langgraph/`. It must expose the same external contract. Person 3 runs common contract and integration tests.

## Phase 9 — LlamaIndex
Owner: Project Lead.

Implement under `app/frameworks/llamaindex/`. It must expose the same external contract. Person 3 runs the same tests.

## Phase 10 — Portability
Owner: Person 3.

Run identical representative inputs against both implementations. Check schema compliance, required behavior, evidence, tool reporting and errors. Do not require identical wording.

Failure loop:
Person 3 reports → Project Lead fixes → Person 3 retests → continue after pass.

## Phase 11 — FastAPI
Owner: Project Lead.

Build minimal health and query endpoints using the common schemas. Person 3 tests.

## Phase 12 — Streamlit
Owner: Project Lead.

Build simple question input, answer, evidence, tools/status and API error display. Person 3 smoke-tests.

## Phase 13 — SQLite
Owner: Project Lead.

Only implement what the demo/challenge requires. Store minimal sessions/query/run metadata. Do not duplicate Qdrant vectors.

## Phase 14 — Full Integration
Owner: Project Lead.

Run:
```text
Streamlit → FastAPI → Agent → Framework → Tools → Qdrant/external services → Qwen → AgentResponse
```
Test document, calculator, web and error cases. Person 3 verifies.

## Phase 15 — Docker
Owner: Project Lead.

Create reproducible startup without secrets in images. Person 3 runs a clean smoke test.

## Phase 16 — Final Verification
Owner: Person 3.

Run contract, RAG, tool, framework, portability, API and integration tests. Record results.

## Phase 17 — Documentation & Demo
Owner: Project Lead.

Finalize README, Agent Passport, architecture, setup, tools, portability/migration explanation and demo script.

## Phase 18 — Submission
All members review source, tests, docs, demo, environment configuration and secret safety.

## Rapid Hackathon Priority
If time is extremely limited:
1. Contract
2. Document RAG + Qdrant
3. Qwen
4. RAG tool
5. LangGraph
6. LlamaIndex portability
7. Verification
8. Streamlit
9. FastAPI
10. SQLite
11. Docker
12. Extra polish

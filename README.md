# Portable RAG Research Agent — Agent Passport

A RAG research agent that answers questions from a document collection and returns
answers with traceable evidence. The same agent contract runs through three
interchangeable orchestrators — **Core**, **LangGraph**, and **LlamaIndex** — all
sharing the same tools (RAG search, calculator, web search), the same Qdrant + FastEmbed
retrieval pipeline, and the same Qwen3-8B model adapter.

```
Streamlit → FastAPI → Agent (core | langgraph | llamaindex)
                        → RAG / Calculator / Web → Qwen3-8B → AgentResponse
```

## Configuration

Copy `.env.example` to `.env` and fill in your values. Never commit `.env`.

```
QWEN_API_KEY=...
QWEN_BASE_URL=https://router.huggingface.co/v1
QWEN_MODEL=Qwen/Qwen3-8B
QDRANT_URL=                # empty = local in-memory Qdrant (dev only — not persistent)
QDRANT_API_KEY=
DOCUMENTS_DIR=documents
WEB_SEARCH_API_KEY=        # optional; web search is disabled if unset
FASTEMBED_CACHE_PATH=      # leave empty locally; set to /app/.fastembed_cache in Docker
```

Put the documents to index at startup in `documents/` (PDF, TXT, or MD).

## Run locally (Python 3.11)

```bash
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000       # API  (terminal 1)
API_BASE_URL=http://localhost:8000 streamlit run ui/app.py   # UI (terminal 2)
```

Health check: `GET http://localhost:8000/health` → `{"status": "ok"}`.

## Run with Docker

The image uses Python 3.11. The fastembed embedding model is baked in at build time
so there is no cold-start download. Secrets are supplied at runtime — never baked in.

```bash
docker build -t portable-rag-agent .
docker run --rm -p 8000:8000 --env-file .env portable-rag-agent
```

Both services together with Docker Compose:

```bash
docker compose up --build
```

- API: http://localhost:8000
- UI:  http://localhost:8501

## Deploy to Render

A `render.yaml` is included for two-service Render deployment.

**Required steps:**

1. Create the API service first (`portable-rag-api`) and note its public URL.
2. Set these environment variables on the API service in the Render dashboard:
   - `QWEN_API_KEY` — your Hugging Face / OpenRouter key
   - `QWEN_BASE_URL` — `https://router.huggingface.co/v1`
   - `QWEN_MODEL` — `Qwen/Qwen3-8B`
   - `QDRANT_URL` — your Qdrant Cloud cluster URL (see below)
   - `QDRANT_API_KEY` — your Qdrant Cloud API key
   - `WEB_SEARCH_API_KEY` — optional Tavily key
3. On the UI service (`portable-rag-ui`), set:
   - `API_BASE_URL=https://<your-api-service>.onrender.com`

**Qdrant Cloud (required for persistent RAG on Render):**
The default in-memory Qdrant works locally but loses all indexed vectors on every
Render restart. For production, create a free cluster at https://cloud.qdrant.io and
set `QDRANT_URL` + `QDRANT_API_KEY`.

**Ephemeral storage note:**
Without a Render persistent disk, uploaded documents and SQLite query history are lost
on each restart. Add a persistent disk and update `UPLOAD_DIR` / `DATABASE_PATH` to
point to the mounted path to make them durable.

## Endpoints

- `GET /health` → `{"status": "ok"}`
- `POST /query` → `{"query": "...", "framework": "core|langgraph|llamaindex"}`
  Returns `AgentResponse` (answer, status, evidence, tool_calls, tools_used).
- `POST /documents/upload` → multipart upload of a PDF, TXT, or MD file.
  Indexes the document into Qdrant and returns `{filename, status, chunks_indexed}`.
- `GET /documents` → `{"documents": [...]}` — lists uploaded filenames.

## Streamlit UI

The UI has two sections:

**Sidebar — Knowledge Base:** Upload PDF, TXT, or MD files via the file uploader.
Click "Upload & Index" to ingest the document into Qdrant. Uploaded filenames are
listed once indexed.

**Main — Query:** Select a framework (Core / LangGraph / LlamaIndex), type a question,
and click Ask. The answer, status, tools used, tool calls, and evidence (with
source / page / chunk ID / text) are displayed. The framework selector makes
portability visible — the same question returns the same contract shape across all three.

## Persistence

Each `/query` run is recorded in a local SQLite database (query text, framework,
status, answer, tools used, timestamp) using Python's standard-library `sqlite3`.

- Default location: `database/agent.db`
- Override with `DATABASE_PATH` (e.g. `DATABASE_PATH=/data/agent.db`)
- No secrets are stored. Database files are gitignored.

## Tests

```bash
python -m pytest -q
```

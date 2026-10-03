"""Minimal FastAPI backend exposing the portable agent behind the Agent Contract."""

import logging
import os
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from app.agent.schemas import AgentRequest
from app.agent.model import QwenModel
from app.agent.core import AgentCore
from app.frameworks.langgraph.agent import LangGraphAgent
from app.frameworks.llamaindex.agent import LlamaIndexAgent
from database import db

logger = logging.getLogger("api")

FRAMEWORKS = ("core", "langgraph", "llamaindex")
DEFAULT_FRAMEWORK = "core"

ALLOWED_EXTENSIONS = (".pdf", ".txt", ".md")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))  # 10 MB


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    framework: str | None = None


def sanitize_filename(name: str) -> str:
    """Keep only the base name and a safe character set; drop any path components."""
    base = os.path.basename(name or "").replace("\\", "/").split("/")[-1]
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base).lstrip(".")
    return base


def build_agents():
    """Build one agent per framework, sharing a single retriever and model."""
    from dotenv import load_dotenv
    from app.rag.retriever import Retriever

    load_dotenv()
    retriever = Retriever()
    docs_dir = os.getenv("DOCUMENTS_DIR", "documents")
    if os.path.isdir(docs_dir):
        try:
            retriever.ingest_dir(docs_dir)
        except Exception:
            pass  # empty/unreadable dir is fine; retrieval just returns no evidence
    model = QwenModel()
    agents = {
        "core": AgentCore(retriever=retriever, model=model),
        "langgraph": LangGraphAgent(retriever=retriever, model=model),
        "llamaindex": LlamaIndexAgent(retriever=retriever, model=model),
    }
    return agents, retriever


def create_app(agents=None, db_path=None, retriever=None, upload_dir=None) -> FastAPI:
    app = FastAPI(title="Portable RAG Research Agent")
    app.state.agents = agents  # lazily built on first use if None
    app.state.retriever = retriever  # shared with the agents
    app.state.db_path = db_path
    app.state.upload_dir = upload_dir or os.getenv("UPLOAD_DIR", "documents/uploads")
    db.init_db(db_path)

    def get_agents():
        if app.state.agents is None:
            app.state.agents, app.state.retriever = build_agents()
        return app.state.agents

    def get_retriever():
        get_agents()  # ensures retriever is built if agents were lazy
        return app.state.retriever

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/query")
    def query(req: QueryRequest):
        framework = (req.framework or DEFAULT_FRAMEWORK).lower()
        if framework not in FRAMEWORKS:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported framework '{framework}'; choose one of {list(FRAMEWORKS)}",
            )
        query_text = req.query.strip()
        if not query_text:
            raise HTTPException(status_code=400, detail="query must not be empty")

        agent = get_agents()[framework]
        try:
            response = agent.run(AgentRequest(query=query_text, framework=framework))
        except Exception:
            # never surface stack traces / secrets
            raise HTTPException(status_code=500, detail="agent execution failed")
        result = response.to_dict()
        result["framework"] = framework

        try:
            db.record_run(
                query=query_text,
                framework=framework,
                status=result["status"],
                answer=result["answer"],
                tools_used=result["tools_used"],
                path=app.state.db_path,
            )
        except Exception:
            logger.warning("failed to persist query run")

        return result

    @app.post("/documents/upload")
    async def upload_document(file: UploadFile = File(...)):
        filename = sanitize_filename(file.filename or "")
        ext = os.path.splitext(filename)[1].lower()
        if not filename or ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported file type; allowed: {list(ALLOWED_EXTENSIONS)}",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="uploaded file is empty")
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"file too large; max {MAX_UPLOAD_BYTES} bytes",
            )

        upload_dir = Path(app.state.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / filename
        dest.write_bytes(content)  # stored as data; never executed

        try:
            chunks = get_retriever().ingest_file(dest)
        except Exception:
            raise HTTPException(status_code=400, detail="could not index document")

        return {
            "filename": filename,
            "status": "success",
            "chunks_indexed": chunks,
            "message": f"indexed {chunks} chunk(s) from {filename}",
        }

    @app.get("/documents")
    def list_documents():
        upload_dir = Path(app.state.upload_dir)
        if not upload_dir.is_dir():
            return {"documents": []}
        names = sorted(
            p.name for p in upload_dir.iterdir()
            if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
        )
        return {"documents": names}

    return app


app = create_app()

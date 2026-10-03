# ── Portable RAG Agent — FastAPI container (Python 3.11) ──
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FASTEMBED_CACHE_PATH=/app/.fastembed_cache

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source (.env and other local files are excluded via .dockerignore)
COPY api ./api
COPY app ./app
COPY ui ./ui
COPY database ./database
COPY documents ./documents

# Pre-bake the fastembed embedding model into the image so cold starts
# do not require a network download.  FASTEMBED_CACHE_PATH is already set above.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

EXPOSE 8000

# Secrets are provided at runtime via environment variables, never baked in.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

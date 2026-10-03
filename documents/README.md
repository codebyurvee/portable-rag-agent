# Documents

Place the source documents for the RAG collection here.

Supported formats: `.pdf` (page numbers preserved), `.txt`, `.md`.

Ingest them with the retriever:

```python
from app.rag.retriever import Retriever

r = Retriever()
r.ingest_dir("documents")
print(r.retrieve("your question"))
```

No documents are committed to the repo. Add the agreed MVP documents here before running ingestion.

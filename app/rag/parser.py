"""Extract text from documents, preserving page numbers for PDFs."""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class Page:
    source: str
    page: int | None
    text: str


def parse_pdf(path: str | Path) -> list[Page]:
    path = Path(path)
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(Page(source=path.name, page=i, text=text))
    return pages


def parse_text(path: str | Path) -> list[Page]:
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    return [Page(source=path.name, page=None, text=text)] if text else []


def parse_file(path: str | Path) -> list[Page]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)
    if suffix in (".txt", ".md"):
        return parse_text(path)
    raise ValueError(f"Unsupported file type: {suffix}")

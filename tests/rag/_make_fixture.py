"""One-off helper to generate a tiny 2-page PDF fixture for parser tests."""

from pathlib import Path


def _pdf_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(path: Path, pages_text: list[str]):
    objects = []

    # 1: catalog, 2: pages tree
    kids_ids = [3 + 2 * i for i in range(len(pages_text))]
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    kids = " ".join(f"{i} 0 R" for i in kids_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages_text)} >>")

    for i, text in enumerate(pages_text):
        page_id = 3 + 2 * i
        content_id = page_id + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        stream = f"BT /F1 24 Tf 72 700 Td ({_pdf_escape(text)}) Tj ET"
        objects.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")

    out = "%PDF-1.4\n"
    offsets = []
    for n, body in enumerate(objects, start=1):
        offsets.append(len(out.encode("latin-1")))
        out += f"{n} 0 obj\n{body}\nendobj\n"

    xref_pos = len(out.encode("latin-1"))
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n"
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF"
    )
    path.write_bytes(out.encode("latin-1"))


if __name__ == "__main__":
    here = Path(__file__).parent
    make_pdf(
        here / "fixtures" / "sample.pdf",
        ["The project deadline is October 3 2026.", "Qdrant stores the document vectors."],
    )
    print("wrote fixture")

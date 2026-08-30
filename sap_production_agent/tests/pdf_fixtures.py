"""Build small real PDFs with known text, so the split and verify paths can be
tested without SAP or a printer.

pypdf reads PDFs but does not write text, and pulling in a full generator for a
test is overkill - so this assembles a minimal PDF by hand.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


def _escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def make_pdf(path: Path, pages: Sequence[str], padding: int = 0) -> Path:
    """Write a PDF where page i contains pages[i] as its only text.

    padding adds filler text so the file clears the validator's minimum size.
    """
    objects: list[bytes] = []
    page_count = len(pages)
    # 1 catalog, 2 pages tree, then per page: page object + content stream,
    # and finally the font.
    font_number = 3 + page_count * 2

    kids = " ".join(f"{3 + i * 2} 0 R" for i in range(page_count))
    objects.append(b"<</Type/Catalog/Pages 2 0 R>>")
    objects.append(f"<</Type/Pages/Kids[{kids}]/Count {page_count}>>".encode())

    for index, text in enumerate(pages):
        content_number = 4 + index * 2
        objects.append((
            f"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
            f"/Contents {content_number} 0 R"
            f"/Resources<</Font<</F1 {font_number} 0 R>>>>>>"
        ).encode())

        lines = [f"BT /F1 12 Tf 72 720 Td ({_escape(text)}) Tj ET"]
        for row in range(padding):
            lines.append(
                f"BT /F1 8 Tf 72 {700 - row * 9} Td "
                f"(filler line {row} for size) Tj ET"
            )
        stream = "\n".join(lines).encode()
        objects.append(
            b"<</Length " + str(len(stream)).encode() + b">>\nstream\n"
            + stream + b"\nendstream"
        )

    objects.append(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_at = len(out)
    total = len(objects) + 1
    out += f"xref\n0 {total}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<</Size {total}/Root 1 0 R>>\nstartxref\n{xref_at}\n%%EOF\n"
    ).encode()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))
    return path

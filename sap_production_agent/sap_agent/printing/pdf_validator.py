"""Verify the PDFs actually exist, are readable, and name the right order."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence

MIN_BYTES = 1024


@dataclass
class PdfCheck:
    work_order: str
    path: Path
    exists: bool = False
    size: int = 0
    pages: int = 0
    readable: bool = False
    names_order: bool = False
    problem: str = ""

    @property
    def ok(self) -> bool:
        return self.exists and self.readable and self.pages > 0 and not self.problem


@dataclass
class PdfReport:
    checks: List[PdfCheck] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing and all(check.ok for check in self.checks)

    @property
    def failures(self) -> List[PdfCheck]:
        return [check for check in self.checks if not check.ok]

    def summary(self) -> str:
        lines = [f"PDFs verified: {sum(1 for c in self.checks if c.ok)}/{len(self.checks)}"]
        for check in self.failures:
            lines.append(f"  FAIL {check.work_order}: {check.problem}")
        for work_order in self.missing:
            lines.append(f"  MISSING {work_order}: no PDF produced")
        return "\n".join(lines)


def verify(pdfs: Dict[str, Path], expected: Sequence[str]) -> PdfReport:
    report = PdfReport(missing=[w for w in expected if w not in pdfs])

    for work_order in expected:
        path = pdfs.get(work_order)
        if path is None:
            continue

        check = PdfCheck(work_order=work_order, path=Path(path))
        check.exists = check.path.exists()
        if not check.exists:
            check.problem = "file does not exist"
            report.checks.append(check)
            continue

        check.size = check.path.stat().st_size
        if check.size < MIN_BYTES:
            check.problem = f"only {check.size} bytes - likely truncated"
            report.checks.append(check)
            continue

        try:
            from pypdf import PdfReader

            reader = PdfReader(str(check.path))
            check.pages = len(reader.pages)
            check.readable = True
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
            check.names_order = work_order in text
            if check.pages == 0:
                check.problem = "no pages"
            elif not check.names_order:
                # The filename says one order; the content does not mention it.
                check.problem = (
                    f"content does not mention {work_order} - the file may be "
                    f"named for the wrong order"
                )
        except ImportError:
            check.readable = True  # cannot check further without pypdf
        except Exception as exc:  # noqa: BLE001
            check.problem = f"unreadable: {exc}"

        report.checks.append(check)

    return report

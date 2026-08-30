"""Turn the CO04 print job into one correctly named PDF per work order.

Two shapes come out of SAP, and which one you get depends on how the output is
configured. Both are handled:

  per_document      SAP raises one Windows save dialog per document. Each is
                    saved to a temporary name, then renamed by reading the work
                    order out of the PDF text - not by dialog order.
  combined_split    SAP produces one PDF holding every document. It is split by
                    finding the work order printed on each page.

Both routes name files from the work order found *inside* the document. Window
order is used only to sequence the saves, never to decide a filename, because a
misordered rename silently attaches the wrong paperwork to a shipment.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from ..models import KittingError

log = logging.getLogger(__name__)


@dataclass
class PrintOutput:
    pdfs: Dict[str, Path] = field(default_factory=dict)
    unmatched_pages: List[int] = field(default_factory=list)
    missing_orders: List[str] = field(default_factory=list)
    combined_source: Optional[Path] = None

    @property
    def ok(self) -> bool:
        return not self.unmatched_pages and not self.missing_orders


def output_dir(config: dict) -> Path:
    """Dated output folder, created on demand."""
    from datetime import date

    root = Path(config["output_dir"])
    if config.get("date_subfolder", True):
        root = root / date.today().isoformat()
    root.mkdir(parents=True, exist_ok=True)
    return root


def wait_for_save_dialog(config: dict, timeout: Optional[int] = None):
    """Return the Windows save dialog raised by the PDF printer."""
    try:
        from pywinauto import Desktop
    except ImportError as exc:
        raise KittingError("pip install pywinauto") from exc

    title = config.get("save_dialog_title", "Save Print Output As")
    timeout = timeout or config.get("save_dialog_timeout_s", 60)
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            dialog = Desktop(backend="win32").window(title_re=f".*{title}.*")
            if dialog.exists():
                dialog.wait("ready", timeout=5)
                return dialog
        except Exception:
            pass
        time.sleep(0.5)

    raise KittingError(
        f"no save dialog titled like {title!r} appeared within {timeout}s. "
        f"The title is localised - set printing.save_dialog_title to what "
        f"Windows actually shows, and confirm the printer is "
        f"{config.get('windows_printer')!r}."
    )


def save_to(dialog, path: Path, timeout: int = 60) -> Path:
    """Type a path into the save dialog and wait for the file to land."""
    path.parent.mkdir(parents=True, exist_ok=True)
    dialog.Edit.set_edit_text(str(path))
    dialog.Button.click()

    deadline = time.time() + timeout
    while time.time() < deadline:
        if path.exists() and path.stat().st_size > 0:
            return path
        time.sleep(0.5)
    raise KittingError(f"save dialog accepted but {path} never appeared")


def capture(config: dict, expected_orders: Sequence[str]) -> PrintOutput:
    """Collect whatever SAP printed and name it by work order."""
    mode = config.get("mode", "combined_split")
    destination = output_dir(config)

    if mode == "combined_split":
        combined = destination / config.get("combined_name", "_combined.pdf")
        dialog = wait_for_save_dialog(config)
        save_to(dialog, combined)
        result = split_by_work_order(combined, expected_orders, destination, config)
        result.combined_source = combined
        return result

    if mode == "per_document":
        return _capture_per_document(config, expected_orders, destination)

    raise KittingError(f"unknown printing.mode {mode!r}")


def _capture_per_document(
    config: dict, expected_orders: Sequence[str], destination: Path
) -> PrintOutput:
    """One dialog per document: save to a temp name, then identify each file."""
    staging = destination / "_staging"
    staging.mkdir(parents=True, exist_ok=True)
    saved: List[Path] = []

    for index in range(len(expected_orders)):
        try:
            dialog = wait_for_save_dialog(
                config, timeout=config.get("first_dialog_timeout_s", 60)
                if index == 0 else config.get("save_dialog_timeout_s", 60)
            )
        except KittingError:
            if index == 0:
                raise
            log.info("no further save dialogs after %d document(s)", index)
            break
        saved.append(save_to(dialog, staging / f"doc_{index:03d}.pdf"))

    result = PrintOutput()
    for path in saved:
        orders = work_orders_in_pdf(path, expected_orders)
        if len(orders) == 1:
            target = destination / f"{orders[0]}.pdf"
            path.replace(target)
            result.pdfs[orders[0]] = target
        else:
            log.warning("%s names %d work orders, not one", path.name, len(orders))
            result.unmatched_pages.append(saved.index(path))

    result.missing_orders = [w for w in expected_orders if w not in result.pdfs]
    return result


def split_by_work_order(
    combined: Path,
    expected_orders: Sequence[str],
    destination: Path,
    config: dict,
) -> PrintOutput:
    """Split a combined PDF into one file per work order, by page content."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError as exc:
        raise KittingError("pip install pypdf") from exc

    reader = PdfReader(str(combined))
    result = PrintOutput()
    pages_for: Dict[str, List[int]] = {}
    current: Optional[str] = None

    for number, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        found = _find_work_orders(text, expected_orders)

        if len(found) == 1:
            current = found[0]
        elif len(found) > 1:
            log.warning("page %d names %s - using the first", number + 1, found)
            current = found[0]
        elif current is None:
            # A continuation page before any order has been identified cannot
            # be attributed to anything.
            result.unmatched_pages.append(number + 1)
            continue

        pages_for.setdefault(current, []).append(number)

    for work_order, pages in pages_for.items():
        writer = PdfWriter()
        for number in pages:
            writer.add_page(reader.pages[number])
        target = destination / f"{work_order}.pdf"
        if target.exists() and not config.get("overwrite", False):
            raise KittingError(
                f"{target} already exists. Set printing.overwrite: true or clear "
                f"the folder - refusing to overwrite production paperwork."
            )
        with target.open("wb") as handle:
            writer.write(handle)
        result.pdfs[work_order] = target

    result.missing_orders = [w for w in expected_orders if w not in result.pdfs]
    return result


def work_orders_in_pdf(path: Path, expected: Sequence[str]) -> List[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise KittingError("pip install pypdf") from exc

    text = "\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)
    return _find_work_orders(text, expected)


def _find_work_orders(text: str, expected: Sequence[str]) -> List[str]:
    """Which of the expected orders this text names, in first-seen order."""
    found: List[str] = []
    for work_order in expected:
        if re.search(rf"\b0*{re.escape(work_order)}\b", text) and work_order not in found:
            found.append(work_order)
    return found

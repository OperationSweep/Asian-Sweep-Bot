"""The ZPRO flow itself: open the transaction, key the order, export the PDF.

Deliberately deterministic. The LLM never drives these keystrokes - see brain.py
for where Mistral does earn its place.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from . import pdf
from .models import KittingError, WorkOrder
from .sap import VKEY_ENTER, VKEY_F8_EXECUTE, SapSession

log = logging.getLogger(__name__)


@dataclass
class OrderResult:
    order_number: str
    ok: bool
    pdf_path: Optional[Path] = None
    error: Optional[str] = None
    screenshot: Optional[Path] = None

    def line(self) -> str:
        if self.ok:
            return f"  OK    {self.order_number} -> {self.pdf_path}"
        return f"  FAIL  {self.order_number}: {self.error}"


def process_order(sap: SapSession, order: WorkOrder, config: dict) -> OrderResult:
    """Run one work order through ZPRO and save its PDF."""
    tx = config["transaction"]
    log.info("processing %s", order.summary())

    try:
        sap.start_transaction(tx["code"])

        field_id = tx["fields"]["order_number"]
        sap.set_text(field_id, order.order_number)

        submit = tx.get("submit_vkey", VKEY_F8_EXECUTE)
        sap.send_vkey(submit)

        # A popup here almost always means ZPRO rejected the order rather than
        # rendering it, so surface the text instead of blindly pressing Enter.
        if sap.has_modal():
            raise KittingError(f"unexpected popup: {sap.modal_text()}")

        sap.raise_on_error(tx.get("ok_message_types", ["S", "W"]))

        path = pdf.export(sap, order.order_number, config["pdf"])
        return OrderResult(order.order_number, ok=True, pdf_path=path)

    except Exception as exc:
        shot = None
        run_config = config.get("run", {})
        if run_config.get("screenshot_on_error", True) and not sap.dry_run:
            shot = sap.screenshot(
                Path(run_config.get("screenshot_dir", ".")) / f"{order.order_number}.png"
            )
        log.error("%s failed: %s", order.order_number, exc)
        return OrderResult(order.order_number, ok=False, error=str(exc), screenshot=shot)


def process_batch(
    sap: SapSession, orders: List[WorkOrder], config: dict
) -> List[OrderResult]:
    """Run every work order, honouring run.stop_on_error."""
    stop_on_error = config.get("run", {}).get("stop_on_error", True)
    results: List[OrderResult] = []

    for order in orders:
        result = process_order(sap, order, config)
        results.append(result)

        if not result.ok and stop_on_error:
            log.error(
                "stopping after %s (run.stop_on_error is true). "
                "%d order(s) not attempted.",
                order.order_number,
                len(orders) - len(results),
            )
            break

    return results

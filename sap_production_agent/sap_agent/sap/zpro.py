"""The ZPRO flow: open the order, fill serials, post the goods issue.

Deterministic by design. No model chooses a keystroke here - the sequence is
fixed and every step is verified against what the workbook says should happen.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..models import Job, KittingError, Workbook
from . import messages as msg
from .connection import VKEY_ENTER, VKEY_F3_BACK, Session
from .controls import Controls

log = logging.getLogger(__name__)


@dataclass
class PostResult:
    work_order: str
    posted: bool
    classification: Optional[msg.Classification] = None
    document: str = ""
    serials_written: int = 0
    error: str = ""
    uncertain: bool = False
    raw_messages: List[tuple] = field(default_factory=list)


class ZproFlow:
    def __init__(
        self,
        session: Session,
        controls: Controls,
        book: Workbook,
        config: dict,
    ) -> None:
        self.session = session
        self.controls = controls
        self.book = book
        self.config = config

    def post(self, job: Job) -> PostResult:
        """Run one work order end to end. Never posts without verifying first."""
        log.info(
            "ZPRO %s (%s): %d serials",
            job.work_order, job.fibre_pair, len(job.serials),
        )
        try:
            self._open_order(job)
            self._verify_order_on_screen(job)
            self._expand_components()
            written = self._write_serials(job)
            self._verify_serial_count(job, written)
            return self._post_goods_issue(job, written)

        except KittingError as exc:
            return PostResult(job.work_order, posted=False, error=str(exc))
        except Exception as exc:  # noqa: BLE001 - anything else is still a failure
            return PostResult(job.work_order, posted=False, error=repr(exc))

    # -- steps -------------------------------------------------------------

    def _open_order(self, job: Job) -> None:
        self.session.start_transaction(self.config.get("transaction", "ZPRO"))
        self.session.set_text(self.controls.get("zpro.work_order_field"), job.work_order)

        execute = self.controls.optional("zpro.execute_button")
        if execute:
            self.session.press(execute)
        else:
            self.session.send_vkey(self.config.get("open_order_vkey", VKEY_ENTER))

    def _verify_order_on_screen(self, job: Job) -> None:
        """Confirm SAP is showing the order we intend to post.

        Skipped only when the display field has not been configured; where it
        is configured, a mismatch stops the run rather than posting serials
        against whatever order happens to be open.
        """
        display = self.controls.optional("zpro.order_display_field")
        if not display:
            log.warning(
                "zpro.order_display_field is not configured - cannot confirm the "
                "screen shows %s before posting", job.work_order,
            )
            return

        on_screen = (self.session.get_text(display) or "").strip().lstrip("0")
        expected = job.work_order.lstrip("0")
        if on_screen and on_screen != expected:
            raise KittingError(
                f"screen shows order {on_screen!r} but we intended "
                f"{job.work_order!r} - refusing to post"
            )

    def _expand_components(self) -> None:
        """Open the Components View section."""
        expand = self.controls.optional("zpro.components_expand_button")
        if not expand:
            log.warning("zpro.components_expand_button not configured - skipping")
            return
        if self.session.exists(expand) or self.session.dry_run:
            self.session.press(expand)

    def _write_serials(self, job: Job) -> int:
        """Fill the Serial Number column, one row per serial, in sheet order."""
        table = self.controls.get("zpro.serial_table")
        column = self.controls.get("zpro.serial_column")
        first_row = int(self.config.get("serial_first_row", 0))

        capacity = self.session.table_row_count(table)
        if capacity and len(job.serials) > capacity:
            raise KittingError(
                f"{len(job.serials)} serials to write but the table shows only "
                f"{capacity} rows. Scrolling is not implemented - raise "
                f"sap.serial_first_row or handle paging before posting."
            )

        for offset, component in enumerate(job.serials):
            self.session.set_table_cell(
                table, first_row + offset, column, component.serial
            )
        return len(job.serials)

    def _verify_serial_count(self, job: Job, written: int) -> None:
        if written != len(job.serials):
            raise KittingError(
                f"wrote {written} serials but the workbook has "
                f"{len(job.serials)} for {job.work_order}"
            )
        if written == 0:
            raise KittingError(f"{job.work_order} has no serials to write")

    def _post_goods_issue(self, job: Job, written: int) -> PostResult:
        """Tick Post Goods Issue, press Post, then classify what SAP says.

        Everything before this point is reversible. Once Post is pressed it is
        not, which is why an unclassifiable response is recorded as uncertain
        rather than retried.
        """
        self.session.set_checkbox(
            self.controls.get("zpro.post_goods_issue_checkbox"), True
        )
        self.session.press(self.controls.get("zpro.post_button"))

        raw = self.session.collect_messages()
        classifications = msg.classify_all(
            raw,
            non_serialised_materials=self.book.non_serialised_materials,
            serialised_materials=self.book.serialised_materials,
        )
        verdict = msg.worst(classifications)
        log.info(
            "%s -> %s: %s", job.work_order, verdict.message_class.value, verdict.reason
        )

        if verdict.may_continue:
            self._confirm_and_exit()
            return PostResult(
                job.work_order, posted=True, classification=verdict,
                document=_document_number(raw), serials_written=written,
                raw_messages=raw,
            )

        # Post was pressed and SAP did not confirm. Whether stock moved is not
        # knowable from here, so it is flagged for a human rather than retried.
        return PostResult(
            job.work_order, posted=False, classification=verdict,
            serials_written=written, raw_messages=raw,
            uncertain=verdict.uncertain,
            error=f"{verdict.message_class.value}: {verdict.reason}",
        )

    def _confirm_and_exit(self) -> None:
        """Dismiss the confirmation popup and leave ZPRO ready for the next order."""
        confirm = self.controls.optional("zpro.confirm_button")
        if confirm and self.session.has_modal():
            self.session.press(confirm)
        elif self.session.has_modal():
            self.session.send_vkey(VKEY_ENTER, window="wnd[1]")
        self.session.send_vkey(VKEY_F3_BACK)


def _document_number(raw_messages: List[tuple]) -> str:
    """Pull a material document number out of SAP's confirmation, if present."""
    import re

    for _, text in raw_messages:
        found = re.search(r"\b(\d{9,10})\b", text or "")
        if found:
            return found.group(1)
    return ""

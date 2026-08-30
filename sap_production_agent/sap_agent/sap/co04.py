"""CO04 reprint for the range of work orders that actually posted.

The range is derived from run state, never from the spreadsheet, so an order
that failed in ZPRO cannot be dragged into the reprint by being adjacent to one
that succeeded.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from ..models import KittingError
from .connection import VKEY_F8_EXECUTE, Session
from .controls import Controls

log = logging.getLogger(__name__)


@dataclass
class Co04Result:
    order_from: str
    order_to: str
    expected_count: int
    selected_count: int = 0
    printed: bool = False
    error: str = ""
    actions: List[str] = field(default_factory=list)


class Co04Flow:
    def __init__(self, session: Session, controls: Controls, config: dict) -> None:
        self.session = session
        self.controls = controls
        self.config = config

    def reprint(
        self,
        order_from: str,
        order_to: str,
        expected_count: int,
        unposted_in_range: Optional[List[str]] = None,
    ) -> Co04Result:
        """Select the posted range and send it to the printer.

        A gap in the range is fatal: CO04 selects everything between the two
        numbers, so printing a range with a hole in it reprints an order this
        run never posted.
        """
        result = Co04Result(order_from, order_to, expected_count)

        if unposted_in_range:
            result.error = (
                f"orders {', '.join(unposted_in_range)} fall inside "
                f"{order_from}-{order_to} but were not posted by this run. "
                f"CO04 selects by range, so printing would include them. "
                f"Print the contiguous blocks separately, or post the gaps first."
            )
            return result

        try:
            self._open()
            self._set_print_mode()
            self._set_selection(order_from, order_to)
            self._execute()
            result.selected_count = self._select_all(expected_count)
            self._print()
            result.printed = True
        except KittingError as exc:
            result.error = str(exc)
        except Exception as exc:  # noqa: BLE001
            result.error = repr(exc)

        result.actions = list(getattr(self.session, "actions", []))
        return result

    # -- steps -------------------------------------------------------------

    def _open(self) -> None:
        self.session.start_transaction(self.config.get("transaction", "CO04"))

    def _set_print_mode(self) -> None:
        """Reprint, not original print - otherwise SAP may refuse or re-issue."""
        reprint = self.controls.optional("co04.reprint_radio")
        if reprint:
            self.session.select(reprint)
            return
        field_id = self.controls.optional("co04.print_mode_field")
        if field_id:
            self.session.set_text(field_id, self.config.get("print_mode", "2"))
            return
        log.warning(
            "neither co04.reprint_radio nor co04.print_mode_field is configured - "
            "print mode left at its default"
        )

    def _set_selection(self, order_from: str, order_to: str) -> None:
        """Clear the other selection criteria, then set plant and order range.

        The CO04 selection screen keeps whatever was entered last. A leftover
        order type, material or date range from a previous run would silently
        narrow the selection, so anything listed in co04.clear_fields is blanked
        before ours are set. Fields already empty cost nothing to blank again.
        """
        self._clear_selection()
        self.session.set_text(
            self.controls.get("co04.plant_field"), str(self.config.get("plant", "8000"))
        )
        self.session.set_text(self.controls.get("co04.order_from_field"), order_from)
        self.session.set_text(self.controls.get("co04.order_to_field"), order_to)

    def _clear_selection(self) -> None:
        for element_id in self.controls.optional("co04.clear_fields", []) or []:
            if not element_id:
                continue
            try:
                self.session.set_text(element_id, "")
            except Exception as exc:  # noqa: BLE001
                # A field absent from this system's screen is not a problem: it
                # cannot be carrying a stale value either. Anything worse fails
                # again immediately when the plant and range are set below.
                log.info("clear_fields: skipping %s (%s)", element_id, exc)

    def _execute(self) -> None:
        execute = self.controls.optional("co04.execute_button")
        if execute:
            self.session.press(execute)
        else:
            self.session.send_vkey(VKEY_F8_EXECUTE)

    def _select_all(self, expected_count: int) -> int:
        """Tick every row, then check the count matches what we posted."""
        select_all = self.controls.get("co04.select_all_button")
        self.session.press(select_all)

        table = self.controls.optional("co04.results_table")
        if not table:
            log.warning(
                "co04.results_table is not configured - cannot verify that CO04 "
                "returned %d documents", expected_count,
            )
            return expected_count

        actual = self.session.table_row_count(table)
        if actual and actual != expected_count:
            raise KittingError(
                f"CO04 returned {actual} documents but {expected_count} orders "
                f"were posted. Not printing until that is explained."
            )
        return actual or expected_count

    def _print(self) -> None:
        self.session.press(self.controls.get("co04.print_button"))
        dialog_ok = self.controls.optional("co04.print_dialog_confirm")
        if dialog_ok:
            self.session.press(dialog_ok)

"""A scriptable fake SAP session, so the whole flow can be tested off-system.

It implements the same interface as SapSession and records every action, so
tests assert on the exact keystroke sequence that would reach production. SAP
responses are scripted per work order:

    MockSession(responses={"900000001": [("W", "Serial Number missing for <material>")]})
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MockSession:
    dry_run = False

    def __init__(
        self,
        responses: Optional[Dict[str, List[Tuple[str, str]]]] = None,
        table_rows: int = 40,
        fail_on: Optional[Dict[str, str]] = None,
        missing_controls: Optional[List[str]] = None,
    ) -> None:
        self.actions: List[str] = []
        self.responses = responses or {}
        self.default_response: List[Tuple[str, str]] = [("S", "Document 4900000001 posted")]
        self.table_rows = table_rows
        self.fail_on = fail_on or {}
        self.missing_controls = set(missing_controls or [])
        self.current_order = ""
        self.cells: Dict[Tuple[int, str], str] = {}
        self.transaction = ""
        self._modal = ""

    # -- interface ---------------------------------------------------------

    def start_transaction(self, code: str) -> None:
        self.transaction = code
        self.actions.append(f"start /n{code}")

    def set_text(self, element_id: str, value: str) -> None:
        self._guard(element_id)
        self.actions.append(f"set {element_id} = {value!r}")
        if "work_order" in element_id or "AUFNR" in element_id.upper():
            self.current_order = value
            self._modal = ""

    def get_text(self, element_id: str) -> str:
        self._guard(element_id)
        # The screen echoes back whichever order was keyed in.
        return self.current_order

    def press(self, element_id: str) -> None:
        self._guard(element_id)
        self.actions.append(f"press {element_id}")
        if self.current_order in self.fail_on:
            raise RuntimeError(self.fail_on[self.current_order])

    def select(self, element_id: str) -> None:
        self._guard(element_id)
        self.actions.append(f"select {element_id}")

    def set_checkbox(self, element_id: str, checked: bool = True) -> None:
        self._guard(element_id)
        self.actions.append(f"checkbox {element_id} = {checked}")

    def send_vkey(self, key: int, window: str = "wnd[0]") -> None:
        self.actions.append(f"vkey {key} -> {window}")

    def exists(self, element_id: str) -> bool:
        if element_id == "wnd[1]":
            return bool(self._modal)
        return element_id not in self.missing_controls

    def set_table_cell(self, table_id: str, row: int, column: str, value: str) -> None:
        self._guard(table_id)
        self.cells[(row, column)] = value
        self.actions.append(f"cell[{row}][{column}] = {value!r}")

    def table_row_count(self, table_id: str) -> int:
        self._guard(table_id)
        return self.table_rows

    def status_message(self) -> Tuple[str, str]:
        messages = self.responses.get(self.current_order, self.default_response)
        return messages[0] if messages else ("", "")

    def collect_messages(self) -> List[Tuple[str, str]]:
        return list(self.responses.get(self.current_order, self.default_response))

    def has_modal(self) -> bool:
        return bool(self._modal)

    def modal_text(self) -> str:
        return self._modal

    def screenshot(self, path: str | Path) -> Optional[Path]:
        self.actions.append(f"screenshot {path}")
        return None

    # -- test helpers ------------------------------------------------------

    def raise_modal(self, text: str) -> None:
        self._modal = text

    def serials_written(self, column: str) -> List[str]:
        return [
            value for (_, col), value in sorted(self.cells.items())
            if col == column
        ]

    def _guard(self, element_id: str) -> None:
        if element_id in self.missing_controls:
            raise RuntimeError(f"control {element_id} not on screen")

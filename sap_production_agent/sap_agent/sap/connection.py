"""SAP GUI Scripting session wrapper.

Every SAP interaction goes through this class, which gives dry-run one place to
intercept and gives the mock session one interface to implement.

Prerequisites on the Windows machine:
  * server profile parameter  sapgui/user_scripting = TRUE   (Basis sets this)
  * SAP GUI > Options > Accessibility & Scripting > Scripting > Enable scripting
  * both "notify when a script..." boxes unticked, or every step stalls on a
    modal the script cannot dismiss
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, List, Optional, Protocol, Tuple

from ..models import KittingError

log = logging.getLogger(__name__)

VKEY_ENTER = 0
VKEY_F3_BACK = 3
VKEY_F8_EXECUTE = 8
VKEY_F11_SAVE = 11
VKEY_CTRL_P = 86


class Session(Protocol):
    """What the ZPRO and CO04 flows need. Implemented by SapSession and MockSession."""

    dry_run: bool

    def start_transaction(self, code: str) -> None: ...
    def set_text(self, element_id: str, value: str) -> None: ...
    def get_text(self, element_id: str) -> str: ...
    def press(self, element_id: str) -> None: ...
    def select(self, element_id: str) -> None: ...
    def set_checkbox(self, element_id: str, checked: bool) -> None: ...
    def send_vkey(self, key: int, window: str = "wnd[0]") -> None: ...
    def exists(self, element_id: str) -> bool: ...
    def status_message(self) -> Tuple[str, str]: ...
    def collect_messages(self) -> List[Tuple[str, str]]: ...
    def has_modal(self) -> bool: ...
    def modal_text(self) -> str: ...
    def set_table_cell(self, table_id: str, row: int, column: str, value: str) -> None: ...
    def table_row_count(self, table_id: str) -> int: ...
    def screenshot(self, path: str | Path) -> Optional[Path]: ...


class SapSession:
    """Attach to a running SAP GUI session, or open one if none exists."""

    def __init__(self, config: dict, dry_run: bool = True) -> None:
        self.config = config
        self.dry_run = dry_run
        self.session: Any = None
        self.actions: List[str] = []
        self._table_kind = config.get("serial_table_kind", "auto")

    # -- lifecycle ---------------------------------------------------------

    def connect(self) -> "SapSession":
        if self.dry_run:
            self._record("attach to SAP GUI scripting engine")
            return self

        try:
            import win32com.client
        except ImportError as exc:  # pragma: no cover - Windows only
            raise KittingError(
                "pywin32 is not installed, or this is not Windows. SAP GUI "
                "Scripting exists only in SAP GUI for Windows."
            ) from exc

        try:
            gui = win32com.client.GetObject("SAPGUI")
        except Exception as exc:  # pragma: no cover
            raise KittingError(
                "Could not reach SAP GUI. Start SAP Logon, and confirm scripting "
                "is enabled (Options > Accessibility & Scripting > Scripting)."
            ) from exc

        engine = gui.GetScriptingEngine
        if getattr(engine, "Children", None) is None or engine.Children.Count == 0:
            name = self.config.get("connection_name")
            if not name:
                raise KittingError(
                    "No SAP connection is open and sap.connection_name is not set."
                )
            log.info("opening SAP connection %r", name)
            engine.OpenConnection(name, True)

        connection = engine.Children(0)
        if connection.Children.Count == 0:
            raise KittingError("SAP GUI has a connection but no session.")

        self.session = connection.Children(0)
        log.info(
            "attached to %s client %s as %s",
            self.session.Info.SystemName,
            self.session.Info.Client,
            self.session.Info.User,
        )

        if self._is_login_screen():
            self._login()
        return self

    @property
    def info(self) -> dict:
        if self.dry_run or self.session is None:
            return {"system": "DRY-RUN", "client": "", "user": "", "transaction": ""}
        return {
            "system": self.session.Info.SystemName,
            "client": self.session.Info.Client,
            "user": self.session.Info.User,
            "transaction": self.session.Info.Transaction,
        }

    def _is_login_screen(self) -> bool:
        return self.exists("wnd[0]/usr/txtRSYST-BNAME")

    def _login(self) -> None:
        user = os.environ.get("SAP_USER")
        password = os.environ.get("SAP_PASSWORD")
        if not user or not password:
            raise KittingError(
                "SAP is not logged in and SAP_USER / SAP_PASSWORD are unset. "
                "Log in to SAP GUI by hand before running - then the automation "
                "attaches to your session and never handles a password."
            )
        log.info("logging in as %s", user)
        self.set_text("wnd[0]/usr/txtRSYST-MANDT", self.config.get("client", ""))
        self.set_text("wnd[0]/usr/txtRSYST-BNAME", user)
        self.set_text("wnd[0]/usr/pwdRSYST-BCODE", password)
        self.set_text("wnd[0]/usr/txtRSYST-LANGU", self.config.get("language", "EN"))
        self.send_vkey(VKEY_ENTER)
        self._handle_multi_logon()
        if self._is_login_screen():
            raise KittingError(
                f"login failed: {self.status_message()[1] or 'check credentials'}"
            )

    def _handle_multi_logon(self) -> None:
        if not self.exists("wnd[1]/usr/radMULTI_LOGON_OPT1"):
            return
        option = 1 if self.config.get("multi_logon") == "continue_and_end_others" else 2
        log.info("multiple-logon prompt: choosing option %d", option)
        self.select(f"wnd[1]/usr/radMULTI_LOGON_OPT{option}")
        self.press("wnd[1]/tbar[0]/btn[0]")

    # -- primitives --------------------------------------------------------

    def _find(self, element_id: str) -> Any:
        try:
            return self.session.findById(element_id)
        except Exception as exc:
            raise KittingError(
                f"control {element_id!r} is not on the current screen. "
                f"Re-run tools/discover_controls.py on this screen and update "
                f"controls.yaml."
            ) from exc

    def start_transaction(self, code: str) -> None:
        """/n closes whatever is open first, so each order starts from a clean screen."""
        self._record(f"start transaction /n{code}")
        if self.dry_run:
            return
        self.session.findById("wnd[0]/tbar[0]/okcd").text = f"/n{code}"
        self.session.findById("wnd[0]").sendVKey(VKEY_ENTER)

    def set_text(self, element_id: str, value: str) -> None:
        self._record(f"set {element_id} = {value!r}")
        if self.dry_run:
            return
        self._find(element_id).text = value

    def get_text(self, element_id: str) -> str:
        if self.dry_run:
            return ""
        return self._find(element_id).text or ""

    def press(self, element_id: str) -> None:
        self._record(f"press {element_id}")
        if self.dry_run:
            return
        self._find(element_id).press()

    def select(self, element_id: str) -> None:
        self._record(f"select {element_id}")
        if self.dry_run:
            return
        self._find(element_id).select()

    def set_checkbox(self, element_id: str, checked: bool = True) -> None:
        self._record(f"set checkbox {element_id} = {checked}")
        if self.dry_run:
            return
        self._find(element_id).selected = checked

    def send_vkey(self, key: int, window: str = "wnd[0]") -> None:
        self._record(f"sendVKey {key} to {window}")
        if self.dry_run:
            return
        self._find(window).sendVKey(key)

    def exists(self, element_id: str) -> bool:
        if self.dry_run or self.session is None:
            return False
        try:
            self.session.findById(element_id)
            return True
        except Exception:
            return False

    # -- tables ------------------------------------------------------------

    def set_table_cell(self, table_id: str, row: int, column: str, value: str) -> None:
        """Write one cell, handling both classic table controls and ALV grids.

        GuiTableControl is addressed with getCell(row, col); a GuiShell ALV grid
        with modifyCell(row, col_name, value). Which one ZPRO uses is visible in
        discover_controls.py output as the control's Type.
        """
        self._record(f"table {table_id} row {row} [{column}] = {value!r}")
        if self.dry_run:
            return

        table = self._find(table_id)
        kind = self._table_kind
        if kind == "auto":
            kind = "alv" if "shell" in str(getattr(table, "Type", "")).lower() else "table"

        if kind == "alv":
            table.modifyCell(row, column, value)
        else:
            table.getCell(row, int(column)).text = value

    def table_row_count(self, table_id: str) -> int:
        if self.dry_run:
            return 0
        table = self._find(table_id)
        for attribute in ("RowCount", "VisibleRowCount"):
            count = getattr(table, attribute, None)
            if count is not None:
                return int(count)
        return 0

    # -- feedback ----------------------------------------------------------

    def status_message(self) -> Tuple[str, str]:
        """(message type, text) from the status bar. S/W/E/A/I."""
        if self.dry_run:
            return ("", "")
        try:
            bar = self.session.findById("wnd[0]/sbar")
            return (bar.messageType or "", bar.text or "")
        except Exception:
            return ("", "")

    def collect_messages(self) -> List[Tuple[str, str]]:
        """Status bar plus any popup text, as things to classify."""
        messages = []
        kind, text = self.status_message()
        if text:
            messages.append((kind, text))
        if self.has_modal():
            popup = self.modal_text()
            if popup:
                messages.append(("W", popup))
        return messages

    def has_modal(self) -> bool:
        return self.exists("wnd[1]")

    def modal_text(self) -> str:
        if not self.has_modal():
            return ""
        try:
            return "\n".join(
                child.Text
                for child in self.session.findById("wnd[1]/usr").Children
                if getattr(child, "Text", "")
            ).strip()
        except Exception:
            return "(popup present, text unreadable)"

    def screenshot(self, path: str | Path) -> Optional[Path]:
        if self.dry_run or self.session is None:
            return None
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.session.findById("wnd[0]").hardCopy(str(path))
            return path
        except Exception:
            log.warning("could not capture SAP screenshot")
            return None

    def _record(self, action: str) -> None:
        self.actions.append(action)
        log.info("%s%s", "[dry-run] " if self.dry_run else "", action)

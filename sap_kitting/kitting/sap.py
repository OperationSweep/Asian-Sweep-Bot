"""Thin wrapper over SAP GUI Scripting (the supported COM automation API).

Everything that talks to SAP goes through here so that dry-run mode has exactly
one place to intercept, and so the ZPRO flow reads as business steps rather than
COM calls.

Requires, on the SAP side:
  * profile parameter  sapgui/user_scripting = TRUE   (Basis sets this)
  * SAP GUI > Options > Accessibility & Scripting > Scripting > Enable scripting
  * the two "notify when a script..." boxes unticked, or every step throws a
    modal dialog that the script cannot dismiss.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

from .models import KittingError, SapMessage

log = logging.getLogger(__name__)

# Virtual key codes used by SAP GUI Scripting.
VKEY_ENTER = 0
VKEY_F3_BACK = 3
VKEY_F8_EXECUTE = 8
VKEY_CTRL_P = 86


class SapSession:
    """Attach to a running SAP GUI session, or open one if none exists."""

    def __init__(self, config: dict, dry_run: bool = True) -> None:
        self.config = config
        self.dry_run = dry_run
        self.session: Any = None
        self._actions: list[str] = []

    # -- lifecycle ---------------------------------------------------------

    def connect(self) -> "SapSession":
        """Attach to SAP GUI. In dry-run we never touch COM at all."""
        if self.dry_run:
            log.info("[dry-run] would attach to SAP GUI scripting engine")
            return self

        try:
            import win32com.client
        except ImportError as exc:  # pragma: no cover - Windows only
            raise KittingError(
                "pywin32 is not installed, or this is not Windows. SAP GUI "
                "Scripting only exists in SAP GUI for Windows."
            ) from exc

        try:
            gui = win32com.client.GetObject("SAPGUI")
        except Exception as exc:  # pragma: no cover - environment dependent
            raise KittingError(
                "SAP GUI is not running. Start SAP Logon first."
            ) from exc

        engine = gui.GetScriptingEngine
        if engine.Children.Count == 0:
            self._open_connection(engine)

        connection = engine.Children(0)
        if connection.Children.Count == 0:
            raise KittingError("SAP GUI has a connection but no session.")

        self.session = connection.Children(0)
        log.info("attached to SAP session %s", self.session.Info.SystemName)

        if self._is_login_screen():
            self._login()

        return self

    def _open_connection(self, engine: Any) -> None:
        name = self.config["connection_name"]
        log.info("opening SAP connection %r", name)
        engine.OpenConnection(name, True)

    def _is_login_screen(self) -> bool:
        """The login screen is the one that has the username field."""
        try:
            self.session.findById("wnd[0]/usr/txtRSYST-BNAME")
            return True
        except Exception:
            return False

    def _login(self) -> None:
        user = os.environ.get("SAP_USER")
        password = os.environ.get("SAP_PASSWORD")
        if not user or not password:
            raise KittingError(
                "Not logged in to SAP and SAP_USER / SAP_PASSWORD are not set. "
                "Either log in to SAP GUI by hand before running, or set those "
                "environment variables."
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
                f"Login failed: {self.status_message()[1] or 'check credentials'}"
            )

    def _handle_multi_logon(self) -> None:
        """Answer the 'already logged on in another session' popup if it shows."""
        try:
            self.session.findById("wnd[1]/usr/radMULTI_LOGON_OPT1")
        except Exception:
            return

        mode = self.config.get("multi_logon", "continue_and_end_others")
        option = 1 if mode == "continue_and_end_others" else 2
        log.info("multiple-logon prompt, choosing option %d", option)
        self.session.findById(f"wnd[1]/usr/radMULTI_LOGON_OPT{option}").select()
        self.session.findById("wnd[1]/tbar[0]/btn[0]").press()

    # -- primitives --------------------------------------------------------

    def set_text(self, element_id: str, value: str) -> None:
        self._record(f"set {element_id} = {value!r}")
        if self.dry_run:
            return
        try:
            self.session.findById(element_id).text = value
        except Exception as exc:
            raise KittingError(
                f"Could not set field {element_id}. Run inspect_screen.py to "
                f"confirm the ID on the current screen."
            ) from exc

    def press(self, element_id: str) -> None:
        self._record(f"press {element_id}")
        if self.dry_run:
            return
        self.session.findById(element_id).press()

    def send_vkey(self, key: int, window: str = "wnd[0]") -> None:
        self._record(f"sendVKey {key} to {window}")
        if self.dry_run:
            return
        self.session.findById(window).sendVKey(key)

    def start_transaction(self, code: str) -> None:
        """Open a transaction from the command field.

        The /n prefix closes whatever is open first, which keeps the run
        idempotent no matter what screen the previous order left behind.
        """
        self._record(f"start transaction /n{code}")
        if self.dry_run:
            return
        self.session.findById("wnd[0]/tbar[0]/okcd").text = f"/n{code}"
        self.session.findById("wnd[0]").sendVKey(VKEY_ENTER)

    # -- feedback ----------------------------------------------------------

    def status_message(self) -> tuple[str, str]:
        """Return (message_type, message_text) from the status bar.

        Types: S success, W warning, E error, A abort, I info.
        """
        if self.dry_run:
            return ("S", "")
        try:
            bar = self.session.findById("wnd[0]/sbar")
            return (bar.messageType or "", bar.text or "")
        except Exception:
            return ("", "")

    def raise_on_error(self, ok_types: list[str]) -> None:
        msg_type, text = self.status_message()
        if msg_type and msg_type not in ok_types:
            raise SapMessage(msg_type, text)

    def has_modal(self) -> bool:
        """True when a popup window is sitting on top of the main window."""
        if self.dry_run:
            return False
        try:
            self.session.findById("wnd[1]")
            return True
        except Exception:
            return False

    def modal_text(self) -> str:
        """Best-effort text of the popup, for logging and LLM triage."""
        if not self.has_modal():
            return ""
        try:
            return "\n".join(
                child.Text
                for child in self.session.findById("wnd[1]/usr").Children
                if getattr(child, "Text", "")
            )
        except Exception:
            return "(popup present, text unreadable)"

    def screenshot(self, path: str | Path) -> Optional[Path]:
        """Save a picture of the SAP window - the fastest way to debug a run."""
        if self.dry_run:
            return None
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.session.findById("wnd[0]").hardCopy(str(path))
            return path
        except Exception:
            log.warning("could not capture SAP screenshot")
            return None

    # -- dry-run bookkeeping ----------------------------------------------

    def _record(self, action: str) -> None:
        self._actions.append(action)
        log.info("%s%s", "[dry-run] " if self.dry_run else "", action)

    @property
    def actions(self) -> list[str]:
        return list(self._actions)

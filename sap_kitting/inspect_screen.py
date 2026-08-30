"""Print the element tree of whatever SAP screen is currently open.

This is the tool that unblocks the config: ZPRO is a custom transaction, so its
field IDs exist only on your system and no one can guess them.

Usage (on the Windows box, with SAP GUI open on the ZPRO selection screen):

    python inspect_screen.py

Look for the field you type the order number into - it will be something like
    wnd[0]/usr/ctxtP_AUFNR   (ctxt = field with a search help)
    wnd[0]/usr/txtP_ORDER    (txt  = plain text field)
and paste it into config.yaml under transaction.fields.order_number.

Also useful on the ZPRO *output* screen to find an export/PDF button ID for the
preview_button strategy.
"""

from __future__ import annotations

import argparse
import sys

INTERESTING = ("GuiTextField", "GuiCTextField", "GuiPasswordField",
               "GuiButton", "GuiCheckBox", "GuiRadioButton", "GuiComboBox")


def walk(element, depth: int = 0, only_interesting: bool = True) -> None:
    kind = getattr(element, "Type", "?")
    element_id = getattr(element, "Id", "?")
    text = (getattr(element, "Text", "") or "").strip()
    tooltip = (getattr(element, "Tooltip", "") or "").strip()

    if not only_interesting or kind in INTERESTING:
        # Ids come back fully qualified; trim the session prefix for readability.
        short = element_id.split("ses[0]/", 1)[-1]
        label = f" text={text!r}" if text else ""
        hint = f" tooltip={tooltip!r}" if tooltip and tooltip != text else ""
        print(f"{'  ' * depth}{kind:<18} {short}{label}{hint}")

    children = getattr(element, "Children", None)
    if children is not None:
        for index in range(children.Count):
            walk(children(index), depth + 1, only_interesting)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all", action="store_true",
        help="show every element, not just input fields and buttons",
    )
    parser.add_argument(
        "--window", default="wnd[0]",
        help="window to dump; use wnd[1] for a popup (default: wnd[0])",
    )
    args = parser.parse_args()

    try:
        import win32com.client
    except ImportError:
        print("pywin32 is not installed, or this is not Windows.", file=sys.stderr)
        return 1

    try:
        gui = win32com.client.GetObject("SAPGUI")
        session = gui.GetScriptingEngine.Children(0).Children(0)
    except Exception as exc:
        print(f"Could not attach to SAP GUI: {exc}", file=sys.stderr)
        print("Is SAP GUI running, and is scripting enabled?", file=sys.stderr)
        return 1

    print(f"System: {session.Info.SystemName}  Transaction: {session.Info.Transaction}")
    print("-" * 70)
    walk(session.findById(args.window), only_interesting=not args.all)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Expose the kitting run as MCP tools, so Le Chat / Studio can drive it.

This is the "talk to it in chat" layer:

    You: "kit work order 4500123456"
    Le Chat -> list_orders / kit_order -> this server -> SAP on your desktop

Run it on the same Windows machine as SAP GUI:

    pip install "mcp[cli]"
    python -m kitting.mcp_server            # stdio, for a local MCP client
    python -m kitting.mcp_server --http     # HTTP, for a remote client

Important: Le Chat runs in Mistral's cloud, so for it to reach this process the
HTTP endpoint has to be reachable from the internet - a tunnel, or a box in your
DMZ. That is a network and security decision for your IT team, not something to
switch on casually on a machine that is logged in to production SAP. Until that
is settled, run.py from the desktop does the same job with no inbound exposure.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import yaml

from .models import KittingError
from .sap import SapSession
from .sheet import read_workbook
from .zpro import process_order

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    raise SystemExit('pip install "mcp[cli]" to run the MCP server')

mcp = FastMCP("sap-kitting")

_CONFIG: dict = {}
_SHEET: Path | None = None


@mcp.tool()
def list_orders() -> List[dict]:
    """List the work orders in the current scan sheet, with their components."""
    orders = read_workbook(_SHEET, _CONFIG["sheet"])
    return [
        {
            "order_number": order.order_number,
            "component_count": len(order.components),
            "total_quantity": order.total_quantity,
            "components": [
                {
                    "part_number": c.part_number,
                    "serial": c.serial,
                    "quantity": c.quantity,
                    "type": c.component_type,
                }
                for c in order.components
            ],
        }
        for order in orders
    ]


@mcp.tool()
def kit_order(order_number: str, execute: bool = False) -> dict:
    """Run one work order through ZPRO and save its PDF.

    Set execute=True to actually drive SAP. With execute=False (the default)
    it returns the exact keystrokes it would send, so the run can be checked
    before anything is posted.
    """
    orders = read_workbook(_SHEET, _CONFIG["sheet"])
    match = next((o for o in orders if o.order_number == order_number.strip()), None)
    if match is None:
        raise KittingError(
            f"{order_number} is not in the sheet. Available: "
            f"{', '.join(o.order_number for o in orders)}"
        )

    sap = SapSession(_CONFIG["sap"], dry_run=not execute).connect()
    result = process_order(sap, match, _CONFIG)

    return {
        "order_number": result.order_number,
        "ok": result.ok,
        "pdf_path": str(result.pdf_path) if result.pdf_path else None,
        "error": result.error,
        "planned_actions": sap.actions if not execute else None,
    }


@mcp.tool()
def sap_status() -> dict:
    """Report whether SAP GUI is reachable and which system is logged in."""
    try:
        sap = SapSession(_CONFIG["sap"], dry_run=False).connect()
        return {
            "connected": True,
            "system": sap.session.Info.SystemName,
            "client": sap.session.Info.Client,
            "user": sap.session.Info.User,
            "transaction": sap.session.Info.Transaction,
        }
    except Exception as exc:
        return {"connected": False, "error": str(exc)}


def main() -> None:
    global _CONFIG, _SHEET

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--sheet", required=True, help="scan spreadsheet to serve")
    parser.add_argument("--http", action="store_true",
                        help="serve over HTTP instead of stdio (see the warning above)")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    _CONFIG = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    _SHEET = Path(args.sheet)

    if args.http:
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()

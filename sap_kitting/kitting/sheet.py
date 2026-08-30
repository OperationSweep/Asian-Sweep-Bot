"""Read the scan spreadsheet into WorkOrder objects.

The column names live in config.yaml because every site labels its scan sheet
differently. Matching is case- and whitespace-insensitive so that a header of
"Work Order " still lines up with "work order".
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .models import Component, KittingError, WorkOrder, normalise_order_number


def _normalise_header(name: object) -> str:
    return str(name).strip().lower()


def _resolve_columns(frame: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, str]:
    """Map logical names to the frame's real column labels.

    ``order_number`` is the only column we cannot proceed without; the rest are
    optional so a minimal sheet (just order numbers) still works.
    """
    available = {_normalise_header(c): c for c in frame.columns}
    resolved: Dict[str, str] = {}
    missing: List[str] = []

    for logical, header in mapping.items():
        if header is None:
            continue
        actual = available.get(_normalise_header(header))
        if actual is None:
            missing.append(f"{logical} -> '{header}'")
        else:
            resolved[logical] = actual

    if "order_number" not in resolved:
        raise KittingError(
            "Could not find the work-order column. Configured as "
            f"'{mapping.get('order_number')}', but the sheet has: "
            f"{list(frame.columns)}"
        )

    if missing:
        # Not fatal - a sheet without serials is still kittable.
        print(f"[sheet] optional columns not found, ignoring: {', '.join(missing)}")

    return resolved


def _cell(row: pd.Series, columns: Dict[str, str], key: str) -> Optional[str]:
    if key not in columns:
        return None
    value = row[columns[key]]
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _quantity(row: pd.Series, columns: Dict[str, str]) -> float:
    raw = _cell(row, columns, "quantity")
    if raw is None:
        return 1.0
    try:
        return float(raw)
    except ValueError:
        raise KittingError(f"quantity '{raw}' is not a number")


def read_workbook(path: str | Path, sheet_config: dict) -> List[WorkOrder]:
    """Load the workbook and group scanned components by work order.

    Order is preserved: work orders come back in the order they first appear in
    the sheet, so the SAP run follows the same sequence the kitter scanned in.
    """
    path = Path(path)
    if not path.exists():
        raise KittingError(f"spreadsheet not found: {path}")

    sheet_name = sheet_config.get("sheet_name")
    frame = pd.read_excel(
        path,
        sheet_name=0 if sheet_name is None else sheet_name,
        header=sheet_config.get("header_row", 0),
        dtype=object,
    )

    columns = _resolve_columns(frame, sheet_config["columns"])
    order_col = columns["order_number"]

    if sheet_config.get("forward_fill_order", True):
        # Scan sheets usually carry the order on its first row only.
        frame[order_col] = frame[order_col].ffill()

    orders: Dict[str, WorkOrder] = {}

    for position, (index, row) in enumerate(frame.iterrows()):
        raw_order = row[order_col]
        if pd.isna(raw_order) or not str(raw_order).strip():
            continue

        try:
            order_number = normalise_order_number(raw_order)
        except ValueError:
            continue

        order = orders.get(order_number)
        if order is None:
            order = WorkOrder(order_number=order_number)
            orders[order_number] = order

        part_number = _cell(row, columns, "part_number")
        serial = _cell(row, columns, "serial")
        if part_number is None and serial is None:
            # A row that only repeats the order number carries no component.
            continue

        order.components.append(
            Component(
                part_number=part_number or "",
                serial=serial,
                quantity=_quantity(row, columns),
                component_type=_cell(row, columns, "component_type"),
                # +2: pandas is 0-based and the header consumed a row, so this
                # is the row number the kitter sees in Excel.
                source_row=int(position) + int(sheet_config.get("header_row", 0)) + 2,
            )
        )

    if not orders:
        raise KittingError(f"no work orders found in {path}")

    return list(orders.values())

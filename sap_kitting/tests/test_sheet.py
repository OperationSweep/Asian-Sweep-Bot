"""Tests for the parts that do not need SAP: order parsing and sheet grouping.

    python -m pytest tests/ -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kitting.models import KittingError, normalise_order_number
from kitting.sheet import read_workbook

COLUMNS = {
    "order_number": "Work Order",
    "part_number": "Material",
    "serial": "Serial Number",
    "quantity": "Qty",
    "component_type": "Type",
}
SHEET_CONFIG = {"sheet_name": None, "header_row": 0, "columns": COLUMNS,
                "forward_fill_order": True}


def write_sheet(tmp_path: Path, rows, columns=None) -> Path:
    frame = pd.DataFrame(rows, columns=columns or list(COLUMNS.values()))
    path = tmp_path / "scan.xlsx"
    frame.to_excel(path, index=False)
    return path


class TestOrderNumber:
    def test_strips_excel_float_suffix(self):
        assert normalise_order_number(12345678.0) == "12345678"

    def test_preserves_leading_zeros_in_text(self):
        assert normalise_order_number("000123") == "000123"

    def test_trims_whitespace(self):
        assert normalise_order_number("  4711  ") == "4711"

    @pytest.mark.parametrize("bad", [None, "", "   "])
    def test_rejects_empty(self, bad):
        with pytest.raises(ValueError):
            normalise_order_number(bad)


class TestReadWorkbook:
    def test_groups_components_under_forward_filled_order(self, tmp_path):
        path = write_sheet(tmp_path, [
            ("4500123456", "FLT-1", "SN1", 1, "optic filter"),
            ("",           "CPL-1", "SN2", 2, "coupler"),
            ("4500123457", "FLT-2", "SN3", 1, "optic filter"),
        ])
        orders = read_workbook(path, SHEET_CONFIG)

        assert [o.order_number for o in orders] == ["4500123456", "4500123457"]
        assert len(orders[0].components) == 2
        assert orders[0].total_quantity == 3

    def test_preserves_sheet_order(self, tmp_path):
        path = write_sheet(tmp_path, [
            ("4500000003", "A", "S1", 1, "coupler"),
            ("4500000001", "B", "S2", 1, "coupler"),
            ("4500000002", "C", "S3", 1, "coupler"),
        ])
        orders = read_workbook(path, SHEET_CONFIG)
        assert [o.order_number for o in orders] == [
            "4500000003", "4500000001", "4500000002"
        ]

    def test_reports_excel_row_numbers(self, tmp_path):
        path = write_sheet(tmp_path, [
            ("4500123456", "FLT-1", "SN1", 1, "optic filter"),
            ("",           "CPL-1", "SN2", 1, "coupler"),
        ])
        orders = read_workbook(path, SHEET_CONFIG)
        # Row 1 is the header, so the first component is on Excel row 2.
        assert [c.source_row for c in orders[0].components] == [2, 3]

    def test_defaults_missing_quantity_to_one(self, tmp_path):
        path = write_sheet(tmp_path, [("4500123456", "FLT-1", "SN1", None, "filter")])
        orders = read_workbook(path, SHEET_CONFIG)
        assert orders[0].components[0].quantity == 1.0

    def test_header_matching_ignores_case_and_padding(self, tmp_path):
        path = write_sheet(
            tmp_path,
            [("4500123456", "FLT-1", "SN1", 1, "filter")],
            columns=["  WORK ORDER ", "material", "Serial Number", "QTY", "type"],
        )
        assert read_workbook(path, SHEET_CONFIG)[0].order_number == "4500123456"

    def test_missing_order_column_is_fatal(self, tmp_path):
        path = write_sheet(
            tmp_path,
            [("FLT-1", "SN1")],
            columns=["Material", "Serial Number"],
        )
        with pytest.raises(KittingError, match="work-order column"):
            read_workbook(path, SHEET_CONFIG)

    def test_empty_sheet_is_fatal(self, tmp_path):
        path = write_sheet(tmp_path, [])
        with pytest.raises(KittingError, match="no work orders"):
            read_workbook(path, SHEET_CONFIG)

    def test_rows_without_components_do_not_create_empty_entries(self, tmp_path):
        path = write_sheet(tmp_path, [
            ("4500123456", None, None, None, None),
            ("",           "FLT-1", "SN1", 1, "filter"),
        ])
        orders = read_workbook(path, SHEET_CONFIG)
        assert len(orders) == 1
        assert len(orders[0].components) == 1

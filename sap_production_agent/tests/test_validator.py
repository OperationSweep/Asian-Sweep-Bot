"""Pre-flight validation."""

from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

import fixture as fx
from sap_agent.excel.reader import read_workbook
from sap_agent.excel.validator import preview, validate
from sap_agent.models import Severity


def edited(tmp_path, sample_path, changes):
    """Copy the fixture with specific cells overwritten."""
    workbook = openpyxl.load_workbook(sample_path)
    sheet = workbook.active
    for coordinate, value in changes.items():
        sheet[coordinate] = value
    target = tmp_path / "edited.xlsx"
    workbook.save(target)
    return read_workbook(target)


class TestCleanWorkbook:
    def test_passes_with_no_blockers(self, book):
        assert [a for a in validate(book) if a.severity is Severity.BLOCKER] == []

    def test_flags_the_short_orders_as_outliers(self, book):
        codes = [a.code for a in validate(book)]
        assert codes.count("SERIAL_COUNT_OUTLIER") == len(fx.ORDERS_WITHOUT_TRAY)

    def test_notes_the_non_material_row_label(self, book):
        infos = [a for a in validate(book) if a.code == "NON_MATERIAL_LABEL"]
        assert len(infos) == 1
        assert fx.TRAY_LABEL in infos[0].message

    def test_anomalies_come_back_worst_first(self, book):
        severities = [a.severity for a in validate(book)]
        assert severities == sorted(
            severities,
            key=lambda s: {Severity.BLOCKER: 0, Severity.WARNING: 1, Severity.INFO: 2}[s],
        )


class TestBlockers:
    def test_a_repeated_serial_blocks_the_run(self, tmp_path, sample_path, book):
        """A scan done twice would post one physical part to two orders."""
        first = book.jobs[0].serials[1]
        book2 = edited(tmp_path, sample_path, {f"C{first.sheet_row}": first.serial})
        codes = [a.code for a in validate(book2) if a.severity is Severity.BLOCKER]
        assert "DUPLICATE_SERIAL" in codes

    def test_a_repeated_work_order_blocks_the_run(self, tmp_path, sample_path):
        book2 = edited(tmp_path, sample_path, {"C2": int(fx.WORK_ORDERS[0])})
        codes = [a.code for a in validate(book2) if a.severity is Severity.BLOCKER]
        assert "DUPLICATE_WORK_ORDER" in codes

    def test_a_malformed_order_number_blocks_the_run(self, tmp_path, sample_path):
        book2 = edited(tmp_path, sample_path, {"C2": "NOT-AN-ORDER"})
        codes = [a.code for a in validate(book2) if a.severity is Severity.BLOCKER]
        assert "MALFORMED_WORK_ORDER" in codes

    def test_asking_for_more_pairs_than_exist_blocks_the_run(self, book):
        codes = [
            a.code for a in validate(book, expected_pairs=fx.COLUMNS + 10)
            if a.severity is Severity.BLOCKER
        ]
        assert "PAIR_COUNT_MISMATCH" in codes

    def test_asking_for_fewer_pairs_is_merely_noted(self, book):
        anomalies = validate(book, expected_pairs=12)
        assert [a for a in anomalies if a.severity is Severity.BLOCKER] == []
        assert any(a.code == "PARTIAL_BATCH" for a in anomalies)


class TestPreview:
    def test_shows_the_counts_and_the_range(self, book):
        text = preview(book, validate(book))
        assert f"Work orders detected: {fx.COLUMNS}" in text
        assert f"Serial numbers:       {fx.TOTAL_SERIALS}" in text
        assert f"First order: {fx.WORK_ORDERS[0]}" in text
        assert f"Last order:  {fx.LAST_ORDER}" in text
        assert "Ready to process." in text

    def test_limits_the_range_to_the_requested_pairs(self, book):
        text = preview(book, validate(book, 12), limit=12)
        assert f"Work orders detected: 12 (of {fx.COLUMNS} in sheet)" in text
        assert f"Last order:  {fx.WORK_ORDERS[11]}" in text

    def test_explains_the_expected_missing_serial_message(self, book):
        text = preview(book, validate(book))
        assert fx.NON_SERIALISED[0] in text
        assert "Serial Number missing" in text

    def test_says_not_ready_when_blocked(self, tmp_path, sample_path):
        book2 = edited(tmp_path, sample_path, {"C2": int(fx.WORK_ORDERS[0])})
        assert "NOT READY" in preview(book2, validate(book2))


class TestVolatileSources:
    def test_flags_work_orders_that_are_formulas(self, tmp_path):
        """The production sheet links rows 1-3 to another workbook."""
        source = tmp_path / "linked.xlsx"
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet["A2"] = "Work Order s/n"
        sheet["A3"] = "91AAA00301AAA"
        for index in range(3):
            column = chr(ord("B") + index)
            sheet[f"{column}2"] = f"=[1]Scan_SN!U{index + 5}"
            sheet[f"{column}3"] = f"SN{index:08d}"
        workbook.save(source)

        # openpyxl stores no cached value for a formula it wrote, so the reader
        # sees no work orders at all - which is itself the safe outcome.
        from sap_agent.models import KittingError

        with pytest.raises(KittingError) as caught:
            read_workbook(source)

        message = str(caught.value)
        assert "come from another workbook" in message
        assert "Scan_SN" in message or "cached value" in message
        assert "let\nthe links refresh" in message or "links refresh" in message

    def test_a_workbook_of_typed_values_is_not_flagged(self, book):
        assert [a for a in validate(book) if a.code == "COMPUTED_WORK_ORDERS"] == []

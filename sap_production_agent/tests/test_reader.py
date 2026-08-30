"""Reader tests: layout discovery, normalising, and anomaly detection.

Run against a generated fixture that reproduces the production sheet's shape -
see fixture.py for what is mirrored and why the real workbook is not committed.
"""

from __future__ import annotations

import pytest

import fixture as fx
from sap_agent.excel.reader import read_workbook
from sap_agent.models import KittingError, normalise_serial, normalise_work_order


class TestNormalising:
    def test_work_order_loses_excel_float_suffix(self):
        assert normalise_work_order(900000001.0) == "900000001"

    def test_work_order_keeps_leading_zeros_when_text(self):
        assert normalise_work_order("000123") == "000123"

    def test_work_order_trims_whitespace(self):
        assert normalise_work_order("  4711  ") == "4711"

    @pytest.mark.parametrize("bad", [None, "", "   "])
    def test_work_order_rejects_empty(self, bad):
        with pytest.raises(ValueError):
            normalise_work_order(bad)

    def test_zero_is_not_a_serial(self):
        """Row 3 uses a literal 0 for 'no amp tray fitted'."""
        assert normalise_serial(0) is None

    def test_blank_is_not_a_serial(self):
        assert normalise_serial(None) is None
        assert normalise_serial("   ") is None

    def test_a_numeric_serial_does_not_become_a_float(self):
        assert normalise_serial(12345) == "12345"


class TestLayoutDiscovery:
    def test_finds_every_work_order_column(self, book):
        assert len(book.jobs) == fx.COLUMNS

    def test_reads_the_work_orders_in_sheet_order(self, book):
        assert [job.work_order for job in book.jobs] == fx.WORK_ORDERS

    def test_carries_the_fibre_pair_label(self, book):
        assert book.jobs[0].fibre_pair == "M1/M2"
        assert book.jobs[-1].fibre_pair == "M47/M48"

    def test_records_the_column_letter(self, book):
        assert book.jobs[0].column_letter == "B"
        assert book.jobs[-1].column_letter == "Y"

    def test_numbers_the_columns_from_one(self, book):
        assert [job.column_index for job in book.jobs] == list(
            range(1, fx.COLUMNS + 1)
        )

    def test_missing_sheet_is_fatal(self, sample_path):
        with pytest.raises(KittingError, match="not in"):
            read_workbook(sample_path, sheet_name="NoSuchSheet")

    def test_missing_file_is_fatal(self, sample_path):
        with pytest.raises(KittingError, match="not found"):
            read_workbook(sample_path.with_name("nope.xlsx"))

    def test_an_unfindable_label_is_fatal(self, sample_path):
        with pytest.raises(KittingError, match="Could not find"):
            read_workbook(sample_path, work_order_label="no such label")


class TestSerials:
    def test_total_serial_count(self, book):
        assert sum(len(job.serials) for job in book.jobs) == fx.TOTAL_SERIALS

    def test_orders_with_an_amp_tray_carry_one_more(self, book):
        job = book.job(fx.ORDERS_WITH_TRAY[0])
        assert len(job.serials) == fx.SERIALS_WITH_TRAY

    def test_orders_without_an_amp_tray_carry_one_fewer(self, book):
        job = book.job(fx.ORDERS_WITHOUT_TRAY[0])
        assert len(job.serials) == fx.SERIALS_WITHOUT_TRAY

    def test_no_serial_is_the_string_zero(self, book):
        every = [s.serial for job in book.jobs for s in job.serials]
        assert "0" not in every

    def test_serials_keep_sheet_order(self, book):
        rows = [s.sheet_row for s in book.jobs[0].serials]
        assert rows == sorted(rows)

    def test_the_first_serial_is_the_amp_tray(self, book):
        assert book.jobs[0].serials[0].material == fx.TRAY_LABEL

    def test_serials_carry_their_material(self, book):
        job = book.jobs[0]
        assert all(component.material for component in job.serials)

    def test_serials_are_numbered_within_the_order(self, book):
        job = book.jobs[0]
        assert [c.sequence for c in job.serials] == list(range(1, len(job.serials) + 1))

    def test_no_duplicate_serials_anywhere(self, book):
        every = [s.serial for job in book.jobs for s in job.serials]
        assert len(every) == len(set(every))


class TestMaterialClassification:
    def test_splits_serialised_from_bulk(self, book):
        assert set(book.non_serialised_materials) == set(fx.NON_SERIALISED)
        assert set(fx.SERIALISED) <= set(book.serialised_materials)

    def test_the_tray_row_counts_as_serialised(self, book):
        assert fx.TRAY_LABEL in book.serialised_materials

    def test_no_material_is_in_both_lists(self, book):
        assert not set(book.serialised_materials) & set(book.non_serialised_materials)


class TestAnomalies:
    def test_no_blockers_in_a_clean_sheet(self, book):
        assert book.blockers == []

    def test_flags_the_stray_cell_below_the_block(self, book):
        stray = [a for a in book.all_anomalies if a.code == "STRAY_CELL"]
        assert len(stray) == 1
        assert stray[0].cell == fx.STRAY_CELL
        assert fx.STRAY_VALUE in stray[0].message

    def test_flags_each_missing_tray_serial(self, book):
        missing = [a for a in book.all_anomalies if a.code == "MISSING_SERIAL"]
        assert len(missing) == len(fx.ORDERS_WITHOUT_TRAY)

    def test_the_missing_serial_names_its_order(self, book):
        missing = [a for a in book.all_anomalies if a.code == "MISSING_SERIAL"]
        assert {a.work_order for a in missing} == set(fx.ORDERS_WITHOUT_TRAY)

    def test_bulk_materials_are_not_reported_as_missing(self, book):
        """Ten materials carry no serials by design - not 10 x 24 warnings."""
        missing = [a for a in book.all_anomalies if a.code == "MISSING_SERIAL"]
        assert all(
            not any(m in a.message for m in fx.NON_SERIALISED) for a in missing
        )


class TestJobShape:
    def test_to_dict_is_the_documented_shape(self, book):
        job = book.jobs[0].to_dict()
        assert set(job) == {"work_order", "fibre_pair", "serial_numbers"}
        assert job["work_order"] == fx.WORK_ORDERS[0]
        assert len(job["serial_numbers"]) == fx.SERIALS_WITH_TRAY

    def test_job_lookup_by_number(self, book):
        assert book.job(fx.WORK_ORDERS[3]).work_order == fx.WORK_ORDERS[3]

    def test_job_lookup_misses_cleanly(self, book):
        assert book.job("000000000") is None

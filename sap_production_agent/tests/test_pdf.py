"""Splitting and verifying the printed PDFs.

The mapping rule under test: a page belongs to the work order printed on it,
never to its position in the print job. A misordered rename would attach the
wrong paperwork to a shipment.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import fixture as fx
from pdf_fixtures import make_pdf

from sap_agent.models import KittingError
from sap_agent.printing import pdf_validator
from sap_agent.printing.pdf_writer import split_by_work_order, work_orders_in_pdf

ORDERS = fx.WORK_ORDERS[:3]
A, B, C = ORDERS


def combined(tmp_path, pages, padding=4):
    return make_pdf(tmp_path / "_combined.pdf", pages, padding=padding)


class TestSplitting:
    def test_one_page_per_order(self, tmp_path):
        source = combined(tmp_path, [f"Work Order {o}" for o in ORDERS])
        result = split_by_work_order(source, ORDERS, tmp_path, {})

        assert set(result.pdfs) == set(ORDERS)
        assert result.ok
        for order in ORDERS:
            assert result.pdfs[order].name == f"{order}.pdf"

    def test_multi_page_documents_stay_together(self, tmp_path):
        source = combined(tmp_path, [
            f"Work Order {A}", "continuation sheet",
            f"Work Order {B}", "continuation sheet",
        ])
        result = split_by_work_order(source, ORDERS[:2], tmp_path, {})

        from pypdf import PdfReader
        assert len(PdfReader(str(result.pdfs[A])).pages) == 2
        assert len(PdfReader(str(result.pdfs[B])).pages) == 2

    def test_pages_are_matched_by_content_not_order(self, tmp_path):
        """SAP emits them shuffled; the names must still be right."""
        source = combined(tmp_path, [
            f"Work Order {C}", f"Work Order {A}", f"Work Order {B}",
        ])
        result = split_by_work_order(source, ORDERS, tmp_path, {})

        assert work_orders_in_pdf(result.pdfs[C], ORDERS) == [C]
        assert work_orders_in_pdf(result.pdfs[A], ORDERS) == [A]

    def test_leading_zeros_in_the_document_still_match(self, tmp_path):
        source = combined(tmp_path, [f"Work Order 000{A}"])
        result = split_by_work_order(source, [A], tmp_path, {})
        assert A in result.pdfs

    def test_an_order_with_no_page_is_reported_missing(self, tmp_path):
        source = combined(tmp_path, [f"Work Order {A}"])
        result = split_by_work_order(source, ORDERS, tmp_path, {})

        assert result.missing_orders == [B, C]
        assert not result.ok

    def test_pages_before_any_order_are_reported_not_guessed(self, tmp_path):
        source = combined(tmp_path, ["cover sheet", f"Work Order {A}"])
        result = split_by_work_order(source, ORDERS[:1], tmp_path, {})

        assert result.unmatched_pages == [1]
        assert not result.ok

    def test_refuses_to_overwrite_by_default(self, tmp_path):
        (tmp_path / f"{A}.pdf").write_bytes(b"existing paperwork")
        source = combined(tmp_path, [f"Work Order {A}"])

        with pytest.raises(KittingError, match="already exists"):
            split_by_work_order(source, [A], tmp_path, {})

    def test_overwrites_when_told_to(self, tmp_path):
        (tmp_path / f"{A}.pdf").write_bytes(b"existing")
        source = combined(tmp_path, [f"Work Order {A}"])
        result = split_by_work_order(
            source, [A], tmp_path, {"overwrite": True}
        )
        assert result.pdfs[A].stat().st_size > 100


class TestVerification:
    def test_a_good_set_passes(self, tmp_path):
        pdfs = {
            order: make_pdf(tmp_path / f"{order}.pdf", [f"Work Order {order}"],
                            padding=140)
            for order in ORDERS
        }
        report = pdf_validator.verify(pdfs, ORDERS)
        assert report.ok, report.summary()

    def test_a_missing_file_fails(self, tmp_path):
        pdfs = {ORDERS[0]: tmp_path / "gone.pdf"}
        report = pdf_validator.verify(pdfs, ORDERS[:1])
        assert not report.ok
        assert "does not exist" in report.failures[0].problem

    def test_a_zero_byte_file_fails(self, tmp_path):
        empty = tmp_path / f"{A}.pdf"
        empty.write_bytes(b"")
        report = pdf_validator.verify({ORDERS[0]: empty}, ORDERS[:1])
        assert not report.ok
        assert "truncated" in report.failures[0].problem

    def test_a_file_naming_the_wrong_order_fails(self, tmp_path):
        """Named 294, but the content says 295 - the exact mix-up to catch."""
        wrong = make_pdf(tmp_path / f"{A}.pdf",
                         [f"Work Order {B}"], padding=140)
        report = pdf_validator.verify({A: wrong}, [A])
        assert not report.ok
        assert "wrong order" in report.failures[0].problem

    def test_an_order_with_no_pdf_is_listed_missing(self, tmp_path):
        good = make_pdf(tmp_path / f"{A}.pdf",
                        [f"Work Order {A}"], padding=140)
        report = pdf_validator.verify({A: good}, ORDERS)
        assert report.missing == [B, C]
        assert not report.ok

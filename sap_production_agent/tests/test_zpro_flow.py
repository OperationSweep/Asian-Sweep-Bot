"""ZPRO flow against a mock SAP session.

These assert the exact keystroke sequence that would reach production, and that
the safety checks refuse to post when the screen disagrees with the workbook.
"""

from __future__ import annotations

import pytest

import fixture as fx
from sap_agent.sap.controls import Controls
from sap_agent.sap.messages import MessageClass
from sap_agent.sap.mock import MockSession
from sap_agent.sap.zpro import ZproFlow

CONTROLS = Controls({
    "zpro": {
        "work_order_field": "wnd[0]/usr/ctxtP_AUFNR",
        "order_display_field": "wnd[0]/usr/txtCAUFVD-AUFNR",
        "execute_button": "wnd[0]/tbar[1]/btn[8]",
        "components_expand_button": "wnd[0]/usr/btnEXPAND",
        "serial_table": "wnd[0]/usr/tblCOMPONENTS",
        "serial_column": "7",
        "post_goods_issue_checkbox": "wnd[0]/usr/chkPGI",
        "post_button": "wnd[0]/tbar[1]/btn[11]",
        "confirm_button": "wnd[1]/tbar[0]/btn[0]",
    },
}, source="test")

WITH_TRAY = fx.ORDERS_WITH_TRAY[0]
WITHOUT_TRAY = fx.ORDERS_WITHOUT_TRAY[0]
A_BULK = fx.NON_SERIALISED[0]
A_SERIALISED = fx.SERIALISED[0]


def flow_for(session, book):
    return ZproFlow(session, CONTROLS, book, {"serial_first_row": 0})


class TestHappyPath:
    def test_posts_and_reports_the_document(self, book):
        session = MockSession(responses={
            WITH_TRAY: [("S", "Document 4900012345 posted")]
        })
        result = flow_for(session, book).post(book.job(WITH_TRAY))

        assert result.posted is True
        assert result.document == "4900012345"
        assert result.serials_written == fx.SERIALS_WITH_TRAY

    def test_writes_every_serial_in_sheet_order(self, book):
        session = MockSession()
        job = book.job(WITH_TRAY)
        flow_for(session, book).post(job)

        assert session.serials_written("7") == job.serial_numbers

    def test_the_keystroke_sequence_is_the_expected_one(self, book):
        session = MockSession()
        flow_for(session, book).post(book.job(WITH_TRAY))
        shape = session.actions

        assert shape[0] == "start /nZPRO"
        assert shape[1].startswith("set wnd[0]/usr/ctxtP_AUFNR")
        assert "press wnd[0]/tbar[1]/btn[8]" in shape
        assert "press wnd[0]/usr/btnEXPAND" in shape

        # Every cell is written before the checkbox is ticked, and Post is last.
        checkbox = shape.index("checkbox wnd[0]/usr/chkPGI = True")
        cells = [i for i, a in enumerate(shape) if a.startswith("cell[")]
        assert cells and max(cells) < checkbox
        assert shape.index("press wnd[0]/tbar[1]/btn[11]") > checkbox

    def test_an_order_without_a_tray_writes_one_fewer(self, book):
        session = MockSession()
        result = flow_for(session, book).post(book.job(WITHOUT_TRAY))

        assert result.serials_written == fx.SERIALS_WITHOUT_TRAY
        assert "0" not in session.serials_written("7")


class TestMessageHandling:
    def test_a_bulk_material_warning_still_counts_as_posted(self, book):
        session = MockSession(responses={
            WITH_TRAY: [("W", f"Serial Number missing for {A_BULK}")]
        })
        result = flow_for(session, book).post(book.job(WITH_TRAY))

        assert result.posted is True
        assert result.classification.message_class is MessageClass.EXPECTED_WARNING

    def test_a_serialised_material_warning_blocks_the_post(self, book):
        """SAP asking for a serial we sent means the entry did not land."""
        session = MockSession(responses={
            WITH_TRAY: [("W", f"Serial Number missing for {A_SERIALISED}")]
        })
        result = flow_for(session, book).post(book.job(WITH_TRAY))

        assert result.posted is False
        assert result.classification.message_class is MessageClass.CRITICAL_ERROR
        assert result.uncertain is False

    def test_an_unknown_message_is_left_uncertain(self, book):
        """Post was pressed; whether stock moved is unknown, so never auto-retry."""
        session = MockSession(responses={
            WITH_TRAY: [("W", "Some message nobody has seen")]
        })
        result = flow_for(session, book).post(book.job(WITH_TRAY))

        assert result.posted is False
        assert result.uncertain is True

    def test_a_lock_is_a_clean_failure(self, book):
        session = MockSession(responses={
            WITH_TRAY: [("E", "Order is locked by user SMITH")]
        })
        result = flow_for(session, book).post(book.job(WITH_TRAY))

        assert result.posted is False
        assert result.uncertain is False


class TestSafetyChecks:
    def test_refuses_when_the_screen_shows_another_order(self, book):
        session = MockSession()
        session.get_text = lambda element_id: "900999999"
        result = flow_for(session, book).post(book.job(WITH_TRAY))

        assert result.posted is False
        assert "refusing to post" in result.error
        assert not any(a.startswith("checkbox") for a in session.actions)

    def test_refuses_when_the_table_cannot_hold_the_serials(self, book):
        session = MockSession(table_rows=5)
        result = flow_for(session, book).post(book.job(WITH_TRAY))

        assert result.posted is False
        assert "only 5 rows" in result.error
        assert not any(a.startswith("checkbox") for a in session.actions)

    def test_a_missing_control_fails_the_order_not_the_batch(self, book):
        session = MockSession(missing_controls=["wnd[0]/usr/tblCOMPONENTS"])
        result = flow_for(session, book).post(book.job(WITH_TRAY))
        assert result.posted is False

    def test_an_exception_mid_post_does_not_raise(self, book):
        session = MockSession(fail_on={WITH_TRAY: "SAP GUI disconnected"})
        result = flow_for(session, book).post(book.job(WITH_TRAY))

        assert result.posted is False
        assert "disconnected" in result.error


class TestControls:
    def test_an_unset_control_says_how_to_find_it(self):
        controls = Controls({"zpro": {"work_order_field": None}}, source="controls.yaml")
        with pytest.raises(Exception, match="discover_controls"):
            controls.get("zpro.work_order_field")

    def test_missing_lists_every_unset_control(self):
        controls = Controls({"zpro": {"a": None, "b": "x"}, "co04": {"c": None}})
        assert controls.missing() == ["co04.c", "zpro.a"]

    def test_optional_returns_the_default_when_unset(self):
        assert Controls({"zpro": {"a": None}}).optional("zpro.a", "fb") == "fb"

    def test_permissive_mode_yields_a_placeholder_for_dry_runs(self):
        controls = Controls({"zpro": {"a": None}}, permissive=True)
        assert controls.get("zpro.a") == "<UNSET zpro.a>"

    def test_permissive_optional_still_returns_the_default(self):
        controls = Controls({"zpro": {"a": None}}, permissive=True)
        assert controls.optional("zpro.a") is None

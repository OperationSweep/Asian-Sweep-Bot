"""CO04 reprint flow.

The screen is standard SAP ("Print Shop Papers: Initial Screen") and keeps
whatever was entered last, so these cover the stale-criteria problem as much as
the happy path.
"""

from __future__ import annotations

import pytest

import fixture as fx
from sap_agent.sap.co04 import Co04Flow
from sap_agent.sap.controls import Controls
from sap_agent.sap.mock import MockSession

CLEAR = [
    "wnd[0]/usr/ctxtMRP_CONTROLLER",
    "wnd[0]/usr/ctxtORDER_TYPE",
    "wnd[0]/usr/ctxtMATERIAL",
    "wnd[0]/usr/ctxtSCHED_START_LOW",
]

CONTROLS = Controls({
    "co04": {
        "reprint_radio": "wnd[0]/usr/radREPRINT",
        "print_mode_field": None,
        "plant_field": "wnd[0]/usr/ctxtPLANT",
        "order_from_field": "wnd[0]/usr/ctxtORDER_LOW",
        "order_to_field": "wnd[0]/usr/ctxtORDER_HIGH",
        "clear_fields": CLEAR,
        "execute_button": "wnd[0]/tbar[1]/btn[8]",
        "select_all_button": "wnd[0]/tbar[1]/btn[9]",
        "results_table": "wnd[0]/usr/tblRESULTS",
        "print_button": "wnd[0]/tbar[1]/btn[11]",
        "print_dialog_confirm": "wnd[1]/tbar[0]/btn[0]",
    },
}, source="test")

FIRST, LAST = fx.BLOCK_B[0], fx.BLOCK_B[-1]
COUNT = len(fx.BLOCK_B)


def flow_for(session, **config):
    settings = {"plant": "8000"}
    settings.update(config)
    return Co04Flow(session, CONTROLS, settings)


class TestSelection:
    def test_prints_the_requested_range(self):
        session = MockSession(table_rows=COUNT)
        result = flow_for(session).reprint(FIRST, LAST, COUNT)

        assert result.printed is True
        assert result.error == ""
        assert f"set wnd[0]/usr/ctxtORDER_LOW = '{FIRST}'" in session.actions
        assert f"set wnd[0]/usr/ctxtORDER_HIGH = '{LAST}'" in session.actions

    def test_selects_the_reprint_radio(self):
        session = MockSession(table_rows=COUNT)
        flow_for(session).reprint(FIRST, LAST, COUNT)
        assert "select wnd[0]/usr/radREPRINT" in session.actions

    def test_sets_the_plant(self):
        session = MockSession(table_rows=COUNT)
        flow_for(session).reprint(FIRST, LAST, COUNT)
        assert "set wnd[0]/usr/ctxtPLANT = '8000'" in session.actions

    def test_opens_co04(self):
        session = MockSession(table_rows=COUNT)
        flow_for(session).reprint(FIRST, LAST, COUNT)
        assert session.actions[0] == "start /nCO04"


class TestStaleCriteria:
    """The screen retains the previous run's entries."""

    def test_clears_every_configured_field(self):
        session = MockSession(table_rows=COUNT)
        flow_for(session).reprint(FIRST, LAST, COUNT)

        for element_id in CLEAR:
            assert f"set {element_id} = ''" in session.actions

    def test_clears_before_setting_the_range(self):
        """Clearing afterwards would wipe the range we just typed."""
        session = MockSession(table_rows=COUNT)
        flow_for(session).reprint(FIRST, LAST, COUNT)

        last_clear = max(
            session.actions.index(f"set {e} = ''") for e in CLEAR
        )
        order_set = session.actions.index(
            f"set wnd[0]/usr/ctxtORDER_LOW = '{FIRST}'"
        )
        assert last_clear < order_set

    def test_a_field_absent_from_this_system_is_skipped(self):
        session = MockSession(missing_controls=[CLEAR[1]])
        session.table_rows = COUNT
        result = flow_for(session).reprint(FIRST, LAST, COUNT)
        assert result.printed is True

    def test_nothing_is_cleared_when_none_configured(self):
        controls = Controls({"co04": dict(CONTROLS._data["co04"], clear_fields=[])})
        session = MockSession(table_rows=COUNT)
        Co04Flow(session, controls, {"plant": "8000"}).reprint(FIRST, LAST, COUNT)
        assert not any(a.endswith("= ''") for a in session.actions)


class TestCountVerification:
    def test_refuses_to_print_the_wrong_number_of_documents(self):
        session = MockSession(table_rows=COUNT + 5)
        result = flow_for(session).reprint(FIRST, LAST, COUNT)

        assert result.printed is False
        assert "returned" in result.error
        assert "press wnd[0]/tbar[1]/btn[11]" not in session.actions

    def test_prints_when_the_count_matches(self):
        session = MockSession(table_rows=COUNT)
        result = flow_for(session).reprint(FIRST, LAST, COUNT)

        assert result.printed is True
        assert result.selected_count == COUNT
        assert "press wnd[0]/tbar[1]/btn[11]" in session.actions

    def test_selects_all_before_printing(self):
        session = MockSession(table_rows=COUNT)
        flow_for(session).reprint(FIRST, LAST, COUNT)

        assert session.actions.index("press wnd[0]/tbar[1]/btn[9]") < \
            session.actions.index("press wnd[0]/tbar[1]/btn[11]")


class TestGaps:
    def test_refuses_a_range_containing_unposted_orders(self):
        """Belt and braces: the orchestrator splits into blocks first."""
        session = MockSession(table_rows=COUNT)
        result = flow_for(session).reprint(
            FIRST, LAST, COUNT, unposted_in_range=[fx.BLOCK_B[3]]
        )

        assert result.printed is False
        assert fx.BLOCK_B[3] in result.error
        assert session.actions == []


class TestFallbacks:
    def test_sends_f8_when_no_execute_button_is_configured(self):
        controls = Controls({
            "co04": dict(CONTROLS._data["co04"], execute_button=None)
        })
        session = MockSession(table_rows=COUNT)
        Co04Flow(session, controls, {"plant": "8000"}).reprint(FIRST, LAST, COUNT)

        assert "vkey 8 -> wnd[0]" in session.actions

    def test_skips_count_check_when_no_results_table_is_configured(self):
        controls = Controls({
            "co04": dict(CONTROLS._data["co04"], results_table=None)
        })
        session = MockSession(table_rows=COUNT + 5)
        result = Co04Flow(session, controls, {"plant": "8000"}).reprint(
            FIRST, LAST, COUNT
        )
        assert result.printed is True

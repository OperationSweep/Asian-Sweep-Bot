"""End-to-end batch behaviour against a mock SAP session."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import fixture as fx
from sap_agent.sap.controls import Controls
from sap_agent.sap.mock import MockSession
from sap_agent.workflow.orchestrator import Orchestrator
from sap_agent.workflow.state import OrderState, RunState

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

WO = fx.WORK_ORDERS
A_BULK = fx.NON_SERIALISED[0]
A_SERIALISED = fx.SERIALISED[0]


def build(tmp_path, session):
    return Orchestrator(
        config={
            "logs_dir": str(tmp_path / "logs"),
            "state_dir": str(tmp_path),
            "zpro": {"serial_first_row": 0},
            "run": {"max_retries": 1},
        },
        session=session,
        controls=CONTROLS,
        state_path=tmp_path / "state.json",
    )


def run(tmp_path, session, sample_path, limit=3, resume=False):
    return build(tmp_path, session).run(
        sample_path, limit=limit, do_zpro=True, do_print=False, resume=resume
    )


class TestBatch:
    def test_posts_every_order_it_was_given(self, tmp_path, sample_path):
        report = run(tmp_path, MockSession(), sample_path, limit=4)

        assert not report.halted
        assert len(report.state.posted) == 4
        assert report.state.print_range() == (WO[0], WO[3])

    def test_stops_the_batch_on_a_critical_message(self, tmp_path, sample_path):
        session = MockSession(responses={
            WO[2]: [("W", f"Serial Number missing for {A_SERIALISED}")],
        })
        report = run(tmp_path, session, sample_path, limit=5)

        assert report.halted
        assert report.state.posted == WO[:2]
        assert report.state.orders[WO[2]].state is OrderState.FAILED
        # Orders after the failure were never attempted.
        assert report.state.orders[WO[3]].state is OrderState.PENDING

    def test_carries_on_past_an_expected_warning(self, tmp_path, sample_path):
        session = MockSession(responses={
            WO[1]: [("W", f"Serial Number missing for {A_BULK}")],
        })
        report = run(tmp_path, session, sample_path, limit=3)

        assert not report.halted
        assert len(report.state.posted) == 3
        assert report.state.orders[WO[1]].message_class == "EXPECTED_WARNING"

    def test_an_unknown_message_halts_without_a_model(self, tmp_path, sample_path):
        session = MockSession(responses={WO[1]: [("W", "Never seen this one")]})
        report = run(tmp_path, session, sample_path, limit=3)

        assert report.halted
        assert report.state.orders[WO[1]].state is OrderState.UNCERTAIN

    def test_a_lock_is_retried_then_halts(self, tmp_path, sample_path):
        session = MockSession(responses={
            WO[1]: [("E", "Order is locked by user SMITH")],
        })
        report = run(tmp_path, session, sample_path, limit=3)

        assert report.halted
        assert report.state.orders[WO[1]].state is OrderState.FAILED
        assert report.state.orders[WO[1]].attempts == 2  # one retry


class TestIdempotency:
    def test_a_resumed_run_does_not_repost(self, tmp_path, sample_path):
        first = run(tmp_path, MockSession(), sample_path, limit=3)
        assert len(first.state.posted) == 3

        second_session = MockSession()
        second = run(tmp_path, second_session, sample_path, limit=3, resume=True)

        assert len(second.state.posted) == 3
        # Nothing was keyed into SAP the second time round.
        assert not any(a.startswith("checkbox") for a in second_session.actions)

    def test_resuming_a_changed_workbook_is_refused(self, tmp_path, sample_path):
        copy = tmp_path / "book.xlsx"
        shutil.copy(sample_path, copy)
        run(tmp_path, MockSession(), copy, limit=2)

        copy.write_bytes(copy.read_bytes() + b"\0")
        with pytest.raises(Exception, match="has changed"):
            run(tmp_path, MockSession(), copy, limit=2, resume=True)

    def test_resume_completes_the_orders_that_failed(self, tmp_path, sample_path):
        failing = MockSession(responses={
            WO[2]: [("E", "Order is locked by user SMITH")],
        })
        first = run(tmp_path, failing, sample_path, limit=4)
        assert first.halted
        assert len(first.state.posted) == 2

        second = run(tmp_path, MockSession(), sample_path, limit=4, resume=True)
        assert not second.halted
        assert len(second.state.posted) == 4

    def test_an_uncertain_order_is_not_reposted_on_resume(self, tmp_path, sample_path):
        """Post was pressed with no clear answer - a human must check SAP."""
        session = MockSession(responses={WO[1]: [("W", "Mystery reply")]})
        run(tmp_path, session, sample_path, limit=3)

        second_session = MockSession()
        second = run(tmp_path, second_session, sample_path, limit=3, resume=True)

        assert second.state.orders[WO[1]].state is OrderState.UNCERTAIN
        assert WO[1] not in second.state.posted


class TestAudit:
    def test_writes_a_csv_and_a_jsonl(self, tmp_path, sample_path):
        report = run(tmp_path, MockSession(), sample_path, limit=2)
        logs = tmp_path / "logs"
        assert (logs / f"run_{report.state.run_id}.csv").exists()
        assert (logs / f"run_{report.state.run_id}.jsonl").exists()

    def test_records_the_serials_that_were_posted(self, tmp_path, sample_path, book):
        report = run(tmp_path, MockSession(), sample_path, limit=1)
        text = (tmp_path / "logs" / f"run_{report.state.run_id}.csv").read_text()

        assert book.jobs[0].serials[0].serial in text
        assert "order_posted" in text

    def test_records_preflight_anomalies(self, tmp_path, sample_path):
        report = run(tmp_path, MockSession(), sample_path, limit=3)
        text = (tmp_path / "logs" / f"run_{report.state.run_id}.csv").read_text()
        assert "preflight_anomaly" in text

    def test_never_writes_a_password(self, tmp_path, sample_path):
        from sap_agent.audit.log import AuditLog

        log = AuditLog(directory=tmp_path / "logs", run_id="test")
        row = log.record("login", sap_password="hunter2", work_order=WO[0])

        assert "sap_password" not in row
        assert "hunter2" not in (tmp_path / "logs" / "run_test.csv").read_text()

    def test_state_survives_on_disk(self, tmp_path, sample_path):
        run(tmp_path, MockSession(), sample_path, limit=2)
        reloaded = RunState.load(tmp_path / "state.json")
        assert len(reloaded.posted) == 2


class TestSummary:
    def test_summary_reports_the_range_and_outcome(self, tmp_path, sample_path):
        report = run(tmp_path, MockSession(), sample_path, limit=3)
        text = report.summary()

        assert "PRODUCTION AUTOMATION COMPLETE" in text
        assert "Successful:   3" in text
        assert f"First order:  {WO[0]}" in text
        assert f"Last order:   {WO[2]}" in text

    def test_summary_says_halted_and_why(self, tmp_path, sample_path):
        session = MockSession(responses={
            WO[1]: [("W", f"Serial Number missing for {A_SERIALISED}")],
        })
        report = run(tmp_path, session, sample_path, limit=3)

        assert "HALTED" in report.summary()
        assert "did not land" in report.summary()

"""Run state: idempotency, resume, and the CO04 range."""

from __future__ import annotations

import pytest

import fixture as fx
from sap_agent.workflow.state import OrderState, Phase, RunState, fingerprint

WO = fx.BLOCK_B          # a contiguous run
ALL = fx.WORK_ORDERS     # the full batch, which spans two blocks


@pytest.fixture
def state(tmp_path):
    run = RunState(dry_run=False).bind(tmp_path / "state.json")
    for work_order in WO[:6]:
        run.register(work_order, serial_count=21)
    return run


class TestIdempotency:
    def test_a_fresh_order_may_post(self, state):
        assert state.may_post(WO[0])[0] is True

    def test_a_posted_order_may_not_post_again(self, state):
        state.begin(WO[0])
        state.finish(WO[0], OrderState.POSTED)
        allowed, why = state.may_post(WO[0])
        assert allowed is False
        assert "already posted" in why

    def test_a_failed_order_may_be_retried(self, state):
        state.begin(WO[0])
        state.finish(WO[0], OrderState.FAILED, error="boom")
        assert state.may_post(WO[0])[0] is True

    def test_an_uncertain_order_is_never_retried_automatically(self, state):
        """Post was pressed but SAP did not confirm - a human must check."""
        state.begin(WO[0])
        state.finish(WO[0], OrderState.UNCERTAIN)
        allowed, why = state.may_post(WO[0])
        assert allowed is False
        assert "uncertain" in why

    def test_an_interrupted_order_is_not_silently_retried(self, state):
        state.begin(WO[0])  # left IN_PROGRESS by a crash
        allowed, why = state.may_post(WO[0])
        assert allowed is False
        assert "in progress" in why

    def test_an_unknown_order_may_not_post(self, state):
        assert state.may_post("999999999")[0] is False

    def test_attempts_are_counted(self, state):
        state.begin(WO[0])
        state.finish(WO[0], OrderState.FAILED)
        state.begin(WO[0])
        assert state.orders[WO[0]].attempts == 2


class TestPersistence:
    def test_round_trips_through_disk(self, tmp_path, state):
        state.begin(WO[0])
        state.finish(WO[0], OrderState.POSTED, document="4900012345")
        state.save()

        reloaded = RunState.load(tmp_path / "state.json")
        assert reloaded.run_id == state.run_id
        assert reloaded.orders[WO[0]].state is OrderState.POSTED
        assert reloaded.orders[WO[0]].document == "4900012345"

    def test_posted_orders_survive_a_reload(self, tmp_path, state):
        state.begin(WO[0])
        state.finish(WO[0], OrderState.POSTED)
        reloaded = RunState.load(tmp_path / "state.json")
        assert reloaded.may_post(WO[0])[0] is False

    def test_registering_again_keeps_existing_state(self, state):
        state.begin(WO[0])
        state.finish(WO[0], OrderState.POSTED)
        state.register(WO[0], serial_count=21)
        assert state.orders[WO[0]].state is OrderState.POSTED

    def test_fingerprint_detects_a_changed_workbook(self, tmp_path):
        path = tmp_path / "book.xlsx"
        path.write_bytes(b"original")
        before = fingerprint(path)
        path.write_bytes(b"edited")
        assert fingerprint(path) != before


class TestPrintRange:
    def _post(self, state, *orders):
        for order in orders:
            state.begin(order)
            state.finish(order, OrderState.POSTED)

    def test_range_spans_the_posted_orders(self, state):
        self._post(state, WO[0], WO[1], WO[2])
        assert state.print_range() == (WO[0], WO[2])

    def test_range_ignores_failed_orders(self, state):
        self._post(state, WO[0], WO[1])
        state.begin(WO[2])
        state.finish(WO[2], OrderState.FAILED)
        assert state.print_range() == (WO[0], WO[1])

    def test_range_is_numeric_not_lexicographic(self, state):
        state.register("99999999", 1)
        state.register("100000000", 1)
        self._post(state, "99999999", "100000000")
        assert state.print_range() == ("99999999", "100000000")

    def test_no_posted_orders_has_no_range(self, state):
        with pytest.raises(ValueError, match="no orders"):
            state.print_range()

    def test_contiguous_run_is_detected(self, state):
        self._post(state, WO[0], WO[1], WO[2])
        assert state.contiguous_range() is True
        assert state.unposted_in_range() == []
        assert state.contiguous_blocks() == [(WO[0], WO[2])]

    def test_a_gap_is_detected(self, state):
        """CO04 prints by range, so a hole would reprint an unposted order."""
        self._post(state, WO[0], WO[2])
        assert state.contiguous_range() is False
        assert state.unposted_in_range() == [WO[1]]


class TestContiguousBlocks:
    """Real batches span more than one order series."""

    def _post_all(self, tmp_path, orders):
        state = RunState(dry_run=False).bind(tmp_path / "blocks.json")
        for work_order in orders:
            state.register(work_order, 21)
            state.begin(work_order)
            state.finish(work_order, OrderState.POSTED)
        return state

    def test_a_two_series_batch_splits_into_two_blocks(self, tmp_path):
        state = self._post_all(tmp_path, ALL)
        assert state.contiguous_blocks() == fx.BLOCKS

    def test_a_gap_becomes_a_block_boundary(self, tmp_path):
        state = self._post_all(tmp_path, [WO[0], WO[1], WO[3], WO[4]])
        assert state.contiguous_blocks() == [(WO[0], WO[1]), (WO[3], WO[4])]

    def test_each_block_reports_only_its_own_orders(self, tmp_path):
        state = self._post_all(tmp_path, ALL)
        first, last = state.contiguous_blocks()[1]
        assert state.orders_in_block(first, last) == list(fx.BLOCK_B)

    def test_blocks_cover_every_posted_order_exactly_once(self, tmp_path):
        state = self._post_all(tmp_path, ALL)
        covered = [
            w for first, last in state.contiguous_blocks()
            for w in state.orders_in_block(first, last)
        ]
        assert sorted(covered) == sorted(ALL)

    def test_one_order_is_a_block_of_one(self, tmp_path):
        state = self._post_all(tmp_path, [WO[0]])
        assert state.contiguous_blocks() == [(WO[0], WO[0])]

    def test_nothing_posted_means_no_blocks(self, tmp_path):
        state = self._post_all(tmp_path, [])
        assert state.contiguous_blocks() == []


class TestPhases:
    def test_halting_records_the_reason(self, state):
        state.halt("CO04 returned the wrong document count")
        assert state.phase is Phase.HALTED
        assert "CO04" in state.halt_reason

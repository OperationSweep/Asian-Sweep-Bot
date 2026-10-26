import gzip
import json

from arb.xemm_sim import XEMM, Params, replay, walk


def book(bid, ask, t, bq=10.0, aq=10.0):
    return {"bids": [[bid, bq], [bid - 1, 50.0]], "asks": [[ask, aq], [ask + 1, 50.0]],
            "recv_ms": t, "exch_ms": t}


def make(model, **kw):
    p = Params("m", "h", "X/USDT", model, maker_fee=0.0, hedge_fee=0.0, edge_bps=0.0,
               quote_usd=100.0, refresh_bps=1000, place_latency_ms=0, hedge_latency_ms=0, **kw)
    return XEMM(p)


def test_walk_respects_limit():
    got, quote = walk([[100, 1], [99, 1], [98, 1]], 3, 99, False)
    assert got == 2 and quote == 199


def test_touch_is_not_a_fill_in_realistic_model():
    s = make("realistic")
    s.step(0, book(99, 101, 0), book(100, 100.5, 0))   # hedge bid 100 -> maker bid 100 (crosses? no: < 101)
    q = s.quotes["buy"]
    assert q is not None and q.price == 100
    s.on_trade(10, 100.0, 0.5, "buy")       # buy aggressor cannot hit our bid
    s.on_trade(11, 100.5, 5.0, "sell")      # above our bid: no fill
    assert s.stats["fills"] == 0


def test_queue_ahead_is_consumed_first():
    s = make("realistic")
    s.step(0, book(100, 101, 0, bq=3.0), book(100, 100.5, 0))   # we join a level with 3 ahead
    q = s.quotes["buy"]
    assert q.queue_ahead == 3.0
    s.on_trade(10, 100.0, 2.5, "sell")
    assert s.stats["fills"] == 0 and abs(q.queue_ahead - 0.5) < 1e-9
    s.on_trade(11, 100.0, 1.0, "sell")      # 0.5 queue left, 0.5 fills us
    assert abs((q.qty - q.remaining) - 0.5) < 1e-9


def test_optimistic_fills_whole_quote_on_touch():
    s = make("optimistic")
    s.step(0, book(99, 101, 0), book(100, 100.5, 0))
    s.on_trade(10, 100.0, 0.001, "sell")
    assert s.stats["fills"] == 1 and s.quotes["buy"].remaining == 0


def test_conservative_needs_trade_through():
    s = make("conservative")
    s.step(0, book(99, 101, 0), book(100, 100.5, 0))
    s.on_trade(10, 100.0, 5.0, "sell")
    assert s.stats["fills"] == 0
    s.on_trade(11, 99.5, 0.4, "sell")
    assert s.stats["fills"] == 1


def test_fill_while_cancel_in_flight_is_still_hedged():
    s = make("realistic", cancel_latency_ms=500)
    s.step(0, book(99, 101, 0), book(100, 100.5, 0))
    s.cancel("buy", 100)                    # cancel sent at 100, effective at 600
    s.on_trade(300, 99.0, 10.0, "sell")     # fills before the cancel lands
    assert s.stats["fills_after_cancel_sent"] == 1
    s.step(400, book(99, 101, 400), book(100, 100.5, 400))
    assert s.stats["cycles"] == 1 and not s.hedges


def test_cycle_pnl_counts_fees_and_failed_hedge_flattens():
    p = Params("m", "h", "X/USDT", "realistic", maker_fee=0.001, hedge_fee=0.001, edge_bps=0.0,
               quote_usd=100.0, refresh_bps=1000, place_latency_ms=0, hedge_latency_ms=0,
               hedge_timeout_ms=1000, hedge_slip_bps=1.0)
    s = XEMM(p)
    s.step(0, book(99.5, 101, 0), book(100, 100.5, 0))
    bid = s.quotes["buy"].price
    s.on_trade(10, bid - 0.01, 10.0, "sell")
    # Hedge book collapses 5 % below the IOC limit: nothing hedges until the timeout.
    s.step(500, book(99.5, 101, 500), book(95, 95.5, 500))
    assert s.stats["cycles"] == 0 and s.hedges
    s.step(1500, book(99.5, 101, 1500), book(95, 95.5, 1500))
    assert s.stats["failed_hedges"] == 1 and s.stats["cycles"] == 1
    assert s.cycle_pnl[0][1] < -4.0         # ~5 % of $100 lost, plus fees


def test_replay_end_to_end(tmp_path):
    bp, tp = tmp_path / "b.jsonl.gz", tmp_path / "t.jsonl.gz"
    with gzip.open(bp, "wt") as fh:
        for t in range(0, 3000, 250):
            fh.write(json.dumps({"t": t, "books": {"m": {"X/USDT": book(99, 101, t)},
                                                  "h": {"X/USDT": book(100, 100.5, t)}}}) + "\n")
    with gzip.open(tp, "wt") as fh:
        fh.write(json.dumps(["m", "X/USDT", 900, 1000, 99.0, 5.0, "sell", "1"]) + "\n")
    p = Params("m", "h", "X/USDT", "realistic", edge_bps=0.0, place_latency_ms=0, hedge_latency_ms=0)
    sims = replay(str(bp), str(tp), [p])
    r = sims[0].summary(None)
    assert r["fills"] == 1 and r["cycles"] == 1 and abs(r["net_pnl_usd"]) < 1e-6   # zero edge, zero fees

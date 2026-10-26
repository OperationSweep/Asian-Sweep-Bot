import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from arb.book_math import (buy_with_quote, sell_base, cross_venue, max_profitable_cross,
                           convert, cycle_return)


ASKS = [[100.0, 1.0], [101.0, 2.0], [102.0, 5.0]]
BIDS = [[103.0, 0.5], [102.5, 1.0], [99.0, 10.0]]


def test_buy_with_quote_walks_levels():
    base, spent = buy_with_quote(ASKS, 302.0)
    assert math.isclose(spent, 302.0)
    assert math.isclose(base, 1.0 + 202.0 / 101.0)


def test_sell_base_walks_levels():
    received, sold = sell_base(BIDS, 1.0)
    assert math.isclose(sold, 1.0)
    assert math.isclose(received, 0.5 * 103.0 + 0.5 * 102.5)


def test_cross_venue_fees_turn_gross_profit_negative():
    # 1 % gross gap, 0.6 % taker each side -> loss.
    asks = [[100.0, 10.0]]
    bids = [[101.0, 10.0]]
    gross = cross_venue(asks, bids, 500.0, 0.0, 0.0)
    assert gross.net > 0
    net = cross_venue(asks, bids, 500.0, 0.006, 0.006)
    assert net.net < 0


def test_cross_venue_thin_sell_book_is_partial():
    asks = [[100.0, 10.0]]
    bids = [[101.0, 1.0]]
    r = cross_venue(asks, bids, 500.0, 0.0, 0.0)
    assert not r.complete
    assert math.isclose(r.base_qty, 1.0)
    assert math.isclose(r.net, 1.0)


def test_max_profitable_cross_stops_at_marginal_breakeven():
    qty, net = max_profitable_cross(ASKS, BIDS, 0.0, 0.0)
    # 0.5 @ (103-100) + 0.5 @ (102.5-100) + 0.5 @ (102.5-101), then bid 99 < ask 101 stops
    assert math.isclose(qty, 1.5)
    assert math.isclose(net, 1.5 + 1.25 + 0.75)


def test_triangle_cycle_round_trip_flat_market_loses_fees():
    books = {
        "BTC/USDT": {"asks": [[50000.0, 1.0]], "bids": [[50000.0, 1.0]]},
        "ETH/BTC": {"asks": [[0.05, 100.0]], "bids": [[0.05, 100.0]]},
        "ETH/USDT": {"asks": [[2500.0, 100.0]], "bids": [[2500.0, 100.0]]},
    }
    assert math.isclose(cycle_return(books, ["USDT", "BTC", "ETH"], 1000.0, 0.0), 0.0, abs_tol=1e-9)
    r = cycle_return(books, ["USDT", "BTC", "ETH"], 1000.0, 0.001)
    assert math.isclose(r, 1000.0 * (0.999 ** 3) - 1000.0)


def test_convert_missing_market_returns_none():
    assert convert({}, 1.0, "USDT", "BTC", 0.0) is None

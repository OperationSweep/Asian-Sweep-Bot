"""
Order-flow analysis for the Asian Session Liquidity Sweep bot.

The sweep + Break-of-Structure logic decides *where* price is; order flow tells
us *who is actually transacting there*. This module reads live market
microstructure from MetaTrader5 and produces a directional confirmation signal
that gates entries after a BOS:

    * Tape / aggressor delta   - net buy vs sell pressure inferred from the
                                 recent tick stream (uptick/downtick rule).
    * Depth-of-market imbalance - resting bid vs ask liquidity from the DOM.

An entry is only allowed when the order flow *agrees* with the intended trade
direction (buying pressure for a BUY, selling pressure for a SELL). This filters
out structure breaks that happen on thin or opposing flow.

The heavy lifting (`evaluate_order_flow`) needs a live MT5 terminal, but the
decision logic is factored into pure functions (`classify_ticks`,
`book_imbalance`, `decide`) that are unit-testable without a broker connection.
Run ``python orderflow.py`` for a self-contained demo of that logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Sequence

import numpy as np
import pandas as pd
import pytz

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - MetaTrader5 is platform specific
    mt5 = None  # type: ignore[assignment]

import config

# Child of the bot's logger so records flow to the same file/stream handlers.
log = logging.getLogger("AsianSweepBot.orderflow")

UTC = pytz.UTC


# --------------------------------------------------------------------------- #
# Metric containers
# --------------------------------------------------------------------------- #
@dataclass
class TapeMetrics:
    """Aggressor-classified summary of the recent tick stream."""

    n_ticks: int = 0
    buy_vol: float = 0.0
    sell_vol: float = 0.0

    @property
    def total_vol(self) -> float:
        return self.buy_vol + self.sell_vol

    @property
    def delta(self) -> float:
        """Net aggressive volume (positive = buyers lifting offers)."""
        return self.buy_vol - self.sell_vol

    @property
    def delta_ratio(self) -> float:
        """Delta normalised to [-1, 1] so thresholds are regime-independent."""
        total = self.total_vol
        if total <= 0:
            return 0.0
        return self.delta / total


@dataclass
class BookMetrics:
    """Depth-of-market (resting limit-order) summary."""

    available: bool = False
    levels: int = 0
    bid_vol: float = 0.0
    ask_vol: float = 0.0

    @property
    def imbalance(self) -> float:
        """(bid - ask) / (bid + ask); positive = resting demand outweighs supply."""
        total = self.bid_vol + self.ask_vol
        if total <= 0:
            return 0.0
        return (self.bid_vol - self.ask_vol) / total


@dataclass
class OrderFlowSignal:
    """Outcome of an order-flow evaluation for one intended direction."""

    direction: str                       # BUY | SELL
    agrees: bool
    reason: str
    tape: TapeMetrics
    book: BookMetrics

    def summary(self) -> str:
        parts = [
            f"dir={self.direction}",
            f"delta={self.tape.delta:+.0f}",
            f"delta_ratio={self.tape.delta_ratio:+.2f}",
            f"ticks={self.tape.n_ticks}",
        ]
        if self.book.available:
            parts.append(f"book_imb={self.book.imbalance:+.2f}")
        else:
            parts.append("book=n/a")
        parts.append(self.reason)
        return " ".join(parts)


# --------------------------------------------------------------------------- #
# Pure logic (no MT5 required) - unit testable
# --------------------------------------------------------------------------- #
def classify_ticks(df: Optional[pd.DataFrame]) -> TapeMetrics:
    """Classify each tick as buy- or sell-initiated using the tick rule.

    FX feeds rarely carry a genuine aggressor flag, so we infer direction from
    price movement: an uptick is buyer-initiated, a downtick seller-initiated,
    and an unchanged tick inherits the previous direction. Trade price is
    ``last`` when present, otherwise the bid/ask mid. Size uses ``volume_real``
    / ``volume`` when the feed provides it, falling back to one unit per tick
    (tick count as a volume proxy).
    """
    if df is None or len(df) == 0:
        return TapeMetrics()

    n = len(df)
    bid = df["bid"].to_numpy(dtype=float) if "bid" in df else np.zeros(n)
    ask = df["ask"].to_numpy(dtype=float) if "ask" in df else np.zeros(n)
    last = df["last"].to_numpy(dtype=float) if "last" in df else np.zeros(n)

    mid = np.where((bid > 0) & (ask > 0), (bid + ask) / 2.0, 0.0)
    price = np.where(last > 0, last, mid)
    # Carry a real price forward over any zero gaps so diffs stay meaningful.
    price = pd.Series(price).replace(0.0, np.nan).ffill().bfill().to_numpy()

    # Size per tick.
    if "volume_real" in df:
        vol = df["volume_real"].to_numpy(dtype=float)
    elif "volume" in df:
        vol = df["volume"].to_numpy(dtype=float)
    else:
        vol = np.ones(n)
    vol = np.where(vol > 0, vol, 1.0)

    # Tick-rule direction: sign of price change, zeros carried forward.
    diff = np.diff(price, prepend=price[0])
    sign = np.sign(diff)
    last_sign = 0.0
    signs = np.empty(n)
    for i in range(n):
        if sign[i] != 0:
            last_sign = sign[i]
        signs[i] = last_sign

    buy_vol = float(vol[signs > 0].sum())
    sell_vol = float(vol[signs < 0].sum())
    return TapeMetrics(n_ticks=n, buy_vol=buy_vol, sell_vol=sell_vol)


def book_imbalance(book_levels: Sequence[tuple]) -> BookMetrics:
    """Aggregate a depth-of-market snapshot into a BookMetrics.

    ``book_levels`` is a sequence of ``(is_bid, volume)`` tuples where ``is_bid``
    is True for resting demand (buy limit orders) and False for resting supply.
    """
    bid_vol = 0.0
    ask_vol = 0.0
    levels = 0
    for is_bid, volume in book_levels:
        v = float(volume)
        if v <= 0:
            continue
        levels += 1
        if is_bid:
            bid_vol += v
        else:
            ask_vol += v
    return BookMetrics(available=levels > 0, levels=levels,
                       bid_vol=bid_vol, ask_vol=ask_vol)


def decide(direction: str, tape: TapeMetrics, book: BookMetrics) -> OrderFlowSignal:
    """Combine tape + book metrics into an agree/reject decision for `direction`.

    A BUY needs net buying pressure (delta ratio above threshold) and, when the
    DOM is used, resting demand that is not skewed against it; a SELL is the
    mirror image. Thresholds come from ``config.ORDER_FLOW_*``.
    """
    direction = direction.upper()
    min_delta = config.ORDER_FLOW_MIN_DELTA_RATIO
    min_book = config.ORDER_FLOW_MIN_BOOK_IMBALANCE
    use_book = config.ORDER_FLOW_USE_BOOK
    require_book = config.ORDER_FLOW_REQUIRE_BOOK
    min_ticks = config.ORDER_FLOW_MIN_TICKS

    if tape.n_ticks < min_ticks:
        return OrderFlowSignal(direction, False,
                               f"insufficient ticks (<{min_ticks})", tape, book)

    if require_book and not book.available:
        return OrderFlowSignal(direction, False, "DOM required but unavailable",
                               tape, book)

    if direction == "BUY":
        tape_ok = tape.delta_ratio >= min_delta
        book_ok = (not use_book or not book.available
                   or book.imbalance >= -min_book)
        want = "buying"
    elif direction == "SELL":
        tape_ok = tape.delta_ratio <= -min_delta
        book_ok = (not use_book or not book.available
                   or book.imbalance <= min_book)
        want = "selling"
    else:
        return OrderFlowSignal(direction, False,
                               f"unknown direction {direction!r}", tape, book)

    if tape_ok and book_ok:
        reason = f"confirmed ({want} pressure)"
    elif not tape_ok:
        reason = f"tape flow too weak/opposed for {want}"
    else:
        reason = f"DOM skewed against {want}"
    return OrderFlowSignal(direction, tape_ok and book_ok, reason, tape, book)


# --------------------------------------------------------------------------- #
# MT5-backed data access
# --------------------------------------------------------------------------- #
def subscribe_book() -> bool:
    """Subscribe to the symbol's depth of market (safe to call repeatedly)."""
    if mt5 is None or not config.ORDER_FLOW_USE_BOOK:
        return False
    try:
        ok = bool(mt5.market_book_add(config.SYMBOL))
        if ok:
            log.info("Subscribed to DOM for %s", config.SYMBOL)
        else:
            log.warning("DOM subscription unavailable for %s (broker may not "
                        "provide Level 2).", config.SYMBOL)
        return ok
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("market_book_add raised: %s", exc)
        return False


def release_book() -> None:
    """Release the DOM subscription during shutdown."""
    if mt5 is None or not config.ORDER_FLOW_USE_BOOK:
        return
    try:
        mt5.market_book_release(config.SYMBOL)
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("market_book_release raised: %s", exc)


def _fetch_ticks(seconds: int) -> Optional[pd.DataFrame]:
    """Pull the last `seconds` of ticks for the configured symbol."""
    if mt5 is None:
        return None
    to_dt = datetime.now(UTC)
    from_dt = to_dt - timedelta(seconds=seconds)
    try:
        ticks = mt5.copy_ticks_range(config.SYMBOL, from_dt, to_dt,
                                     mt5.COPY_TICKS_ALL)
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("copy_ticks_range raised: %s", exc)
        return None
    if ticks is None or len(ticks) == 0:
        return None
    return pd.DataFrame(ticks)


def _fetch_book() -> BookMetrics:
    """Snapshot the current depth of market as BookMetrics."""
    if mt5 is None or not config.ORDER_FLOW_USE_BOOK:
        return BookMetrics()
    try:
        items = mt5.market_book_get(config.SYMBOL)
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("market_book_get raised: %s", exc)
        return BookMetrics()
    if not items:
        return BookMetrics()

    # BUY entries are resting bids (demand); SELL entries are resting asks.
    buy_types = {mt5.BOOK_TYPE_BUY, mt5.BOOK_TYPE_BUY_MARKET}
    levels = []
    for it in items:
        volume = getattr(it, "volume_real", 0) or getattr(it, "volume", 0)
        levels.append((it.type in buy_types, volume))
    return book_imbalance(levels)


def evaluate_order_flow(direction: str) -> Optional[OrderFlowSignal]:
    """Read live tape + DOM and decide whether flow confirms `direction`.

    Returns ``None`` when market data is unavailable (no MT5 or no ticks in the
    window) so the caller can retry rather than treat it as a rejection.
    """
    df = _fetch_ticks(config.ORDER_FLOW_LOOKBACK_SECONDS)
    if df is None:
        log.info("Order flow: no tick data in the last %ds window.",
                 config.ORDER_FLOW_LOOKBACK_SECONDS)
        return None

    tape = classify_ticks(df)
    book = _fetch_book()
    return decide(direction, tape, book)


# --------------------------------------------------------------------------- #
# Self-test / demo (runs without a broker connection)
# --------------------------------------------------------------------------- #
def _demo() -> None:
    """Exercise the pure decision logic against synthetic scenarios."""
    def synth_ticks(trend: float, n: int = 60, start: float = 1.1000):
        # trend > 0 walks price up (buyer-initiated ticks dominate).
        prices, p = [], start
        step = 0.00002
        for i in range(n):
            # Deterministic zig-zag biased by `trend`, no RNG needed.
            drift = step * trend
            wobble = step * (1 if (i % 3 == 0) else -1) * 0.4
            p = round(p + drift + wobble, 5)
            prices.append(p)
        return pd.DataFrame({
            "bid": [pr - 0.00001 for pr in prices],
            "ask": [pr + 0.00001 for pr in prices],
            "last": [0.0] * n,          # force mid-price path (typical for FX)
            "volume": [1] * n,
        })

    scenarios = [
        ("BUY", "strong buying tape", synth_ticks(trend=+3.0),
         [(True, 800), (True, 600), (False, 300), (False, 200)]),
        ("BUY", "tape drifting down (should reject)", synth_ticks(trend=-3.0),
         [(True, 800), (False, 200)]),
        ("SELL", "strong selling tape", synth_ticks(trend=-3.0),
         [(True, 200), (False, 700), (False, 500)]),
        ("SELL", "DOM stacked on the bid (should reject)", synth_ticks(trend=-3.0),
         [(True, 900), (True, 800), (False, 100)]),
    ]

    print("=" * 68)
    print("ORDER-FLOW DECISION SELF-TEST")
    print("=" * 68)
    print(f"thresholds: min_delta_ratio={config.ORDER_FLOW_MIN_DELTA_RATIO} "
          f"min_book_imbalance={config.ORDER_FLOW_MIN_BOOK_IMBALANCE} "
          f"use_book={config.ORDER_FLOW_USE_BOOK}\n")
    for direction, label, ticks, levels in scenarios:
        tape = classify_ticks(ticks)
        book = book_imbalance(levels)
        signal = decide(direction, tape, book)
        verdict = "ENTER " if signal.agrees else "SKIP  "
        print(f"[{verdict}] {label}")
        print(f"          {signal.summary()}\n")


if __name__ == "__main__":
    _demo()

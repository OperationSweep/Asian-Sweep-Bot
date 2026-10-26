"""
Queue-aware paper simulator for cross-exchange market making (XEMM).

One strategy instance quotes passively on a "maker" venue and, when a quote is
filled, hedges the filled quantity with an IOC-style taker order on a deeper
"hedge" venue. Spot only, pre-funded inventory on both venues: a maker buy is
offset by SELLING base we already hold on the hedge venue (never a short).

Inputs are the collector's files (no keys, no orders):
    books.jsonl.gz   one line per sample: {"t": local_ms, "books": {venue: {symbol: book}}}
    trades.jsonl.gz  one line per print:  [venue, symbol, exch_ms, recv_ms, price, amount, side, id]

Only completed maker-and-hedge cycles count as profit. Unfilled quotes,
cancels and open inventory never do; open exposure at the end is reported
separately.

Fill models for the maker quote (a price merely touching the quote is never a
fill, except in "optimistic"):
    optimistic    any print at or through our price fills the whole remaining
                  quote; so does the opposite best price touching it
    realistic     prints through our price fill up to the print size; prints AT
                  our price first consume the queue that was ahead of us when we
                  joined (which also shrinks if that level shrinks)
    conservative  only prints strictly through our price fill (up to the print
                  size), and the hedge latency is doubled

Run:
    python -m arb.xemm_sim data/books.jsonl.gz data/trades.jsonl.gz --out data/xemm.json
"""

from __future__ import annotations

import argparse
import bisect
import gzip
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from arb import arb_config as cfg

Level = List[float]          # [price, qty]
FILL_MODELS = ("optimistic", "realistic", "conservative")


# --------------------------------------------------------------------------- book helpers

def walk(levels: List[Level], qty: float, limit: Optional[float], is_buy: bool) -> Tuple[float, float]:
    """Take up to qty from levels, not past limit. Returns (filled_qty, quote_amount)."""
    filled = 0.0
    quote = 0.0
    for p, q in levels:
        if limit is not None and ((is_buy and p > limit) or (not is_buy and p < limit)):
            break
        take = min(q, qty - filled)
        filled += take
        quote += take * p
        if filled >= qty - 1e-12:
            break
    return filled, quote


def vwap(levels: List[Level], qty: float) -> Optional[float]:
    filled, quote = walk(levels, qty, None, True)
    return quote / filled if filled >= qty - 1e-12 and filled > 0 else None


def level_size(levels: List[Level], price: float) -> float:
    for p, q in levels:
        if math.isclose(p, price, rel_tol=1e-12, abs_tol=1e-12):
            return q
    return 0.0


def tick_of(book: dict) -> float:
    """Rough price increment: smallest gap between adjacent levels (precision is not in the feed)."""
    gaps = []
    for side in ("bids", "asks"):
        lv = book[side]
        gaps += [abs(lv[i][0] - lv[i + 1][0]) for i in range(min(len(lv), 10) - 1)]
    gaps = [g for g in gaps if g > 0]
    return min(gaps) if gaps else 0.0


# --------------------------------------------------------------------------- strategy

@dataclass
class Params:
    maker: str
    hedge: str
    symbol: str
    fill_model: str = "realistic"
    maker_fee: float = 0.0
    hedge_fee: float = 0.0
    edge_bps: float = 5.0             # extra margin over fees, vs the hedge VWAP
    quote_usd: float = 100.0
    bucket_usd: float = 1000.0        # starting value of each of the 4 balances
    refresh_bps: float = 1.0          # replace the quote when the target moves this much
    place_latency_ms: int = 150
    cancel_latency_ms: int = 150
    hedge_latency_ms: int = 300
    hedge_timeout_ms: int = 2000      # after this, an unhedged fill counts as a failed hedge
    hedge_slip_bps: float = 10.0      # IOC limit: worst price vs the hedge VWAP at fill time
    max_book_age_ms: int = 1500
    max_mid_gap_bps: float = 50.0     # maker mid vs hedge mid: larger gap pauses quoting

    def label(self) -> str:
        return f"{self.maker}>{self.hedge} {self.symbol} {self.fill_model} edge{self.edge_bps:g}"


@dataclass
class Quote:
    side: str                 # "buy" or "sell" on the maker venue
    price: float
    qty: float
    placed_ms: int
    live_ms: int
    queue_ahead: float
    remaining: float = 0.0
    cancel_ms: Optional[int] = None   # quote stays fillable until this time

    def live_at(self, t: int) -> bool:
        return t >= self.live_ms and (self.cancel_ms is None or t < self.cancel_ms) and self.remaining > 1e-12


@dataclass
class PendingHedge:
    side: str                 # maker side that was filled
    qty: float
    maker_px: float
    fill_ms: int
    due_ms: int
    ref_px: float             # hedge VWAP when the quote was priced (IOC limit anchor)
    proceeds: float = 0.0     # hedge quote amount so far, after fee
    hedged: float = 0.0
    failed: bool = False


class XEMM:
    def __init__(self, p: Params):
        self.p = p
        if p.fill_model == "conservative":
            p.hedge_latency_ms *= 2
        self.quotes: Dict[str, Optional[Quote]] = {"buy": None, "sell": None}
        self.cancelling: List[Quote] = []
        self.hedges: List[PendingHedge] = []
        self.bal = None       # {"m_base","m_quote","h_base","h_quote"}, set on first good sample
        self.start_px = None
        self.ref_hedge = {"buy": None, "sell": None}
        self.stats = defaultdict(float)
        self.cycle_pnl: List[Tuple[int, float]] = []
        self.unhedged_s: List[float] = []
        self.markouts = {1000: [], 5000: []}
        self._markout_queue: List[Tuple[int, str, float, int]] = []
        self.max_drift = 0.0

    # -- quoting -------------------------------------------------------------
    def targets(self, mb: dict, hb: dict, mid: float) -> Dict[str, Optional[float]]:
        p = self.p
        qty = p.quote_usd / mid
        out: Dict[str, Optional[float]] = {"buy": None, "sell": None}
        sell_vwap = vwap(hb["bids"], qty)          # hedge for a maker buy
        buy_vwap = vwap(hb["asks"], qty)           # hedge for a maker sell
        tick = tick_of(mb)
        e = p.edge_bps / 1e4
        if sell_vwap:
            bid = sell_vwap * (1 - p.hedge_fee) / (1 + p.maker_fee) * (1 - e)
            if tick:
                bid = math.floor(bid / tick) * tick
            if bid < mb["asks"][0][0]:            # post-only: must not cross
                out["buy"] = bid
            self.ref_hedge["buy"] = sell_vwap
        if buy_vwap:
            ask = buy_vwap * (1 + p.hedge_fee) / (1 - p.maker_fee) * (1 + e)
            if tick:
                ask = math.ceil(ask / tick) * tick
            if ask > mb["bids"][0][0]:
                out["sell"] = ask
            self.ref_hedge["sell"] = buy_vwap
        return out

    def can_quote(self, side: str, px: float, qty: float) -> bool:
        b = self.bal
        if side == "buy":   # need maker quote cash and hedge base to sell
            return b["m_quote"] >= px * qty * (1 + self.p.maker_fee) and b["h_base"] >= qty
        return b["m_base"] >= qty and b["h_quote"] >= px * qty * 1.01

    def cancel(self, side: str, t: int) -> None:
        q = self.quotes[side]
        if q is not None:
            q.cancel_ms = t + self.p.cancel_latency_ms
            self.cancelling.append(q)
            self.quotes[side] = None
            self.stats["cancels"] += 1

    def requote(self, t: int, mb: dict, tgt: Dict[str, Optional[float]], mid: float) -> None:
        p = self.p
        for side in ("buy", "sell"):
            px = tgt[side]
            cur = self.quotes[side]
            qty = p.quote_usd / mid
            if px is None or not self.can_quote(side, px, qty):
                self.cancel(side, t)
                continue
            if cur is not None and abs(cur.price - px) / px * 1e4 < p.refresh_bps:
                continue
            self.cancel(side, t)
            same = mb["bids"] if side == "buy" else mb["asks"]
            ahead = level_size(same, px)
            self.quotes[side] = Quote(side, px, qty, t, t + p.place_latency_ms, ahead, remaining=qty)
            self.stats["quotes"] += 1
            self.stats["quoted_usd"] += qty * px

    # -- fills ---------------------------------------------------------------
    def _all_quotes(self) -> List[Quote]:
        return [q for q in list(self.quotes.values()) + self.cancelling if q is not None]

    def on_trade(self, t: int, price: float, amount: float, aggressor: Optional[str]) -> None:
        for q in self._all_quotes():
            if not q.live_at(t):
                continue
            # A sell aggressor hits bids; a buy aggressor lifts asks.
            if aggressor and ((q.side == "buy") != (aggressor == "sell")):
                continue
            through = price < q.price if q.side == "buy" else price > q.price
            at = math.isclose(price, q.price, rel_tol=1e-12)
            if not (through or at):
                continue
            m = self.p.fill_model
            if m == "optimistic":
                self.fill(q, q.remaining, t)
            elif m == "realistic":
                avail = amount
                if at:
                    used = min(q.queue_ahead, avail)
                    q.queue_ahead -= used
                    avail -= used
                if avail > 0:
                    self.fill(q, min(q.remaining, avail), t)
            elif through:   # conservative
                self.fill(q, min(q.remaining, amount), t)

    def on_book(self, t: int, mb: dict) -> None:
        for q in self._all_quotes():
            same = mb["bids"] if q.side == "buy" else mb["asks"]
            q.queue_ahead = min(q.queue_ahead, level_size(same, q.price))
            if self.p.fill_model == "optimistic" and q.live_at(t):
                opp = mb["asks"][0][0] if q.side == "buy" else mb["bids"][0][0]
                if (q.side == "buy" and opp <= q.price) or (q.side == "sell" and opp >= q.price):
                    self.fill(q, q.remaining, t)
        self.cancelling = [q for q in self.cancelling if q.cancel_ms is not None and q.cancel_ms > t]

    def fill(self, q: Quote, qty: float, t: int) -> None:
        if qty <= 1e-12:
            return
        p, b = self.p, self.bal
        q.remaining -= qty
        notional = qty * q.price
        if q.side == "buy":
            b["m_base"] += qty
            b["m_quote"] -= notional * (1 + p.maker_fee)
        else:
            b["m_base"] -= qty
            b["m_quote"] += notional * (1 - p.maker_fee)
        if q.cancel_ms is not None:
            self.stats["fills_after_cancel_sent"] += 1
        self.stats["fills"] += 1
        self.stats["filled_usd"] += notional
        ref = self.ref_hedge[q.side] or q.price
        self.hedges.append(PendingHedge(q.side, qty, q.price, t, t + p.hedge_latency_ms, ref))
        self._markout_queue.append((t, q.side, q.price, 0))

    # -- hedging -------------------------------------------------------------
    def run_hedges(self, t: int, hb: Optional[dict]) -> None:
        p, b = self.p, self.bal
        keep = []
        for h in self.hedges:
            if t < h.due_ms:
                keep.append(h)
                continue
            if t - h.fill_ms > p.hedge_timeout_ms and not h.failed:
                h.failed = True
                self.stats["failed_hedges"] += 1
            if hb is not None:
                need = h.qty - h.hedged
                slip = p.hedge_slip_bps / 1e4
                if h.failed:   # past the timeout: flatten at any price on the visible book
                    limit = None
                else:
                    limit = h.ref_px * (1 - slip) if h.side == "buy" else h.ref_px * (1 + slip)
                if h.side == "buy":    # maker bought, so sell the same qty on the hedge venue
                    got, quote = walk(hb["bids"], need, limit, False)
                    b["h_base"] -= got
                    b["h_quote"] += quote * (1 - p.hedge_fee)
                    h.proceeds += quote * (1 - p.hedge_fee)
                else:
                    got, quote = walk(hb["asks"], need, limit, True)
                    b["h_base"] += got
                    b["h_quote"] -= quote * (1 + p.hedge_fee)
                    h.proceeds -= quote * (1 + p.hedge_fee)
                h.hedged += got
            if h.hedged >= h.qty - 1e-12:
                maker_cash = h.qty * h.maker_px
                if h.side == "buy":
                    pnl = h.proceeds - maker_cash * (1 + p.maker_fee)
                else:
                    pnl = maker_cash * (1 - p.maker_fee) + h.proceeds
                self.cycle_pnl.append((t, pnl))
                self.unhedged_s.append((t - h.fill_ms) / 1000)
                self.stats["cycles"] += 1
            else:
                keep.append(h)
        self.hedges = keep

    def markouts_step(self, t: int, hedge_mid: float) -> None:
        rest = []
        for (ft, side, px, done) in self._markout_queue:
            for horizon in (1000, 5000):
                if not done & (1 if horizon == 1000 else 2) and t >= ft + horizon:
                    sign = 1 if side == "buy" else -1
                    self.markouts[horizon].append(sign * (hedge_mid - px) / px * 1e4)
                    done |= 1 if horizon == 1000 else 2
            if done != 3:
                rest.append((ft, side, px, done))
        self._markout_queue = rest

    # -- main step -----------------------------------------------------------
    def step(self, t: int, mb: Optional[dict], hb: Optional[dict]) -> None:
        p = self.p
        ok_m = mb is not None and t - mb["recv_ms"] <= p.max_book_age_ms and mb["bids"] and mb["asks"] \
            and mb["bids"][0][0] < mb["asks"][0][0]
        ok_h = hb is not None and t - hb["recv_ms"] <= p.max_book_age_ms and hb["bids"] and hb["asks"] \
            and hb["bids"][0][0] < hb["asks"][0][0]
        if self.bal is None:
            if not (ok_m and ok_h):
                return
            mid = (hb["bids"][0][0] + hb["asks"][0][0]) / 2
            base = p.bucket_usd / mid
            self.bal = {"m_base": base, "m_quote": p.bucket_usd, "h_base": base, "h_quote": p.bucket_usd}
            self.start_px = mid
        self.run_hedges(t, hb if ok_h else None)
        if ok_m:
            self.on_book(t, mb)
        if not (ok_m and ok_h):
            self.stats["paused_bad_data"] += 1
            self.cancel("buy", t)
            self.cancel("sell", t)
            return
        m_mid = (mb["bids"][0][0] + mb["asks"][0][0]) / 2
        h_mid = (hb["bids"][0][0] + hb["asks"][0][0]) / 2
        self.markouts_step(t, h_mid)
        if abs(m_mid - h_mid) / h_mid * 1e4 > p.max_mid_gap_bps:
            # Not assumed to be an error, but too risky to quote through.
            self.stats["paused_mid_gap"] += 1
            self.cancel("buy", t)
            self.cancel("sell", t)
            return
        b = self.bal
        start_base = p.bucket_usd / self.start_px
        self.max_drift = max(self.max_drift, abs(b["m_base"] - start_base) * h_mid)
        self.requote(t, mb, self.targets(mb, hb, h_mid), h_mid)

    # -- results -------------------------------------------------------------
    def summary(self, last_hedge_mid: Optional[float]) -> dict:
        pnl = [x for _, x in self.cycle_pnl]
        cum, peak, dd = 0.0, 0.0, 0.0
        for x in pnl:
            cum += x
            peak = max(peak, cum)
            dd = max(dd, peak - cum)
        open_qty = sum((h.qty - h.hedged) * (1 if h.side == "buy" else -1) for h in self.hedges)
        open_mtm = None
        if last_hedge_mid is not None and self.hedges:
            # Value of finishing the open hedges at the last mid, no fees (optimistic).
            open_mtm = sum(
                (h.proceeds + (h.qty - h.hedged) * last_hedge_mid - h.qty * h.maker_px) if h.side == "buy"
                else (h.qty * h.maker_px + h.proceeds - (h.qty - h.hedged) * last_hedge_mid)
                for h in self.hedges)
        us = sorted(self.unhedged_s)
        capital = 4 * self.p.bucket_usd
        s = dict(self.stats)
        fills = s.get("fills", 0)
        hedged_fills = s.get("cycles", 0)
        return {
            "label": self.p.label(),
            "maker": self.p.maker, "hedge": self.p.hedge, "symbol": self.p.symbol,
            "fill_model": self.p.fill_model, "edge_bps": self.p.edge_bps,
            "maker_fee": self.p.maker_fee, "hedge_fee": self.p.hedge_fee,
            "hedge_latency_ms": self.p.hedge_latency_ms,
            "quotes": int(s.get("quotes", 0)), "cancels": int(s.get("cancels", 0)),
            "fills": int(fills), "fills_after_cancel_sent": int(s.get("fills_after_cancel_sent", 0)),
            "filled_usd": round(s.get("filled_usd", 0), 2),
            "fill_rate_per_quote": round(fills / s["quotes"], 4) if s.get("quotes") else 0,
            "cycles": int(hedged_fills),
            "hedge_completion_pct": round(100 * hedged_fills / fills, 2) if fills else None,
            "failed_hedges": int(s.get("failed_hedges", 0)),
            "net_pnl_usd": round(sum(pnl), 4),
            "net_pnl_bps_of_filled": round(sum(pnl) / s["filled_usd"] * 1e4, 2) if s.get("filled_usd") else None,
            "max_drawdown_usd": round(dd, 4),
            "max_drawdown_pct_of_capital": round(100 * dd / capital, 4),
            "p50_s_unhedged": us[len(us) // 2] if us else None,
            "p95_s_unhedged": us[int(len(us) * 0.95)] if us else None,
            "max_s_unhedged": us[-1] if us else None,
            "markout_1s_bps": round(sum(self.markouts[1000]) / len(self.markouts[1000]), 2) if self.markouts[1000] else None,
            "markout_5s_bps": round(sum(self.markouts[5000]) / len(self.markouts[5000]), 2) if self.markouts[5000] else None,
            "max_inventory_drift_usd": round(self.max_drift, 2),
            "open_qty_end": open_qty, "open_mtm_usd_end": round(open_mtm, 4) if open_mtm is not None else None,
            "paused_bad_data": int(s.get("paused_bad_data", 0)), "paused_mid_gap": int(s.get("paused_mid_gap", 0)),
        }


# --------------------------------------------------------------------------- replay

def load_trades(path: str, wanted: set) -> Dict[Tuple[str, str], List[list]]:
    out: Dict[Tuple[str, str], List[list]] = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            key = (r[0], r[1])
            if key in wanted:
                out[key].append(r)
    for k in out:
        out[k].sort(key=lambda r: r[3])   # by local receive time: same clock as the simulator
    return out


def replay(books_path: str, trades_path: str, params: List[Params]) -> List[XEMM]:
    sims = [XEMM(p) for p in params]
    wanted = {(p.maker, p.symbol) for p in params}
    trades = load_trades(trades_path, wanted)
    recv_index = {k: [r[3] for r in v] for k, v in trades.items()}
    by_key: Dict[Tuple[str, str], List[XEMM]] = defaultdict(list)
    for s in sims:
        by_key[(s.p.maker, s.p.symbol)].append(s)
    prev_t = None
    last_mid: Dict[Tuple[str, str], float] = {}
    with gzip.open(books_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            snap = json.loads(line)
            t = snap["t"]
            books = snap["books"]
            if prev_t is not None:
                for key, group in by_key.items():
                    if key not in trades:
                        continue
                    lo = bisect.bisect_right(recv_index[key], prev_t)
                    hi = bisect.bisect_right(recv_index[key], t)
                    for r in trades[key][lo:hi]:
                        for s in group:
                            if s.bal is not None:
                                s.on_trade(r[3], r[4], r[5], r[6])
            for s in sims:
                mb = books.get(s.p.maker, {}).get(s.p.symbol)
                hb = books.get(s.p.hedge, {}).get(s.p.symbol)
                s.step(t, mb, hb)
                if hb and hb["bids"] and hb["asks"]:
                    last_mid[(s.p.hedge, s.p.symbol)] = (hb["bids"][0][0] + hb["asks"][0][0]) / 2
            prev_t = t
    for s in sims:
        s._last_mid = last_mid.get((s.p.hedge, s.p.symbol))
    return sims


def feed_quality(books_path: str, trades_path: str) -> dict:
    """Per venue/symbol: update ages, crossed books, timestamp lag, trade counts."""
    q: Dict[str, dict] = defaultdict(lambda: {"samples": 0, "stale": 0, "crossed": 0, "lag_ms": []})
    with gzip.open(books_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            snap = json.loads(line)
            for v, syms in snap["books"].items():
                for s, b in syms.items():
                    d = q[f"{v} {s}"]
                    d["samples"] += 1
                    if snap["t"] - b["recv_ms"] > cfg.MAX_QUOTE_AGE_MS:
                        d["stale"] += 1
                    if b["bids"] and b["asks"] and b["bids"][0][0] >= b["asks"][0][0]:
                        d["crossed"] += 1
                    if b.get("exch_ms") and len(d["lag_ms"]) < 20000:
                        d["lag_ms"].append(b["recv_ms"] - b["exch_ms"])
    tcount: Dict[str, int] = defaultdict(int)
    with gzip.open(trades_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            tcount[f"{r[0]} {r[1]}"] += 1
    out = {}
    for k, d in q.items():
        lags = sorted(d["lag_ms"])
        out[k] = {"samples": d["samples"], "stale_pct": round(100 * d["stale"] / d["samples"], 2),
                  "crossed_pct": round(100 * d["crossed"] / d["samples"], 3),
                  "median_lag_ms": lags[len(lags) // 2] if lags else None, "trades": tcount.get(k, 0)}
    return out


def fee(venue: str, kind: str, scenario: str) -> float:
    if scenario == "low":     # a hypothetical well-tiered account: 0 maker, 0.05 % taker
        return 0.0 if kind == "maker" else 0.0005
    table = cfg.MAKER_FEES if kind == "maker" else cfg.TAKER_FEES
    return table.get(venue, (0.001, ""))[0]


def build_grid(venues: List[str], hedges: List[str], symbols: List[str], edges: List[float],
               scenarios: List[str], latencies: List[int]) -> List[Params]:
    grid = []
    for m in venues:
        for h in hedges:
            if m == h:
                continue
            for sym in symbols:
                for sc in scenarios:
                    for e in edges:
                        for fm in FILL_MODELS:
                            for lat in latencies:
                                if lat != latencies[0] and fm != "realistic":
                                    continue
                                pr = Params(m, h, sym, fm, fee(m, "maker", sc), fee(h, "taker", sc), e,
                                            hedge_latency_ms=lat)
                                pr.scenario = sc
                                grid.append(pr)
    return grid


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("books")
    ap.add_argument("trades")
    ap.add_argument("--out", default="xemm.json")
    ap.add_argument("--venues", default=",".join(cfg.XEMM_VENUES))
    ap.add_argument("--hedges", default=",".join(cfg.XEMM_HEDGE_VENUES))
    ap.add_argument("--symbols", default=",".join(cfg.XEMM_SYMBOLS))
    ap.add_argument("--edges", default="0,5,15")
    ap.add_argument("--scenarios", default="retail,low")
    ap.add_argument("--latencies", default="300,2000", help="hedge latencies in ms; extras run realistic only")
    a = ap.parse_args()
    grid = build_grid(a.venues.split(","), a.hedges.split(","), a.symbols.split(","),
                      [float(x) for x in a.edges.split(",")], a.scenarios.split(","),
                      [int(x) for x in a.latencies.split(",")])
    sims = replay(a.books, a.trades, grid)
    rows = []
    for s in sims:
        r = s.summary(getattr(s, "_last_mid", None))
        r["scenario"] = s.p.scenario
        rows.append(r)
    out = {"feed_quality": feed_quality(a.books, a.trades), "runs": rows}
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    active = [r for r in rows if r["fills"]]
    print(f"{len(rows)} configurations, {len(active)} with at least one fill")
    hdr = f"{'config':52} {'sc':6} {'lat':>5} {'quotes':>6} {'fills':>5} {'cyc':>4} {'hedge%':>6} {'fail':>4} {'net$':>9} {'bps':>7} {'mk5s':>6} {'p95s':>5}"
    print(hdr)
    for r in sorted(active, key=lambda r: -r["net_pnl_usd"])[:60]:
        print(f"{r['label']:52} {r['scenario']:6} {r['hedge_latency_ms']:>5} {r['quotes']:>6} {r['fills']:>5} "
              f"{r['cycles']:>4} {str(r['hedge_completion_pct']):>6} {r['failed_hedges']:>4} {r['net_pnl_usd']:>9.3f} "
              f"{str(r['net_pnl_bps_of_filled']):>7} {str(r['markout_5s_bps']):>6} {str(r['p95_s_unhedged']):>5}")
    print("feed quality:")
    for k, v in sorted(out["feed_quality"].items()):
        print(f"  {k:22} {v}")

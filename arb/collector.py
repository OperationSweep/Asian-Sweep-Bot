"""
Public order-book collector.

Subscribes to WebSocket order books (via ccxt.pro) for every configured venue and
symbol, keeps the latest book in memory, and once per sample interval writes one
JSON line per sample containing every book plus how old each one is.

With --trades it also records every public trade print (exchange and local
timestamps) to a second file, which the market-making simulator needs for
queue-aware fills.

No API keys, no orders. Run:
    python -m arb.collector --minutes 30 --out data/books.jsonl.gz
    python -m arb.collector --minutes 60 --interval 0.25 --trades data/trades.jsonl.gz \
        --venues kraken,okx --symbols BTC/USDT,ETH/USDT --out data/books.jsonl.gz
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import logging
import time
from typing import Dict, List, Optional

import ccxt.pro as ccxtpro

from arb import arb_config as cfg

log = logging.getLogger("collector")

# (venue, symbol) -> {"bids", "asks", "recv_ms", "exch_ms", "nonce"}
BOOKS: Dict[str, Dict[str, dict]] = {}
STATS: Dict[str, Dict[str, int]] = {}
# Trade prints waiting to be flushed: [venue, symbol, exch_ms, recv_ms, price, amount, side, id]
TRADES: List[list] = []


# Some venues only accept fixed subscription depths; the book is truncated after.
WS_DEPTH = {"kraken": 25, "bitfinex": 25}


def _stat(venue: str) -> Dict[str, int]:
    return STATS.setdefault(venue, {"updates": 0, "errors": 0, "trades": 0,
                                    "book_ts_backwards": 0, "trade_ts_backwards": 0})


async def watch(ex, symbol: str, stop_at: float) -> None:
    venue = ex.id
    backoff = 1.0
    warned = 0
    while time.time() < stop_at:
        try:
            ob = await ex.watch_order_book(symbol, WS_DEPTH.get(venue, cfg.BOOK_DEPTH))
            # Sort defensively: a mis-ordered side would fake a cross-venue gap.
            bids = sorted(([float(p), float(q)] for p, q, *_ in ob["bids"]), key=lambda l: -l[0])
            asks = sorted(([float(p), float(q)] for p, q, *_ in ob["asks"]), key=lambda l: l[0])
            prev = BOOKS.get(venue, {}).get(symbol)
            exch_ms = ob.get("timestamp")
            if prev and exch_ms and prev.get("exch_ms") and exch_ms < prev["exch_ms"]:
                _stat(venue)["book_ts_backwards"] += 1   # out-of-sequence update
            BOOKS.setdefault(venue, {})[symbol] = {
                "bids": bids[: cfg.BOOK_DEPTH],
                "asks": asks[: cfg.BOOK_DEPTH],
                "recv_ms": int(time.time() * 1000),
                "exch_ms": exch_ms,
                "nonce": ob.get("nonce"),
            }
            _stat(venue)["updates"] += 1
            backoff = 1.0
        except Exception as e:  # network drops, geo-blocks, unsupported symbols
            _stat(venue)["errors"] += 1
            # First failure per feed at ERROR so it survives log filtering; repeats as WARNING.
            (log.error if warned == 0 else log.warning)("%s %s: %s", venue, symbol, str(e)[:200])
            warned += 1
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)


async def watch_trades(ex, symbol: str, stop_at: float) -> None:
    venue = ex.id
    backoff = 1.0
    warned = 0
    seen: Dict[str, None] = {}   # insertion-ordered, bounded set of trade ids
    last_ts = 0
    while time.time() < stop_at:
        try:
            trades = await ex.watch_trades(symbol)
            recv = int(time.time() * 1000)
            for tr in trades:
                key = str(tr.get("id") or (tr.get("timestamp"), tr.get("price"), tr.get("amount")))
                if key in seen:
                    continue
                seen[key] = None
                if len(seen) > 5000:
                    seen.pop(next(iter(seen)))
                ts = tr.get("timestamp") or 0
                if ts and ts < last_ts:
                    _stat(venue)["trade_ts_backwards"] += 1
                last_ts = max(last_ts, ts)
                TRADES.append([venue, symbol, ts, recv, float(tr["price"]), float(tr["amount"]),
                               tr.get("side"), tr.get("id")])
                _stat(venue)["trades"] += 1
            backoff = 1.0
        except Exception as e:
            _stat(venue)["errors"] += 1
            (log.error if warned == 0 else log.warning)("%s %s trades: %s", venue, symbol, str(e)[:200])
            warned += 1
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)


async def sampler(out_path: str, stop_at: float, interval: float, trades_path: Optional[str]) -> None:
    tfh = gzip.open(trades_path, "at", encoding="utf-8") if trades_path else None
    try:
        with gzip.open(out_path, "at", encoding="utf-8") as fh:
            while time.time() < stop_at:
                await asyncio.sleep(interval)
                now = int(time.time() * 1000)
                fh.write(json.dumps({"t": now, "books": BOOKS}, separators=(",", ":")) + "\n")
                if tfh and TRADES:
                    batch = TRADES[:]
                    del TRADES[: len(batch)]
                    tfh.write("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in batch))
    finally:
        if tfh:
            tfh.close()


async def open_venue(venue: str, wanted: List[str]):
    ex = getattr(ccxtpro, venue)({"enableRateLimit": True})
    try:
        await ex.load_markets()
    except Exception as e:
        log.error("skip %s: load_markets failed: %s", venue, str(e)[:200])
        await ex.close()
        return None, []
    symbols = [s for s in wanted if s in ex.markets and ex.markets[s].get("active", True) is not False]
    log.info("%s: %d symbols %s", venue, len(symbols), symbols)
    return ex, symbols


async def main(minutes: float, out_path: str, venues: List[str], symbols: List[str],
               interval: float = cfg.SAMPLE_INTERVAL_S, trades_path: Optional[str] = None) -> None:
    stop_at = time.time() + minutes * 60
    opened = await asyncio.gather(*(open_venue(v, symbols) for v in venues))
    tasks = [asyncio.create_task(sampler(out_path, stop_at, interval, trades_path))]
    exchanges = []
    for ex, symbols in opened:
        if ex is None:
            continue
        exchanges.append(ex)
        for s in symbols:
            tasks.append(asyncio.create_task(watch(ex, s, stop_at)))
            if trades_path:
                tasks.append(asyncio.create_task(watch_trades(ex, s, stop_at)))
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=minutes * 60 + 60)
    except asyncio.TimeoutError:
        pass
    finally:
        for ex in exchanges:
            try:
                await ex.close()
            except Exception:
                pass
    log.info("venue stats: %s", json.dumps(STATS))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--out", default="books.jsonl.gz")
    ap.add_argument("--venues", default=",".join(cfg.VENUES))
    ap.add_argument("--symbols", default=",".join(cfg.CROSS_SYMBOLS + cfg.TRIANGLE_LEGS))
    ap.add_argument("--interval", type=float, default=cfg.SAMPLE_INTERVAL_S, help="seconds between book samples")
    ap.add_argument("--trades", default=None, help="also record trade prints to this .jsonl.gz path")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main(a.minutes, a.out, a.venues.split(","), a.symbols.split(","), a.interval, a.trades))

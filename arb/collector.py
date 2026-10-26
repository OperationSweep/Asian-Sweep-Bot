"""
Public order-book collector.

Subscribes to WebSocket order books (via ccxt.pro) for every configured venue and
symbol, keeps the latest book in memory, and once per SAMPLE_INTERVAL_S writes one
JSON line per sample containing every book plus how old each one is.

No API keys, no orders. Run:
    python -m arb.collector --minutes 30 --out data/books.jsonl.gz
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import logging
import time
from typing import Dict, List

import ccxt.pro as ccxtpro

from arb import arb_config as cfg

log = logging.getLogger("collector")

# (venue, symbol) -> {"bids", "asks", "recv_ms", "exch_ms"}
BOOKS: Dict[str, Dict[str, dict]] = {}
STATS: Dict[str, Dict[str, int]] = {}


async def watch(ex, symbol: str, stop_at: float) -> None:
    venue = ex.id
    backoff = 1.0
    while time.time() < stop_at:
        try:
            ob = await ex.watch_order_book(symbol, cfg.BOOK_DEPTH)
            BOOKS.setdefault(venue, {})[symbol] = {
                "bids": [[float(p), float(q)] for p, q, *_ in ob["bids"][: cfg.BOOK_DEPTH]],
                "asks": [[float(p), float(q)] for p, q, *_ in ob["asks"][: cfg.BOOK_DEPTH]],
                "recv_ms": int(time.time() * 1000),
                "exch_ms": ob.get("timestamp"),
            }
            STATS.setdefault(venue, {"updates": 0, "errors": 0})["updates"] += 1
            backoff = 1.0
        except Exception as e:  # network drops, geo-blocks, unsupported symbols
            STATS.setdefault(venue, {"updates": 0, "errors": 0})["errors"] += 1
            log.warning("%s %s: %s", venue, symbol, str(e)[:200])
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)


async def sampler(out_path: str, stop_at: float) -> None:
    with gzip.open(out_path, "at", encoding="utf-8") as fh:
        while time.time() < stop_at:
            await asyncio.sleep(cfg.SAMPLE_INTERVAL_S)
            now = int(time.time() * 1000)
            fh.write(json.dumps({"t": now, "books": BOOKS}, separators=(",", ":")) + "\n")


async def open_venue(venue: str):
    ex = getattr(ccxtpro, venue)({"enableRateLimit": True})
    try:
        await ex.load_markets()
    except Exception as e:
        log.error("skip %s: load_markets failed: %s", venue, str(e)[:200])
        await ex.close()
        return None, []
    wanted = cfg.CROSS_SYMBOLS + cfg.TRIANGLE_LEGS
    symbols = [s for s in wanted if s in ex.markets and ex.markets[s].get("active", True) is not False]
    log.info("%s: %d symbols %s", venue, len(symbols), symbols)
    return ex, symbols


async def main(minutes: float, out_path: str, venues: List[str]) -> None:
    stop_at = time.time() + minutes * 60
    opened = await asyncio.gather(*(open_venue(v) for v in venues))
    tasks = [asyncio.create_task(sampler(out_path, stop_at))]
    exchanges = []
    for ex, symbols in opened:
        if ex is None:
            continue
        exchanges.append(ex)
        for s in symbols:
            tasks.append(asyncio.create_task(watch(ex, s, stop_at)))
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
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(main(a.minutes, a.out, a.venues.split(",")))

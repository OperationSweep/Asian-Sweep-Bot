"""
Measure how many apparent arbitrage opportunities survive executable prices, depth,
fees, quote age and a one-sample (~1 s) detection-to-execution delay.

    python -m arb.analyze data/books.jsonl.gz --out data/summary.json

Cross-venue model: inventory is already on both venues (quote on the buy venue,
base on the sell venue), both legs are taker orders sent at the same time, and no
transfer happens inside the trade. Rebalancing cost is NOT included here; it is
added in the report's worked examples.
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
from collections import defaultdict
from itertools import permutations
from typing import Dict, List, Optional, Sequence

from arb import arb_config as cfg
from arb.book_math import cross_venue, cycle_return, max_profitable_cross

FEE_SCENARIOS = {
    "retail_taker": None,          # per-venue table from arb_config
    "flat_0.10pct": 0.0010,
    "flat_0.02pct": 0.0002,
    "zero_fee": 0.0,
}


def fee_for(venue: str, scenario: str) -> float:
    flat = FEE_SCENARIOS[scenario]
    if flat is not None:
        return flat
    return cfg.TAKER_FEES.get(venue, (0.0010, ""))[0]


def pct(values: List[float], q: float) -> Optional[float]:
    if not values:
        return None
    values = sorted(values)
    k = min(len(values) - 1, max(0, int(round(q * (len(values) - 1)))))
    return values[k]


class Episodes:
    """Tracks runs of consecutive samples where a key is profitable."""

    def __init__(self):
        self.open: Dict[tuple, dict] = {}
        self.closed: List[dict] = []

    def update(self, t: int, positives: Dict[tuple, dict]) -> None:
        for key, info in positives.items():
            ep = self.open.get(key)
            if ep is None:
                self.open[key] = {"key": key, "start": t, "end": t, "samples": 1,
                                  "first": info, "peak_bps": info["bps"]}
            else:
                ep["end"] = t
                ep["samples"] += 1
                if ep["samples"] == 2:
                    ep["second"] = info
                ep["peak_bps"] = max(ep["peak_bps"], info["bps"])
        for key in list(self.open):
            if key not in positives:
                self.closed.append(self.open.pop(key))

    def finish(self) -> List[dict]:
        self.closed.extend(self.open.values())
        self.open = {}
        return self.closed


# A venue whose mid sits this far from the other venues' median most of the time, or
# whose own book is crossed, is more likely a broken feed than a real opportunity.
SUSPECT_MEDIAN_DEV_BPS = 5.0
SUSPECT_CROSSED_SHARE = 0.005


def analyze(path: str, exclude: Sequence[str] = ()) -> dict:
    samples = 0
    venue_seen: Dict[str, int] = defaultdict(int)
    venue_lag: Dict[str, List[float]] = defaultdict(list)
    venue_crossed: Dict[str, int] = defaultdict(int)
    venue_dev: Dict[str, List[float]] = defaultdict(list)
    stale_dropped = 0

    funnel = {s: defaultdict(int) for s in FEE_SCENARIOS}
    cross_eps = {s: Episodes() for s in FEE_SCENARIOS}
    gross_bps_best: Dict[str, List[float]] = defaultdict(list)

    tri_counts = defaultdict(lambda: defaultdict(int))
    tri_best_bps: Dict[str, List[float]] = defaultdict(list)
    tri_eps = Episodes()

    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            t = rec["t"]
            samples += 1
            fresh: Dict[str, Dict[str, dict]] = defaultdict(dict)
            for venue, books in rec["books"].items():
                if venue in exclude:
                    continue
                for sym, b in books.items():
                    if t - b["recv_ms"] > cfg.MAX_QUOTE_AGE_MS:
                        stale_dropped += 1
                        continue
                    if not b["bids"] or not b["asks"]:
                        continue
                    if b["bids"][0][0] >= b["asks"][0][0]:
                        venue_crossed[venue] += 1   # a venue's own book can't be crossed
                        continue
                    fresh[venue][sym] = b
                    venue_seen[venue] += 1
                    if b.get("exch_ms"):
                        venue_lag[venue].append(b["recv_ms"] - b["exch_ms"])

            # ---- feed sanity: each venue's mid vs the median of the others ----
            for sym in cfg.CROSS_SYMBOLS + cfg.TRIANGLE_LEGS:
                mids = {v: (fresh[v][sym]["bids"][0][0] + fresh[v][sym]["asks"][0][0]) / 2
                        for v in fresh if sym in fresh[v]}
                if len(mids) < 3:
                    continue
                for v, m in mids.items():
                    others = statistics.median([x for k, x in mids.items() if k != v])
                    venue_dev[v].append(abs(m / others - 1) * 1e4)

            # ---- cross-venue ----
            positives = {s: {} for s in FEE_SCENARIOS}
            for sym in cfg.CROSS_SYMBOLS:
                venues = [v for v in fresh if sym in fresh[v]]
                best_gross = None
                for a, b in permutations(venues, 2):
                    asks = fresh[a][sym]["asks"]
                    bids = fresh[b][sym]["bids"]
                    gross_bps = (bids[0][0] / asks[0][0] - 1) * 1e4
                    best_gross = gross_bps if best_gross is None else max(best_gross, gross_bps)
                    for scen in FEE_SCENARIOS:
                        f = funnel[scen]
                        f["pair_observations"] += 1
                        if gross_bps <= 0:
                            continue
                        f["top_of_book_crossed"] += 1
                        fa, fb = fee_for(a, scen), fee_for(b, scen)
                        qty, net_max = max_profitable_cross(asks, bids, fa, fb)
                        if qty <= 0:
                            continue
                        f["net_positive_any_size"] += 1
                        r100 = cross_venue(asks, bids, 100.0, fa, fb)
                        if r100 and r100.net > 0 and r100.complete:
                            f["net_positive_at_100"] += 1
                            positives[scen][(sym, a, b)] = {
                                "bps": r100.net_bps, "max_net_usd": net_max,
                                "max_qty_usd": qty * asks[0][0]}
                        for n in cfg.NOTIONALS[1:]:
                            r = cross_venue(asks, bids, float(n), fa, fb)
                            if r and r.net > 0 and r.complete:
                                f[f"net_positive_at_{n}"] += 1
                if best_gross is not None:
                    gross_bps_best[sym].append(best_gross)
            for scen in FEE_SCENARIOS:
                cross_eps[scen].update(t, positives[scen])

            # ---- triangular, per venue ----
            tri_pos = {}
            for venue, books in fresh.items():
                fee = fee_for(venue, "retail_taker")
                for tri in cfg.TRIANGLES:
                    for path in (tri, [tri[0], tri[2], tri[1]]):
                        name = f"{venue}:{'>'.join(path)}"
                        g = cycle_return(books, path, 1000.0, 0.0)
                        if g is None:
                            continue
                        tri_counts[name]["observations"] += 1
                        gbps = g / 1000.0 * 1e4
                        tri_best_bps[name].append(gbps)
                        if g > 0:
                            tri_counts[name]["gross_positive"] += 1
                        n = cycle_return(books, path, 1000.0, fee)
                        if n is not None and n > 0:
                            tri_counts[name]["net_positive_1000"] += 1
                            tri_pos[(name,)] = {"bps": n / 1000.0 * 1e4}
            tri_eps.update(t, tri_pos)

    # ---- summarise ----
    quality = {}
    for v in set(venue_seen) | set(venue_crossed):
        devs = venue_dev.get(v, [])
        total = venue_seen.get(v, 0) + venue_crossed.get(v, 0)
        crossed_share = venue_crossed.get(v, 0) / total if total else 0.0
        med = pct(devs, 0.5)
        quality[v] = {"crossed_book_share": round(crossed_share, 4),
                      "mid_dev_bps_median": med, "mid_dev_bps_p90": pct(devs, 0.9),
                      "suspect": bool((med is not None and med > SUSPECT_MEDIAN_DEV_BPS)
                                      or crossed_share > SUSPECT_CROSSED_SHARE)}
    out = {"excluded_venues": list(exclude), "venue_quality": quality,
           "samples": samples, "stale_books_dropped": stale_dropped,
           "venue_book_samples": dict(venue_seen),
           "venue_lag_ms_median": {v: statistics.median(l) for v, l in venue_lag.items() if l},
           "cross_venue": {}, "gross_best_bps_by_symbol": {}, "triangular": {}}

    for sym, vals in gross_bps_best.items():
        out["gross_best_bps_by_symbol"][sym] = {
            "median": pct(vals, 0.5), "p90": pct(vals, 0.9), "p99": pct(vals, 0.99),
            "max": max(vals), "share_crossed": sum(v > 0 for v in vals) / len(vals)}

    for scen in FEE_SCENARIOS:
        eps = cross_eps[scen].finish()
        durations = [e["samples"] for e in eps]
        survived = [e for e in eps if e["samples"] >= 2]
        upper_bound = sum(e["first"]["max_net_usd"] for e in eps)
        # Arriving one sample late you can only take what is still there at the second sample.
        upper_bound_survived = sum(e["second"]["max_net_usd"] for e in survived)
        by_key = defaultdict(lambda: {"episodes": 0, "upper_bound_usd": 0.0})
        for e in eps:
            k = "|".join(e["key"])
            by_key[k]["episodes"] += 1
            by_key[k]["upper_bound_usd"] += e["first"]["max_net_usd"]
        top = sorted(by_key.items(), key=lambda kv: -kv[1]["upper_bound_usd"])[:15]
        out["cross_venue"][scen] = {
            "funnel": dict(funnel[scen]),
            "episodes": len(eps),
            "episodes_surviving_1_sample": len(survived),
            "episodes_surviving_3_samples": sum(e["samples"] >= 4 for e in eps),
            "duration_samples_median": pct(durations, 0.5),
            "upper_bound_profit_usd_all": round(upper_bound, 2),
            "upper_bound_profit_usd_if_1s_late": round(upper_bound_survived, 2),
            "top_routes": [{"route": k, **v} for k, v in top],
        }

    tri_eps_list = tri_eps.finish()
    for name, c in tri_counts.items():
        vals = tri_best_bps[name]
        out["triangular"][name] = {**c, "gross_bps_median": pct(vals, 0.5),
                                   "gross_bps_p99": pct(vals, 0.99), "gross_bps_max": max(vals)}
    out["triangular_episodes_net_positive"] = len(tri_eps_list)
    out["triangular_episodes_surviving_1_sample"] = sum(e["samples"] >= 2 for e in tri_eps_list)
    return out


def print_report(s: dict) -> None:
    print(f"excluded venues: {s['excluded_venues'] or 'none'}")
    print(f"samples={s['samples']} stale_books_dropped={s['stale_books_dropped']}")
    print("venue feed quality (own-book crossed share, |mid - median of other venues| bps):")
    for v, q in sorted(s["venue_quality"].items()):
        med = q["mid_dev_bps_median"]
        p90 = q["mid_dev_bps_p90"]
        print(f"  {v:10s} crossed={q['crossed_book_share']*100:.2f}% "
              f"dev_med={med if med is None else round(med, 2)} dev_p90={p90 if p90 is None else round(p90, 2)}"
              f"{'  SUSPECT' if q['suspect'] else ''}")
    print("venue book-samples:", s["venue_book_samples"])
    print("venue recv-minus-exchange-timestamp median ms:", s["venue_lag_ms_median"])
    print("\nBest top-of-book gross cross per symbol (bps, before fees):")
    for sym, d in s["gross_best_bps_by_symbol"].items():
        print(f"  {sym:10s} median={d['median']:.2f} p90={d['p90']:.2f} p99={d['p99']:.2f} "
              f"max={d['max']:.2f} crossed={d['share_crossed']*100:.1f}%")
    for scen, d in s["cross_venue"].items():
        print(f"\n[{scen}] funnel: {d['funnel']}")
        print(f"  episodes={d['episodes']} survive1={d['episodes_surviving_1_sample']} "
              f"survive3={d['episodes_surviving_3_samples']} median_len={d['duration_samples_median']}")
        print(f"  upper-bound profit (perfect capture once per episode): all=${d['upper_bound_profit_usd_all']}"
              f" | if 1 s late=${d['upper_bound_profit_usd_if_1s_late']}")
        for r in d["top_routes"][:8]:
            print(f"    {r['route']:40s} episodes={r['episodes']:5d} upper_bound=${r['upper_bound_usd']:.2f}")
    print("\nTriangular (retail taker fees, $1000 notional):")
    for name, d in sorted(s["triangular"].items()):
        print(f"  {name:32s} obs={d['observations']:6d} gross+={d.get('gross_positive', 0):5d} "
              f"net+={d.get('net_positive_1000', 0):4d} gross_bps med={d['gross_bps_median']:.2f} "
              f"p99={d['gross_bps_p99']:.2f} max={d['gross_bps_max']:.2f}")
    print(f"  triangular net-positive episodes={s['triangular_episodes_net_positive']} "
          f"surviving 1 sample={s['triangular_episodes_surviving_1_sample']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--out", default=None)
    ap.add_argument("--exclude", default="", help="comma-separated venues to ignore")
    a = ap.parse_args()
    exclude = [v for v in a.exclude.split(",") if v]
    summary = analyze(a.path, exclude)
    print_report(summary)
    result = {"all": summary}
    suspects = [v for v, q in summary["venue_quality"].items() if q["suspect"]]
    if suspects:
        print(f"\n==== re-run excluding suspect feeds: {suspects} ====")
        clean = analyze(a.path, exclude + suspects)
        print_report(clean)
        result["clean"] = clean
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(result, fh, indent=2, default=str)

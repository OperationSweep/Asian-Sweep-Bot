# Arbitrage measurement toolkit

Stage 1 and 2 of the validation plan: collect public order books and measure how many
apparent arbitrage opportunities survive executable prices, depth, fees, quote age and
a one-second execution delay. **No API keys and no order placement exist anywhere in
this package.**

| File | Purpose |
|---|---|
| `book_math.py` | Pure depth-walk arithmetic: cross-venue fills, max profitable size, triangular cycles |
| `arb_config.py` | Venues, symbols, taker-fee table with sources, quality gates |
| `collector.py` | WebSocket order-book collector (ccxt.pro), snapshots all books once a second to `.jsonl.gz` |
| `analyze.py` | Opportunity funnel, episode persistence, fee-scenario comparison, triangular scan |
| `tests/` | Unit tests for the arithmetic |

```bash
pip install -r arb/requirements.txt
python -m pytest -q arb/tests
python -m arb.collector --minutes 30 --out data/books.jsonl.gz
python -m arb.analyze data/books.jsonl.gz --out data/summary.json
```

The `arb-collect` GitHub Actions workflow runs the same steps on a cloud runner and
uploads the raw data and summary as an artifact. Note that runners sit in the US, so
venues that geo-block US IPs (Binance, Bybit) will show up as errors there. Run the
collector from your own region to see the venues you can actually trade.

## What the numbers mean

- **top_of_book_crossed**: best bid on venue B above best ask on venue A. This is the
  "headline spread" most bots advertise. It ignores fees and size.
- **net_positive_at_N**: still profitable after both taker fees when buying N USDT worth
  by walking real depth, with the full size fillable on both books.
- **episodes / survive1**: a run of consecutive one-second samples where the route stays
  net-positive at $100. `survive1` counts episodes still there one sample later, a proxy
  for "would it still exist when my orders arrive".
- **upper_bound_profit**: perfect capture of the max profitable size once per episode,
  with inventory already in place. It is a ceiling, not an expected return: it excludes
  rebalancing, failed legs, competition and adverse selection.


## Hedged market-making (XEMM) paper simulator

`arb/xemm_sim.py` replays the collector's books and trade prints (`--trades`) and
simulates quoting on one venue and hedging on another, spot only, with three fill
models (optimistic, queue-aware realistic, conservative). Only completed
maker-and-hedge cycles count. Pass/fail thresholds are pre-registered in
`arb/xemm_prereg.json`. The `xemm-collect` workflow runs a 60-minute collection
plus the simulation; a push touching the workflow file starts it.

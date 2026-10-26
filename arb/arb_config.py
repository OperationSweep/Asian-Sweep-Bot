"""
Settings for the public-data arbitrage collector and analyzer.

No API keys are used anywhere in this package. Everything here reads public
order books only.

Taker fees are the lowest retail tier with no token discount, checked on
2026-10-26. Re-check them against your own account before trusting any result:
library defaults are often stale (ccxt 4.5.90 ships Kraken at 0.26 % taker,
Kraken's own page says 0.80 % for tier 1).
"""

# venue id (ccxt) -> taker fee fraction, source
TAKER_FEES = {
    "kraken":    (0.0080, "kraken.com/features/fee-schedule, tier 1 ($0+), fetched 2026-10-26"),
    "coinbase":  (0.0120, "bitbo.io Kraken vs Coinbase calculator, $0-1K tier; secondary source"),
    "cryptocom": (0.00075, "coinmarketcap exchange page, <$250K 30d volume; secondary source"),
    "okx":       (0.0010, "bitdegree OKX fees, updated 2026-08-07; secondary source"),
    "binance":   (0.0010, "cryptopotato Binance fees, 2025-10; 0.075 % with BNB"),
    "bybit":     (0.0010, "mexc.com fee comparison, May 2026; secondary source"),
    "kucoin":    (0.0010, "mexc.com fee comparison, May 2026; secondary source"),
    "mexc":      (0.0005, "mexc.com fee comparison, May 2026 (self-reported)"),
    "gate":      (0.0010, "assumed standard 0.10 % tier; verify"),
    "bitget":    (0.0010, "assumed standard 0.10 % tier; verify"),
    "htx":       (0.0020, "assumed standard 0.20 % tier; verify"),
    "bitstamp":  (0.0040, "assumed; verify"),
    "bitfinex":  (0.0020, "assumed standard 0.20 % taker; verify"),
}

# Venues to try. Some are geo-blocked from some regions (Binance and Bybit from
# US cloud IPs, for example); the collector logs and skips those.
VENUES = ["kraken", "coinbase", "cryptocom", "okx", "binance", "bybit", "kucoin",
          "mexc", "gate", "bitget", "htx", "bitstamp", "bitfinex"]

# Cross-venue symbols (all quoted in USDT so prices compare directly) plus the
# BTC-quoted legs needed for triangles.
CROSS_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT",
                 "LINK/USDT", "SUI/USDT", "PEPE/USDT", "USDC/USDT"]
TRIANGLE_LEGS = ["ETH/BTC", "SOL/BTC", "XRP/BTC", "LINK/BTC", "DOGE/BTC"]

# Triangles to evaluate on each venue, both directions.
TRIANGLES = [["USDT", "BTC", "ETH"], ["USDT", "BTC", "SOL"], ["USDT", "BTC", "XRP"],
             ["USDT", "BTC", "LINK"], ["USDT", "BTC", "DOGE"]]

BOOK_DEPTH = 20                  # levels kept per side
SAMPLE_INTERVAL_S = 1.0          # how often the collector snapshots every cached book
NOTIONALS = [100, 500, 1000, 5000]   # USDT trade sizes evaluated

# Analyzer quality gates
MAX_QUOTE_AGE_MS = 1500          # drop a book whose last update is older than this

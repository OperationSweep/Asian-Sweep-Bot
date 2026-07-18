"""Configuration for the Asian Session Liquidity Sweep + BOS bot."""

MT5_LOGIN    = 000000        # Replace with your MT5 account number
MT5_PASSWORD = "your_password"
MT5_SERVER   = "your_broker_server"
LOT_SIZE     = 0.10          # Lot size per trade
MAX_TRADES   = 1             # Max open trades at once
DUBAI_UTC_OFFSET = 4

SYMBOL                  = "EURUSD"
MAGIC_NUMBER            = 20260518
DEVIATION_POINTS        = 20
RR_RATIO                = 2.0
RETRY_COUNT             = 3
RETRY_DELAY_SECONDS     = 5
LOG_FILE                = "bot.log"

NY_TIMEZONE             = "America/New_York"
DUBAI_TIMEZONE          = "Asia/Dubai"

ASIAN_SESSION_START_NY  = (19, 0)
ASIAN_SESSION_END_NY    = (0, 0)

SWEEP_SCAN_START_DUBAI  = "09:00"
SWEEP_SCAN_END_DUBAI    = "13:00"
DAILY_SETUP_DUBAI       = "08:30"
FORCE_CLOSE_DUBAI       = "13:00"
RESET_DUBAI             = "13:05"

SWING_LOOKBACK_CANDLES  = 60
SWING_FRACTAL_WINDOW    = 2

# --------------------------------------------------------------------------- #
# Order-flow confirmation
# After a Break of Structure, the entry is gated on live order flow (tape
# aggressor delta + depth-of-market imbalance) agreeing with the trade
# direction. Set ORDER_FLOW_ENABLED = False to fall back to entering purely on
# structure (original behaviour).
# --------------------------------------------------------------------------- #
ORDER_FLOW_ENABLED             = True
ORDER_FLOW_LOOKBACK_SECONDS    = 90    # tape window used to measure delta
ORDER_FLOW_MIN_TICKS           = 20    # need at least this many ticks to judge
ORDER_FLOW_MIN_DELTA_RATIO     = 0.15  # |buy-sell|/total needed to confirm flow
ORDER_FLOW_USE_BOOK            = True  # factor in DOM imbalance when available
ORDER_FLOW_REQUIRE_BOOK        = False # hard-require DOM (else it is optional)
ORDER_FLOW_MIN_BOOK_IMBALANCE  = 0.10  # resting bid/ask skew tolerance
ORDER_FLOW_CONFIRM_TIMEOUT_MIN = 15    # abort setup if flow never confirms

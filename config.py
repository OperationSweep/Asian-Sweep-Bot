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

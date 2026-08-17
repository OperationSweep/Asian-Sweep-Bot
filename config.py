"""Configuration for the Asian Session Liquidity Sweep research bot."""

# --- MT5 account / broker ---
MT5_LOGIN = 000000
MT5_PASSWORD = "your_password"
MT5_SERVER = "your_broker_server"
SYMBOL = "EURUSD"
MAGIC_NUMBER = 20260518
DEVIATION_POINTS = 20

# --- Runtime modes ---
DRY_RUN = True          # True = signal and journal only, no real order_send
PAPER_MODE = True       # For future broker/demo separation; kept explicit
MAX_TRADES = 1
LOT_SIZE = 0.10

# --- Strategy timing ---
NY_TIMEZONE = "America/New_York"
DUBAI_TIMEZONE = "Asia/Dubai"
ASIAN_SESSION_START_NY = (19, 0)
ASIAN_SESSION_END_NY = (0, 0)
SWEEP_SCAN_START_DUBAI = "09:00"
SWEEP_SCAN_END_DUBAI = "13:00"
DAILY_SETUP_DUBAI = "08:30"
FORCE_CLOSE_DUBAI = "13:00"
RESET_DUBAI = "13:05"

# --- Risk / trade logic ---
RR_RATIO = 2.0
SL_BUFFER_PIPS = 0.5
MAX_SPREAD_PIPS = 1.5
MIN_STOP_PIPS = 2.0
MAX_STOP_PIPS = 15.0
MIN_MINUTES_BEFORE_FORCE_CLOSE = 30
MIN_SWEEP_BUFFER_PIPS = 1.0
MIN_H4_STRUCTURE_PIPS = 20.0
SWING_LOOKBACK_CANDLES = 60
SWING_FRACTAL_WINDOW = 2
MOVE_TO_BE_AT_R = 1.0

# --- Reliability ---
RETRY_COUNT = 3
RETRY_DELAY_SECONDS = 5

# --- Files ---
LOG_FILE = "bot.log"
STATE_FILE = "daily_state.json"
SIGNAL_JOURNAL_FILE = "signals.csv"
TRADE_JOURNAL_FILE = "trades.csv"
EVENT_JOURNAL_FILE = "events.jsonl"

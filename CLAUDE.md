# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An automated EURUSD trading bot implementing an "Asian Session Liquidity Sweep + Break of Structure (BOS)" strategy against a MetaTrader 5 account. The entire application lives in two files: `bot.py` (all logic) and `config.py` (all settings).

## Commands

```bash
pip install -r requirements.txt   # install dependencies
python bot.py                     # run the bot (long-running scheduler loop)
```

There is no test suite, linter, or build step configured.

**Platform caveat:** the `MetaTrader5` package only works on Windows with a running MT5 terminal. `bot.py` guards the import (`mt5` becomes `None` on other platforms), so the module can be imported and statically checked on Linux/macOS, but nothing involving live data or execution can run there. Preserve the `if mt5 is None` guards when editing.

## Configuration

All tunables live in `config.py` as module-level constants: MT5 credentials (placeholders in the repo — never commit real ones), symbol, lot size, risk-reward ratio, retry policy, and the Dubai-time schedule strings (`DAILY_SETUP_DUBAI`, `SWEEP_SCAN_START/END_DUBAI`, `FORCE_CLOSE_DUBAI`, `RESET_DUBAI`). `bot.py` reads them via `import config` / `config.X` — add new settings there rather than hardcoding values in `bot.py`.

## Architecture

`bot.py` is a state machine driven by the `schedule` library, advancing one global `DailyState` dataclass (`STATE`) through a daily lifecycle:

1. **08:30 Dubai — `job_daily_setup`**: resets state, computes 4H bias (`determine_bias`: three closed H4 candles forming HH/HL → BULLISH, LH/LL → BEARISH, else NEUTRAL and the bot sits out), and computes the Asian range (`compute_asian_range`: high/low of 5m candles between 19:00 and 00:00 New York time).
2. **Every 5 minutes within 09:00–13:00 Dubai — `job_scan_tick` → `scan_for_setup`**: first waits for a sweep of the Asian high (bearish bias) or low (bullish bias) via `_check_for_sweep`, then waits for a 5m close beyond the most recent fractal swing (`_check_for_bos` + `find_recent_swing`). BOS confirmation triggers `place_trade` — a market order with SL at the sweep extreme and TP at `RR_RATIO` (1:2). If price runs in the bias direction without sweeping, the day is marked closed with result `SKIP`.
3. **While a trade is open — `manage_open_trade`**: moves SL to break-even once profit reaches 1R; detects external closes (TP/SL hit) and finalizes.
4. **13:00 Dubai — `job_force_close`**: closes all positions on the symbol, then `_finalize_after_close` computes pips/PnL and prints a session summary.
5. **13:05 Dubai — `job_reset`**: wipes `STATE` for the next day.

Key conventions to preserve:

- **Timezones**: all strategy times are anchored to Dubai or New York time via `pytz`; candle timestamps from MT5 are converted to UTC. The `schedule` library uses naive host-local time, so Dubai times are translated with `dubai_hhmm_to_local_hhmm` when registering jobs.
- **Candle indexing**: MT5's `copy_rates_from_pos` returns the still-forming candle last, so the last *closed* candle is `df.iloc[-2]`. All signal logic operates on closed candles only.
- **Resilience**: every MT5 call goes through `_retry` (configurable retry count/delay) and `ensure_connection` (re-initializes on dropped connections). Follow this pattern for any new MT5 interaction; never call `mt5.*` raw in strategy code.
- **Dual output**: user-facing events use `print` with a `[HH:MM]` Dubai timestamp, and everything is also logged via the `log` logger (writes to `bot.log` and stdout). New events should do both.
- **Orders**: all order requests carry `config.MAGIC_NUMBER` and a `comment` identifying the bot, and use IOC filling.

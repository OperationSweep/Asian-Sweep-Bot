"""
Asian Session Liquidity Sweep + Break of Structure trading bot for EURUSD.

Strategy:
    1. Determine 4H bias (last 3 closes -> HH/HL or LH/LL).
    2. Mark the Asian session range (19:00 - 00:00 New York time) on 5m candles.
    3. Wait for a sweep of the Asian high (bearish bias) or low (bullish bias)
       between 09:00 and 13:00 Dubai time.
    4. After a sweep, watch for a Break of Structure on the 5m chart.
    5. Confirm the BOS with live order flow (tape aggressor delta + DOM
       imbalance) agreeing with the trade direction, then execute a market
       order with SL at the sweep extreme and TP at 1:2 RR.
    6. Move SL to break-even at 1R profit, and force close everything at 13:00
       Dubai time.

This module is a single-file, production-ready implementation that uses
MetaTrader5 for market data + execution and the `schedule` library for the
job loop.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time as dtime
from typing import Optional, List

import numpy as np
import pandas as pd
import pytz
import schedule

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - MetaTrader5 is platform specific
    mt5 = None  # type: ignore[assignment]

import config
import orderflow


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def _build_logger() -> logging.Logger:
    logger = logging.getLogger("AsianSweepBot")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

    fh = logging.FileHandler(config.LOG_FILE, mode="a", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


log = _build_logger()


def banner(text: str) -> None:
    line = "=" * 50
    print(line)
    print(text)
    print(line)


# --------------------------------------------------------------------------- #
# Timezone helpers
# --------------------------------------------------------------------------- #
NY_TZ = pytz.timezone(config.NY_TIMEZONE)
DUBAI_TZ = pytz.timezone(config.DUBAI_TIMEZONE)
UTC = pytz.UTC


def now_dubai() -> datetime:
    return datetime.now(DUBAI_TZ)


def now_ny() -> datetime:
    return datetime.now(NY_TZ)


def dubai_hhmm_to_local_hhmm(hhmm: str) -> str:
    """Convert a Dubai HH:MM string to the local machine's HH:MM string.

    `schedule` uses naive local time, so we translate a Dubai-anchored time
    into the host's local clock for today.
    """
    hour, minute = (int(x) for x in hhmm.split(":"))
    dubai_today = now_dubai().replace(hour=hour, minute=minute,
                                      second=0, microsecond=0)
    local_dt = dubai_today.astimezone().replace(tzinfo=None)
    return local_dt.strftime("%H:%M")


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
@dataclass
class DailyState:
    trade_date: Optional[str] = None
    bias: str = "NEUTRAL"
    asian_high: Optional[float] = None
    asian_low: Optional[float] = None

    sweep_detected: bool = False
    sweep_type: Optional[str] = None        # HIGH_SWEEP | LOW_SWEEP
    sweep_extreme: Optional[float] = None
    sweep_candle_time: Optional[datetime] = None

    bos_level: Optional[float] = None
    bos_confirmed: bool = False
    bos_direction: Optional[str] = None     # BUY | SELL (pending entry)
    bos_entry_hint: Optional[float] = None
    bos_confirmed_time: Optional[datetime] = None
    order_flow_confirmed: bool = False

    trade_open: bool = False
    ticket: Optional[int] = None
    entry_price: Optional[float] = None
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    direction: Optional[str] = None         # BUY | SELL
    initial_risk_price: Optional[float] = None
    breakeven_done: bool = False

    closed: bool = False
    exit_price: Optional[float] = None
    pip_result: Optional[float] = None
    pnl: Optional[float] = None
    result_label: Optional[str] = None      # WIN | LOSS | BE

    logged_monitor_msg: bool = False
    monitored_directional_move: bool = False

    def reset(self) -> None:
        for f in self.__dataclass_fields__:  # type: ignore[attr-defined]
            setattr(self, f, self.__dataclass_fields__[f].default)  # type: ignore[attr-defined]


STATE = DailyState()


# --------------------------------------------------------------------------- #
# MetaTrader5 helpers (resilient)
# --------------------------------------------------------------------------- #
def _retry(callable_, *args, **kwargs):
    last_err: Optional[BaseException] = None
    for attempt in range(1, config.RETRY_COUNT + 1):
        try:
            return callable_(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - defensive
            last_err = exc
            log.warning("MT5 call %s failed (attempt %d/%d): %s",
                        getattr(callable_, "__name__", str(callable_)),
                        attempt, config.RETRY_COUNT, exc)
            time.sleep(config.RETRY_DELAY_SECONDS)
    log.error("MT5 call permanently failed: %s", last_err)
    return None


def mt5_initialize() -> bool:
    if mt5 is None:
        log.error("MetaTrader5 library is not installed on this host.")
        return False
    for attempt in range(1, config.RETRY_COUNT + 1):
        try:
            ok = mt5.initialize(login=int(config.MT5_LOGIN),
                                password=config.MT5_PASSWORD,
                                server=config.MT5_SERVER)
            if ok:
                info = mt5.account_info()
                if info is not None:
                    log.info("MT5 connected: login=%s server=%s balance=%.2f",
                             info.login, info.server, info.balance)
                else:
                    log.info("MT5 initialized (no account info).")
                # make sure the symbol is selected
                if not mt5.symbol_select(config.SYMBOL, True):
                    log.warning("Failed to select symbol %s", config.SYMBOL)
                if config.ORDER_FLOW_ENABLED:
                    orderflow.subscribe_book()
                return True
            err = mt5.last_error()
            log.warning("MT5 initialize failed (attempt %d/%d): %s",
                        attempt, config.RETRY_COUNT, err)
        except Exception as exc:
            log.warning("MT5 initialize raised (attempt %d/%d): %s",
                        attempt, config.RETRY_COUNT, exc)
        time.sleep(config.RETRY_DELAY_SECONDS)
    log.error("MT5 could not be initialized after %d attempts",
              config.RETRY_COUNT)
    return False


def mt5_shutdown() -> None:
    if mt5 is None:
        return
    if config.ORDER_FLOW_ENABLED:
        orderflow.release_book()
    try:
        mt5.shutdown()
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("mt5.shutdown raised: %s", exc)


def ensure_connection() -> bool:
    if mt5 is None:
        return False
    try:
        info = mt5.terminal_info()
        if info is not None and getattr(info, "connected", True):
            return True
    except Exception:
        pass
    log.warning("MT5 connection lost - re-initialising.")
    mt5_shutdown()
    return mt5_initialize()


def fetch_rates(timeframe: int, n: int) -> Optional[pd.DataFrame]:
    if not ensure_connection():
        return None
    rates = _retry(mt5.copy_rates_from_pos, config.SYMBOL, timeframe, 0, n)
    if rates is None or len(rates) == 0:
        log.error("No rates returned for %s tf=%s n=%d",
                  config.SYMBOL, timeframe, n)
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def fetch_rates_range(timeframe: int,
                      start_utc: datetime,
                      end_utc: datetime) -> Optional[pd.DataFrame]:
    if not ensure_connection():
        return None
    rates = _retry(mt5.copy_rates_range, config.SYMBOL, timeframe,
                   start_utc, end_utc)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def symbol_point() -> float:
    info = mt5.symbol_info(config.SYMBOL) if mt5 is not None else None
    if info is None:
        return 0.00001
    return info.point


def pip_size() -> float:
    """For 5-digit FX brokers a pip == 10 * point."""
    info = mt5.symbol_info(config.SYMBOL) if mt5 is not None else None
    if info is None:
        return 0.0001
    if info.digits in (3, 5):
        return info.point * 10
    return info.point


def latest_tick() -> Optional[object]:
    if not ensure_connection():
        return None
    return _retry(mt5.symbol_info_tick, config.SYMBOL)


# --------------------------------------------------------------------------- #
# Strategy: bias
# --------------------------------------------------------------------------- #
def determine_bias() -> str:
    """Bias = direction of last 3 closed H4 candles via HH/HL or LH/LL."""
    df = fetch_rates(mt5.TIMEFRAME_H4, 10) if mt5 is not None else None
    if df is None or len(df) < 4:
        log.warning("Not enough H4 data to compute bias.")
        return "NEUTRAL"

    # last fully-closed candle is the second-to-last in copy_rates_from_pos
    closed = df.iloc[:-1].tail(3)
    if len(closed) < 3:
        return "NEUTRAL"

    highs = closed["high"].values
    lows = closed["low"].values

    higher_highs = highs[0] < highs[1] < highs[2]
    higher_lows = lows[0] < lows[1] < lows[2]
    lower_highs = highs[0] > highs[1] > highs[2]
    lower_lows = lows[0] > lows[1] > lows[2]

    if higher_highs and higher_lows:
        return "BULLISH"
    if lower_highs and lower_lows:
        return "BEARISH"
    return "NEUTRAL"


# --------------------------------------------------------------------------- #
# Strategy: Asian range
# --------------------------------------------------------------------------- #
def compute_asian_range() -> Optional[tuple[float, float]]:
    """Asian session = 19:00 -> 00:00 New York local time.

    For the current Dubai trading day, the Asian window is the most recently
    completed 19:00 NY -> 00:00 NY block.
    """
    if mt5 is None:
        return None

    today_ny = now_ny().date()
    start_ny_naive = datetime.combine(today_ny - timedelta(days=1),
                                      dtime(19, 0))
    end_ny_naive = datetime.combine(today_ny, dtime(0, 0))

    start_ny = NY_TZ.localize(start_ny_naive)
    end_ny = NY_TZ.localize(end_ny_naive)
    start_utc = start_ny.astimezone(UTC)
    end_utc = end_ny.astimezone(UTC)

    df = fetch_rates_range(mt5.TIMEFRAME_M5, start_utc, end_utc)
    if df is None or df.empty:
        log.error("Asian range fetch returned no candles.")
        return None

    asian_high = float(df["high"].max())
    asian_low = float(df["low"].min())
    return asian_high, asian_low


# --------------------------------------------------------------------------- #
# Strategy: swing detection
# --------------------------------------------------------------------------- #
def find_recent_swing(df: pd.DataFrame, kind: str,
                      before_time: datetime) -> Optional[float]:
    """Locate the most recent fractal swing high/low strictly before
    `before_time`.

    A swing high at index i requires highs[i] strictly greater than the
    `SWING_FRACTAL_WINDOW` highs on either side; mirror for swing low.
    """
    w = config.SWING_FRACTAL_WINDOW
    sub = df[df["time"] < before_time].copy()
    if len(sub) < (2 * w + 1):
        return None

    highs = sub["high"].values
    lows = sub["low"].values

    candidates: List[float] = []
    for i in range(w, len(sub) - w):
        if kind == "HIGH":
            window = highs[i - w: i + w + 1]
            if highs[i] == window.max() and (window == highs[i]).sum() == 1:
                candidates.append(highs[i])
        else:
            window = lows[i - w: i + w + 1]
            if lows[i] == window.min() and (window == lows[i]).sum() == 1:
                candidates.append(lows[i])
    if not candidates:
        return None
    return float(candidates[-1])


# --------------------------------------------------------------------------- #
# Strategy: sweep + BOS scan
# --------------------------------------------------------------------------- #
def fmt_price(price: Optional[float]) -> str:
    if price is None:
        return "N/A"
    info = mt5.symbol_info(config.SYMBOL) if mt5 is not None else None
    digits = info.digits if info is not None else 5
    return f"{price:.{digits}f}"


def scan_for_setup() -> None:
    """Runs every 5 minutes during the Dubai scan window."""
    if STATE.closed or STATE.trade_open:
        # Trade management handled separately; nothing to detect.
        if STATE.trade_open:
            manage_open_trade()
        return

    if STATE.bias == "NEUTRAL":
        return

    if STATE.asian_high is None or STATE.asian_low is None:
        log.warning("Asian range not set yet - skipping scan tick.")
        return

    if not STATE.sweep_detected:
        _check_for_sweep()
        return

    if not STATE.bos_confirmed:
        _check_for_bos()
        return

    if not STATE.order_flow_confirmed:
        _confirm_order_flow_and_enter()


def _check_for_sweep() -> None:
    df = fetch_rates(mt5.TIMEFRAME_M5, 3)
    if df is None or len(df) < 2:
        return
    last_closed = df.iloc[-2]
    candle_high = float(last_closed["high"])
    candle_low = float(last_closed["low"])
    candle_close = float(last_closed["close"])
    candle_time = last_closed["time"].to_pydatetime()

    now_str = now_dubai().strftime("[%H:%M]")

    if STATE.bias == "BEARISH":
        if not STATE.logged_monitor_msg:
            print(f"{now_str} Monitoring for HIGH sweep above "
                  f"{fmt_price(STATE.asian_high)}...")
            log.info("Monitoring for HIGH sweep above %s",
                     fmt_price(STATE.asian_high))
            STATE.logged_monitor_msg = True

        if candle_high > STATE.asian_high:
            STATE.sweep_detected = True
            STATE.sweep_type = "HIGH_SWEEP"
            STATE.sweep_extreme = candle_high
            STATE.sweep_candle_time = candle_time
            STATE.logged_monitor_msg = False
            print(f"{now_str} SWEEP DETECTED - Price spiked to "
                  f"{fmt_price(candle_high)} (above Asian High)")
            log.info("SWEEP DETECTED type=HIGH price=%s asian_high=%s",
                     fmt_price(candle_high), fmt_price(STATE.asian_high))
            return

        # No sweep but trending in bias direction -> abort for today
        if candle_close < STATE.asian_low and not STATE.monitored_directional_move:
            STATE.monitored_directional_move = True
            log.info("No sweep - price moving in bias direction without "
                     "taking liquidity. Skipping trade today.")
            print(f"{now_str} No sweep - skipping trade today")
            STATE.closed = True
            STATE.result_label = "SKIP"

    elif STATE.bias == "BULLISH":
        if not STATE.logged_monitor_msg:
            print(f"{now_str} Monitoring for LOW sweep below "
                  f"{fmt_price(STATE.asian_low)}...")
            log.info("Monitoring for LOW sweep below %s",
                     fmt_price(STATE.asian_low))
            STATE.logged_monitor_msg = True

        if candle_low < STATE.asian_low:
            STATE.sweep_detected = True
            STATE.sweep_type = "LOW_SWEEP"
            STATE.sweep_extreme = candle_low
            STATE.sweep_candle_time = candle_time
            STATE.logged_monitor_msg = False
            print(f"{now_str} SWEEP DETECTED - Price spiked to "
                  f"{fmt_price(candle_low)} (below Asian Low)")
            log.info("SWEEP DETECTED type=LOW price=%s asian_low=%s",
                     fmt_price(candle_low), fmt_price(STATE.asian_low))
            return

        if candle_close > STATE.asian_high and not STATE.monitored_directional_move:
            STATE.monitored_directional_move = True
            log.info("No sweep - price moving in bias direction without "
                     "taking liquidity. Skipping trade today.")
            print(f"{now_str} No sweep - skipping trade today")
            STATE.closed = True
            STATE.result_label = "SKIP"


def _check_for_bos() -> None:
    df = fetch_rates(mt5.TIMEFRAME_M5, config.SWING_LOOKBACK_CANDLES)
    if df is None or len(df) < 5 or STATE.sweep_candle_time is None:
        return
    last_closed = df.iloc[-2]
    candle_close = float(last_closed["close"])
    candle_time = last_closed["time"].to_pydatetime()
    now_str = now_dubai().strftime("[%H:%M]")

    if STATE.sweep_type == "HIGH_SWEEP":
        swing = find_recent_swing(df, "LOW", STATE.sweep_candle_time)
        if swing is None:
            log.info("BOS scan: no swing low identified yet.")
            return
        if STATE.bos_level != swing:
            STATE.bos_level = swing
            print(f"{now_str} Monitoring for BOS below swing low: "
                  f"{fmt_price(swing)}...")
            log.info("Monitoring BOS below swing low %s", fmt_price(swing))
        if candle_close < swing and candle_time > STATE.sweep_candle_time:
            _register_bos("SELL", candle_close, candle_time)

    elif STATE.sweep_type == "LOW_SWEEP":
        swing = find_recent_swing(df, "HIGH", STATE.sweep_candle_time)
        if swing is None:
            log.info("BOS scan: no swing high identified yet.")
            return
        if STATE.bos_level != swing:
            STATE.bos_level = swing
            print(f"{now_str} Monitoring for BOS above swing high: "
                  f"{fmt_price(swing)}...")
            log.info("Monitoring BOS above swing high %s", fmt_price(swing))
        if candle_close > swing and candle_time > STATE.sweep_candle_time:
            _register_bos("BUY", candle_close, candle_time)


# --------------------------------------------------------------------------- #
# Order-flow confirmation gate
# --------------------------------------------------------------------------- #
def _register_bos(direction: str, entry_hint: float,
                  candle_time: datetime) -> None:
    """Latch a confirmed BOS and hand off to the order-flow gate for entry."""
    STATE.bos_confirmed = True
    STATE.bos_direction = direction
    STATE.bos_entry_hint = entry_hint
    STATE.bos_confirmed_time = candle_time
    now_str = now_dubai().strftime("[%H:%M]")
    print(f"{now_str} BOS CONFIRMED - 5m candle closed at "
          f"{fmt_price(entry_hint)}")
    log.info("BOS CONFIRMED close=%s dir=%s",
             fmt_price(entry_hint), direction)
    # Attempt an immediate confirmation; otherwise the scan loop retries.
    _confirm_order_flow_and_enter()


def _confirm_order_flow_and_enter() -> None:
    """Gate the pending BOS entry on live order flow agreeing with direction.

    Retried each scan tick until flow confirms, the setup times out, or the
    session is force-closed. When ORDER_FLOW_ENABLED is off this passes through
    to a structure-only entry (original behaviour).
    """
    if STATE.trade_open or STATE.closed:
        return
    direction = STATE.bos_direction
    if direction is None or STATE.bos_entry_hint is None:
        return

    now_str = now_dubai().strftime("[%H:%M]")

    if not config.ORDER_FLOW_ENABLED:
        STATE.order_flow_confirmed = True
        place_trade(direction=direction, entry_hint=STATE.bos_entry_hint)
        return

    signal = orderflow.evaluate_order_flow(direction)
    if signal is not None and signal.agrees:
        STATE.order_flow_confirmed = True
        print(f"{now_str} ORDER FLOW CONFIRMED - {signal.summary()}")
        log.info("Order flow confirmed entry: %s", signal.summary())
        place_trade(direction=direction, entry_hint=STATE.bos_entry_hint)
        return

    if signal is None:
        log.info("Order flow: awaiting data before entering %s.", direction)
    else:
        print(f"{now_str} Order flow not confirming - waiting "
              f"({signal.summary()})")
        log.info("Order flow rejected entry: %s", signal.summary())

    # Abandon the setup if flow never lines up within the allowed window.
    if STATE.bos_confirmed_time is not None:
        elapsed_min = (now_dubai() - STATE.bos_confirmed_time
                       ).total_seconds() / 60.0
        if elapsed_min >= config.ORDER_FLOW_CONFIRM_TIMEOUT_MIN:
            print(f"{now_str} Order flow never confirmed within "
                  f"{config.ORDER_FLOW_CONFIRM_TIMEOUT_MIN}m - skipping trade")
            log.info("Order-flow confirmation timed out after %.1fm - "
                     "skipping trade.", elapsed_min)
            STATE.closed = True
            STATE.result_label = "SKIP-OF"


# --------------------------------------------------------------------------- #
# Execution
# --------------------------------------------------------------------------- #
def place_trade(direction: str, entry_hint: float) -> None:
    if not ensure_connection():
        log.error("Cannot place trade - no MT5 connection.")
        return

    positions = mt5.positions_get(symbol=config.SYMBOL) or []
    if len(positions) >= config.MAX_TRADES:
        log.warning("MAX_TRADES (%d) already open - skipping new entry.",
                    config.MAX_TRADES)
        return

    tick = latest_tick()
    if tick is None:
        log.error("No tick data for entry.")
        return

    if direction == "SELL":
        price = float(tick.bid)
        order_type = mt5.ORDER_TYPE_SELL
        sl = float(STATE.sweep_extreme)
        risk = sl - price
        if risk <= 0:
            log.error("Invalid risk distance for SELL: entry=%.5f sl=%.5f",
                      price, sl)
            return
        tp = price - config.RR_RATIO * risk
    else:
        price = float(tick.ask)
        order_type = mt5.ORDER_TYPE_BUY
        sl = float(STATE.sweep_extreme)
        risk = price - sl
        if risk <= 0:
            log.error("Invalid risk distance for BUY: entry=%.5f sl=%.5f",
                      price, sl)
            return
        tp = price + config.RR_RATIO * risk

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": config.SYMBOL,
        "volume": float(config.LOT_SIZE),
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": config.DEVIATION_POINTS,
        "magic": config.MAGIC_NUMBER,
        "comment": "AsianSweep_BOS",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = _retry(mt5.order_send, request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        rc = getattr(result, "retcode", "n/a")
        log.error("Order send failed retcode=%s result=%s", rc, result)
        return

    STATE.trade_open = True
    STATE.ticket = int(result.order)
    STATE.entry_price = float(result.price)
    STATE.sl_price = sl
    STATE.tp_price = tp
    STATE.direction = direction
    STATE.initial_risk_price = abs(STATE.entry_price - sl)

    now_str = now_dubai().strftime("[%H:%M]")
    arrow = "SELL" if direction == "SELL" else "BUY"
    print(f"{now_str} {arrow} ORDER PLACED")
    print(f"         Entry : {fmt_price(STATE.entry_price)}")
    print(f"         SL    : {fmt_price(sl)}  (sweep extreme)")
    print(f"         TP    : {fmt_price(tp)}  (1:{int(config.RR_RATIO)} RR)")
    print(f"         Lots  : {config.LOT_SIZE:.2f}")
    log.info("Trade opened ticket=%s dir=%s entry=%s sl=%s tp=%s lots=%.2f",
             STATE.ticket, direction,
             fmt_price(STATE.entry_price), fmt_price(sl), fmt_price(tp),
             config.LOT_SIZE)


# --------------------------------------------------------------------------- #
# Trade management
# --------------------------------------------------------------------------- #
def manage_open_trade() -> None:
    if not STATE.trade_open or STATE.ticket is None:
        return
    if not ensure_connection():
        return

    positions = mt5.positions_get(ticket=STATE.ticket) or []
    if not positions:
        # Position was closed externally (TP/SL hit, manual close, etc.)
        _finalize_after_close()
        return

    pos = positions[0]
    tick = latest_tick()
    if tick is None:
        return

    if STATE.direction == "SELL":
        current = float(tick.bid)
        profit_dist = STATE.entry_price - current
    else:
        current = float(tick.ask)
        profit_dist = current - STATE.entry_price

    if not STATE.breakeven_done and STATE.initial_risk_price \
            and profit_dist >= STATE.initial_risk_price:
        _move_to_breakeven(pos)


def _move_to_breakeven(position) -> None:
    new_sl = float(STATE.entry_price)
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": config.SYMBOL,
        "position": position.ticket,
        "sl": new_sl,
        "tp": float(STATE.tp_price),
        "magic": config.MAGIC_NUMBER,
    }
    result = _retry(mt5.order_send, request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        log.error("Failed to move SL to BE retcode=%s",
                  getattr(result, "retcode", "n/a"))
        return
    STATE.breakeven_done = True
    STATE.sl_price = new_sl
    now_str = now_dubai().strftime("[%H:%M]")
    print(f"{now_str} Break-even activated - SL moved to "
          f"{fmt_price(new_sl)}")
    log.info("Break-even SL moved to %s", fmt_price(new_sl))


def force_close_all() -> None:
    """Force-close any open EURUSD positions at 13:00 Dubai."""
    if mt5 is None or not ensure_connection():
        return
    positions = mt5.positions_get(symbol=config.SYMBOL) or []
    now_str = now_dubai().strftime("[%H:%M]")
    if not positions:
        log.info("Force-close tick: no open %s positions.", config.SYMBOL)
        return

    print(f"{now_str} Time exit - closing all {config.SYMBOL} positions")
    log.info("Force-close starting for %d positions.", len(positions))

    for pos in positions:
        _close_position(pos)
    _finalize_after_close()


def _close_position(position) -> None:
    tick = latest_tick()
    if tick is None:
        log.error("No tick for closing position %s", position.ticket)
        return
    if position.type == mt5.POSITION_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = float(tick.bid)
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = float(tick.ask)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": config.SYMBOL,
        "volume": float(position.volume),
        "type": order_type,
        "position": position.ticket,
        "price": price,
        "deviation": config.DEVIATION_POINTS,
        "magic": config.MAGIC_NUMBER,
        "comment": "AsianSweep_ForceClose",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = _retry(mt5.order_send, request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        log.error("Close failed for ticket %s retcode=%s",
                  position.ticket, getattr(result, "retcode", "n/a"))
        return
    log.info("Closed position %s at %s", position.ticket, fmt_price(price))
    STATE.exit_price = price


def _finalize_after_close() -> None:
    if STATE.closed:
        return
    STATE.closed = True
    STATE.trade_open = False

    exit_price = STATE.exit_price
    if exit_price is None:
        tick = latest_tick()
        if tick is not None:
            exit_price = float(tick.bid if STATE.direction == "SELL"
                               else tick.ask)
            STATE.exit_price = exit_price

    if exit_price is None or STATE.entry_price is None:
        return

    pip = pip_size() or 0.0001
    if STATE.direction == "SELL":
        pip_diff = (STATE.entry_price - exit_price) / pip
    else:
        pip_diff = (exit_price - STATE.entry_price) / pip

    STATE.pip_result = round(pip_diff, 1)

    # Approximate $ PnL (assumes $10 / pip / 1.0 lot on EURUSD)
    pnl = STATE.pip_result * 10.0 * (config.LOT_SIZE / 1.0)
    STATE.pnl = round(pnl, 2)

    if STATE.pip_result > 0:
        STATE.result_label = "WIN"
    elif STATE.pip_result < 0:
        STATE.result_label = "LOSS"
    else:
        STATE.result_label = "BE"

    now_str = now_dubai().strftime("[%H:%M]")
    sign = "+" if STATE.pip_result >= 0 else ""
    sign_pnl = "+" if STATE.pnl >= 0 else ""
    print(f"{now_str} Trade closed. Result: {sign}{STATE.pip_result:g} pips "
          f"| Net P&L: {sign_pnl}${STATE.pnl:.2f}")
    log.info("Trade finalized pips=%s pnl=%.2f result=%s",
             STATE.pip_result, STATE.pnl, STATE.result_label)
    _print_session_summary()


def _print_session_summary() -> None:
    line = "=" * 50
    print(line)
    print("SESSION SUMMARY")
    date_str = STATE.trade_date or now_dubai().strftime("%Y-%m-%d")
    direction_text = "N/A"
    if STATE.direction == "SELL":
        direction_text = "SELL (Bearish sweep)"
    elif STATE.direction == "BUY":
        direction_text = "BUY (Bullish sweep)"
    pip_text = "0"
    if STATE.pip_result is not None:
        pip_text = f"{'+' if STATE.pip_result >= 0 else ''}{STATE.pip_result:g}"
    print(f"Date       : {date_str}")
    print(f"Direction  : {direction_text}")
    print(f"Entry      : {fmt_price(STATE.entry_price)}")
    print(f"Exit       : {fmt_price(STATE.exit_price)}")
    print(f"Pips       : {pip_text}")
    print(f"Result     : {STATE.result_label or 'N/A'}")
    print(line)


# --------------------------------------------------------------------------- #
# Scheduled jobs
# --------------------------------------------------------------------------- #
def job_daily_setup() -> None:
    log.info("Daily setup job triggered.")
    STATE.reset()
    STATE.trade_date = now_dubai().strftime("%Y-%m-%d")

    if not ensure_connection():
        log.error("Daily setup aborted - MT5 connection unavailable.")
        return

    bias = determine_bias()
    STATE.bias = bias
    now_str = now_dubai().strftime("[%H:%M]")
    print(f"{now_str} 4H Bias determined: {bias}")
    log.info("4H bias = %s", bias)

    if bias == "NEUTRAL":
        log.info("Bias neutral - bot will sit out today.")
        STATE.closed = True
        STATE.result_label = "NO TRADE"
        return

    rng = compute_asian_range()
    if rng is None:
        log.error("Could not compute Asian range - aborting setup.")
        STATE.closed = True
        STATE.result_label = "NO DATA"
        return

    STATE.asian_high, STATE.asian_low = rng
    print(f"{now_str} Asian Range -> High: {fmt_price(STATE.asian_high)} "
          f"| Low: {fmt_price(STATE.asian_low)}")
    log.info("Asian range high=%s low=%s",
             fmt_price(STATE.asian_high), fmt_price(STATE.asian_low))


def job_scan_tick() -> None:
    if not _within_scan_window():
        return
    try:
        scan_for_setup()
        if STATE.trade_open:
            manage_open_trade()
    except Exception as exc:  # pragma: no cover
        log.exception("scan tick error: %s", exc)


def _within_scan_window() -> bool:
    now = now_dubai().time()
    start_h, start_m = (int(x) for x in config.SWEEP_SCAN_START_DUBAI.split(":"))
    end_h, end_m = (int(x) for x in config.SWEEP_SCAN_END_DUBAI.split(":"))
    start = dtime(start_h, start_m)
    end = dtime(end_h, end_m)
    return start <= now <= end


def job_force_close() -> None:
    try:
        force_close_all()
    except Exception as exc:  # pragma: no cover
        log.exception("force_close error: %s", exc)


def job_reset() -> None:
    log.info("Daily reset job triggered.")
    STATE.reset()


# --------------------------------------------------------------------------- #
# Scheduler bootstrap
# --------------------------------------------------------------------------- #
def configure_schedule() -> None:
    schedule.clear()
    schedule.every().day.at(
        dubai_hhmm_to_local_hhmm(config.DAILY_SETUP_DUBAI)
    ).do(job_daily_setup)
    schedule.every(5).minutes.do(job_scan_tick)
    schedule.every().day.at(
        dubai_hhmm_to_local_hhmm(config.FORCE_CLOSE_DUBAI)
    ).do(job_force_close)
    schedule.every().day.at(
        dubai_hhmm_to_local_hhmm(config.RESET_DUBAI)
    ).do(job_reset)
    log.info("Schedule configured: setup=%s scan=every 5m close=%s reset=%s "
             "(Dubai)",
             config.DAILY_SETUP_DUBAI, config.FORCE_CLOSE_DUBAI,
             config.RESET_DUBAI)


def run() -> None:
    banner("ASIAN SESSION LIQUIDITY SWEEP BOT - EURUSD")
    if not mt5_initialize():
        log.error("Initial MT5 connection failed - exiting.")
        return
    configure_schedule()

    # If we start mid-session and no setup has run today, kick one off.
    now = now_dubai().time()
    if now >= dtime(*[int(x) for x in config.DAILY_SETUP_DUBAI.split(":")]) \
            and STATE.trade_date is None:
        try:
            job_daily_setup()
        except Exception as exc:  # pragma: no cover
            log.exception("Initial setup failed: %s", exc)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Interrupted - shutting down.")
    finally:
        mt5_shutdown()


if __name__ == "__main__":
    run()

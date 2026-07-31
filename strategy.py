from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time as dtime
from typing import Optional

import pandas as pd
import pytz

import config
from datafeed import fetch_rates, fetch_rates_range, mt5, pip_size, spread_pips
from state_store import DailyState

NY_TZ = pytz.timezone(config.NY_TIMEZONE)
DUBAI_TZ = pytz.timezone(config.DUBAI_TIMEZONE)
UTC = pytz.UTC


@dataclass
class SetupDecision:
    allowed: bool
    reason: str
    stop_distance_pips: Optional[float] = None
    spread_pips: Optional[float] = None


def now_dubai() -> datetime:
    return datetime.now(DUBAI_TZ)


def determine_bias() -> str:
    if mt5 is None:
        return "NEUTRAL"
    df = fetch_rates(mt5.TIMEFRAME_H4, 10)
    if df is None or len(df) < 4:
        return "NEUTRAL"
    closed = df.iloc[:-1].tail(3)
    highs = closed["high"].values
    lows = closed["low"].values

    structure_pips = (max(highs) - min(lows)) / pip_size()
    if structure_pips < config.MIN_H4_STRUCTURE_PIPS:
        return "NEUTRAL"

    if highs[0] < highs[1] < highs[2] and lows[0] < lows[1] < lows[2]:
        return "BULLISH"
    if highs[0] > highs[1] > highs[2] and lows[0] > lows[1] > lows[2]:
        return "BEARISH"
    return "NEUTRAL"


def compute_asian_range() -> Optional[tuple[float, float]]:
    if mt5 is None:
        return None
    today_ny = datetime.now(NY_TZ).date()
    start_ny = NY_TZ.localize(datetime.combine(today_ny - timedelta(days=1), dtime(*config.ASIAN_SESSION_START_NY)))
    end_ny = NY_TZ.localize(datetime.combine(today_ny, dtime(*config.ASIAN_SESSION_END_NY)))
    df = fetch_rates_range(mt5.TIMEFRAME_M5, start_ny.astimezone(UTC), end_ny.astimezone(UTC))
    if df is None or df.empty:
        return None
    return float(df["high"].max()), float(df["low"].min())


def find_recent_swing(df: pd.DataFrame, kind: str, before_time: datetime) -> Optional[float]:
    w = config.SWING_FRACTAL_WINDOW
    sub = df[df["time"] < before_time].copy()
    if len(sub) < (2 * w + 1):
        return None
    series = sub["high"].values if kind == "HIGH" else sub["low"].values
    candidates: list[float] = []
    for i in range(w, len(sub) - w):
        window = series[i - w:i + w + 1]
        if kind == "HIGH" and series[i] == window.max() and (window == series[i]).sum() == 1:
            candidates.append(series[i])
        if kind == "LOW" and series[i] == window.min() and (window == series[i]).sum() == 1:
            candidates.append(series[i])
    return float(candidates[-1]) if candidates else None


def detect_sweep(state: DailyState) -> Optional[dict]:
    if mt5 is None or state.asian_high is None or state.asian_low is None:
        return None
    df = fetch_rates(mt5.TIMEFRAME_M5, 3)
    if df is None or len(df) < 2:
        return None
    candle = df.iloc[-2]
    high = float(candle["high"])
    low = float(candle["low"])
    close = float(candle["close"])
    t = candle["time"].to_pydatetime()

    if state.bias == "BEARISH":
        if close < state.asian_low:
            return {"event": "INVALID", "reason": "moved_with_bias_before_sweep"}
        if high >= state.asian_high + config.MIN_SWEEP_BUFFER_PIPS * pip_size():
            return {"event": "SWEEP", "sweep_type": "HIGH_SWEEP", "sweep_extreme": high, "time": t}
    elif state.bias == "BULLISH":
        if close > state.asian_high:
            return {"event": "INVALID", "reason": "moved_with_bias_before_sweep"}
        if low <= state.asian_low - config.MIN_SWEEP_BUFFER_PIPS * pip_size():
            return {"event": "SWEEP", "sweep_type": "LOW_SWEEP", "sweep_extreme": low, "time": t}
    return None


def detect_bos(state: DailyState) -> Optional[dict]:
    if mt5 is None or not state.sweep_time_iso:
        return None
    df = fetch_rates(mt5.TIMEFRAME_M5, config.SWING_LOOKBACK_CANDLES)
    if df is None or len(df) < 5:
        return None
    sweep_time = datetime.fromisoformat(state.sweep_time_iso)
    last_closed = df.iloc[-2]
    candle_close = float(last_closed["close"])
    candle_time = last_closed["time"].to_pydatetime()

    if state.sweep_type == "HIGH_SWEEP":
        level = find_recent_swing(df, "LOW", sweep_time)
        if level is not None and candle_time > sweep_time and candle_close < level:
            return {"event": "BOS", "level": level, "time": candle_time, "signal_price": candle_close}
    elif state.sweep_type == "LOW_SWEEP":
        level = find_recent_swing(df, "HIGH", sweep_time)
        if level is not None and candle_time > sweep_time and candle_close > level:
            return {"event": "BOS", "level": level, "time": candle_time, "signal_price": candle_close}
    return None


def qualify_trade(direction: str, signal_price: float, sweep_extreme: float) -> SetupDecision:
    spread = spread_pips()
    if spread is None:
        return SetupDecision(False, "no_spread_data")
    if spread > config.MAX_SPREAD_PIPS:
        return SetupDecision(False, "spread_too_wide", spread_pips=spread)

    if direction == "SELL":
        sl = sweep_extreme + config.SL_BUFFER_PIPS * pip_size()
        stop_pips = abs(sl - signal_price) / pip_size()
    else:
        sl = sweep_extreme - config.SL_BUFFER_PIPS * pip_size()
        stop_pips = abs(signal_price - sl) / pip_size()

    if stop_pips < config.MIN_STOP_PIPS:
        return SetupDecision(False, "stop_too_small", stop_distance_pips=stop_pips, spread_pips=spread)
    if stop_pips > config.MAX_STOP_PIPS:
        return SetupDecision(False, "stop_too_large", stop_distance_pips=stop_pips, spread_pips=spread)

    minutes_left = _minutes_until_force_close()
    if minutes_left < config.MIN_MINUTES_BEFORE_FORCE_CLOSE:
        return SetupDecision(False, "too_close_to_force_close", stop_distance_pips=stop_pips, spread_pips=spread)

    return SetupDecision(True, "qualified", stop_distance_pips=stop_pips, spread_pips=spread)


def _minutes_until_force_close() -> int:
    now = now_dubai()
    force_close = now.replace(hour=int(config.FORCE_CLOSE_DUBAI.split(":")[0]), minute=int(config.FORCE_CLOSE_DUBAI.split(":")[1]), second=0, microsecond=0)
    return max(0, int((force_close - now).total_seconds() // 60))

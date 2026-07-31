from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

import pandas as pd

import config

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover
    mt5 = None

log = logging.getLogger("AsianSweepBot")


def mt5_available() -> bool:
    return mt5 is not None


def retry(callable_, *args, **kwargs):
    last_err = None
    for _ in range(config.RETRY_COUNT):
        try:
            return callable_(*args, **kwargs)
        except Exception as exc:  # pragma: no cover
            last_err = exc
            time.sleep(config.RETRY_DELAY_SECONDS)
    log.error("MT5 call failed permanently: %s", last_err)
    return None


def initialize() -> bool:
    if mt5 is None:
        log.error("MetaTrader5 library unavailable.")
        return False
    ok = mt5.initialize(
        login=int(config.MT5_LOGIN),
        password=config.MT5_PASSWORD,
        server=config.MT5_SERVER,
    )
    if ok:
        mt5.symbol_select(config.SYMBOL, True)
    else:
        log.error("MT5 initialize failed: %s", mt5.last_error())
    return bool(ok)


def shutdown() -> None:
    if mt5 is not None:
        mt5.shutdown()


def ensure_connection() -> bool:
    if mt5 is None:
        return False
    try:
        info = mt5.terminal_info()
        if info is not None and getattr(info, "connected", True):
            return True
    except Exception:
        pass
    shutdown()
    return initialize()


def fetch_rates(timeframe: int, n: int) -> Optional[pd.DataFrame]:
    if not ensure_connection():
        return None
    rates = retry(mt5.copy_rates_from_pos, config.SYMBOL, timeframe, 0, n)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def fetch_rates_range(timeframe: int, start_utc: datetime, end_utc: datetime) -> Optional[pd.DataFrame]:
    if not ensure_connection():
        return None
    rates = retry(mt5.copy_rates_range, config.SYMBOL, timeframe, start_utc, end_utc)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def latest_tick():
    if not ensure_connection():
        return None
    return retry(mt5.symbol_info_tick, config.SYMBOL)


def symbol_info():
    return mt5.symbol_info(config.SYMBOL) if mt5 is not None else None


def pip_size() -> float:
    info = symbol_info()
    if info is None:
        return 0.0001
    if info.digits in (3, 5):
        return info.point * 10
    return info.point


def spread_pips() -> Optional[float]:
    tick = latest_tick()
    if tick is None:
        return None
    return abs(float(tick.ask) - float(tick.bid)) / pip_size()

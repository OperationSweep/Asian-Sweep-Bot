from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, time as dtime

import schedule

import config
from datafeed import initialize, mt5, shutdown
from execution import force_close_positions, maybe_move_to_breakeven, place_trade
from journal import Journal
from state_store import DailyState, StateStore
from strategy import compute_asian_range, detect_bos, detect_sweep, determine_bias, now_dubai, qualify_trade


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def build_logger() -> logging.Logger:
    logger = logging.getLogger("AsianSweepBot")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger

    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    fh = logging.FileHandler(config.LOG_FILE, mode="a", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


log = build_logger()
store = StateStore()
STATE = store.load()
journal = Journal()


def fmt_price(price):
    if price is None:
        return "N/A"
    digits = mt5.symbol_info(config.SYMBOL).digits if mt5 is not None and mt5.symbol_info(config.SYMBOL) else 5
    return f"{price:.{digits}f}"


def dubai_hhmm_to_local_hhmm(hhmm: str) -> str:
    dt = now_dubai().replace(hour=int(hhmm.split(":")[0]), minute=int(hhmm.split(":")[1]), second=0, microsecond=0)
    return dt.astimezone().replace(tzinfo=None).strftime("%H:%M")


def persist() -> None:
    store.save(STATE)


def daily_setup() -> None:
    log.info("Daily setup triggered")
    STATE.reset()
    STATE.trade_date = now_dubai().strftime("%Y-%m-%d")

    bias = determine_bias()
    STATE.bias = bias
    journal.log_event("daily_setup", {"bias": bias, "trade_date": STATE.trade_date})

    if bias == "NEUTRAL":
        STATE.day_closed = True
        STATE.result_label = "NO_TRADE_NEUTRAL_BIAS"
        journal.append_signal_row({
            "date": STATE.trade_date,
            "bias": STATE.bias,
            "result": "SKIP",
            "reason": "neutral_bias",
        })
        persist()
        return

    rng = compute_asian_range()
    if rng is None:
        STATE.day_closed = True
        STATE.result_label = "NO_DATA"
        persist()
        return

    STATE.asian_high, STATE.asian_low = rng
    journal.log_event("asian_range", {"high": STATE.asian_high, "low": STATE.asian_low})
    persist()


def scan_tick() -> None:
    if STATE.day_closed or STATE.trade_open:
        if STATE.trade_open:
            moved = maybe_move_to_breakeven(STATE)
            if moved:
                journal.log_event("breakeven", {"entry_price": STATE.entry_price})
                persist()
        return

    if not within_scan_window():
        return

    if STATE.sweep_detected is False:
        sweep = detect_sweep(STATE)
        if sweep:
            if sweep["event"] == "INVALID":
                STATE.invalidated = True
                STATE.invalidation_reason = sweep["reason"]
                STATE.day_closed = True
                journal.log_event("invalid_day", sweep)
                journal.append_signal_row({
                    "date": STATE.trade_date,
                    "bias": STATE.bias,
                    "result": "SKIP",
                    "reason": sweep["reason"],
                })
            else:
                STATE.sweep_detected = True
                STATE.sweep_type = sweep["sweep_type"]
                STATE.sweep_extreme = sweep["sweep_extreme"]
                STATE.sweep_time_iso = sweep["time"].isoformat()
                journal.log_event("sweep_detected", sweep)
            persist()
            return

    if STATE.sweep_detected and not STATE.bos_confirmed:
        bos = detect_bos(STATE)
        if bos:
            STATE.bos_confirmed = True
            STATE.bos_level = bos["level"]
            STATE.bos_time_iso = bos["time"].isoformat()
            STATE.signal_price = bos["signal_price"]
            journal.log_event("bos_confirmed", bos)

            direction = "SELL" if STATE.sweep_type == "HIGH_SWEEP" else "BUY"
            decision = qualify_trade(direction, bos["signal_price"], float(STATE.sweep_extreme))
            journal.log_event("qualification", decision.__dict__)

            if not decision.allowed:
                STATE.day_closed = True
                STATE.result_label = f"SKIP_{decision.reason}"
                journal.append_signal_row({
                    "date": STATE.trade_date,
                    "bias": STATE.bias,
                    "sweep_type": STATE.sweep_type,
                    "bos_level": STATE.bos_level,
                    "result": "SKIP",
                    "reason": decision.reason,
                    "stop_distance_pips": decision.stop_distance_pips,
                    "spread_pips": decision.spread_pips,
                })
                persist()
                return

            result = place_trade(direction, bos["signal_price"], float(STATE.sweep_extreme))
            journal.log_event("trade_attempt", result)
            if result.get("ok"):
                STATE.trade_open = True
                STATE.direction = direction
                STATE.ticket = result.get("ticket")
                STATE.signal_price = result.get("signal_price")
                STATE.entry_price = result.get("fill_price")
                STATE.sl_price = result.get("sl")
                STATE.tp_price = result.get("tp")
                STATE.stop_distance_pips = decision.stop_distance_pips
                journal.append_trade_row({
                    "date": STATE.trade_date,
                    "symbol": config.SYMBOL,
                    "direction": direction,
                    "signal_price": result.get("signal_price"),
                    "fill_price": result.get("fill_price"),
                    "sl": result.get("sl"),
                    "tp": result.get("tp"),
                    "ticket": result.get("ticket"),
                    "dry_run": result.get("dry_run"),
                })
            else:
                STATE.day_closed = True
                STATE.result_label = f"EXEC_FAIL_{result.get('reason')}"
            persist()


def force_close_job() -> None:
    info = force_close_positions()
    journal.log_event("force_close", info)
    STATE.day_closed = True
    STATE.trade_open = False
    STATE.exit_reason = "TIME_EXIT"
    persist()


def reset_job() -> None:
    journal.log_event("daily_reset", {"previous_trade_date": STATE.trade_date})
    STATE.reset()
    persist()


def within_scan_window() -> bool:
    now = now_dubai().time()
    start = dtime(*[int(x) for x in config.SWEEP_SCAN_START_DUBAI.split(":")])
    end = dtime(*[int(x) for x in config.SWEEP_SCAN_END_DUBAI.split(":")])
    return start <= now <= end


def configure_schedule() -> None:
    schedule.clear()
    schedule.every().day.at(dubai_hhmm_to_local_hhmm(config.DAILY_SETUP_DUBAI)).do(daily_setup)
    schedule.every(5).minutes.do(scan_tick)
    schedule.every().day.at(dubai_hhmm_to_local_hhmm(config.FORCE_CLOSE_DUBAI)).do(force_close_job)
    schedule.every().day.at(dubai_hhmm_to_local_hhmm(config.RESET_DUBAI)).do(reset_job)


def run() -> None:
    print("=" * 50)
    print("ASIAN SESSION LIQUIDITY SWEEP BOT — RESEARCH MODE")
    print("=" * 50)
    print(f"DRY_RUN={config.DRY_RUN} PAPER_MODE={config.PAPER_MODE}")

    if not initialize():
        log.error("Initial MT5 connection failed.")
        return

    configure_schedule()

    now = now_dubai().time()
    setup_time = dtime(*[int(x) for x in config.DAILY_SETUP_DUBAI.split(":")])
    if now >= setup_time and STATE.trade_date != now_dubai().strftime("%Y-%m-%d"):
        daily_setup()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Interrupted by user.")
    finally:
        shutdown()


if __name__ == "__main__":
    run()

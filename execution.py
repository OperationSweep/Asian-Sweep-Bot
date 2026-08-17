from __future__ import annotations

from typing import Optional

import config
from datafeed import latest_tick, mt5, pip_size
from state_store import DailyState


class ExecutionResult(dict):
    pass


def build_order_levels(direction: str, signal_price: float, sweep_extreme: float) -> dict:
    if direction == "SELL":
        sl = sweep_extreme + config.SL_BUFFER_PIPS * pip_size()
        risk = sl - signal_price
        tp = signal_price - config.RR_RATIO * risk
    else:
        sl = sweep_extreme - config.SL_BUFFER_PIPS * pip_size()
        risk = signal_price - sl
        tp = signal_price + config.RR_RATIO * risk
    return {"sl": sl, "tp": tp, "risk_price": abs(signal_price - sl)}


def place_trade(direction: str, signal_price: float, sweep_extreme: float) -> ExecutionResult:
    levels = build_order_levels(direction, signal_price, sweep_extreme)
    tick = latest_tick()
    if tick is None:
        return ExecutionResult(ok=False, reason="no_tick")

    fill_price = float(tick.bid if direction == "SELL" else tick.ask)
    result = ExecutionResult(
        ok=True,
        direction=direction,
        signal_price=signal_price,
        fill_price=fill_price,
        sl=levels["sl"],
        tp=levels["tp"],
        risk_price=levels["risk_price"],
        dry_run=config.DRY_RUN,
        ticket=None,
    )

    if config.DRY_RUN or mt5 is None:
        return result

    # TODO: validate broker-specific filling mode and retcode behaviour in demo before live use.
    order_type = mt5.ORDER_TYPE_SELL if direction == "SELL" else mt5.ORDER_TYPE_BUY
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": config.SYMBOL,
        "volume": float(config.LOT_SIZE),
        "type": order_type,
        "price": fill_price,
        "sl": levels["sl"],
        "tp": levels["tp"],
        "deviation": config.DEVIATION_POINTS,
        "magic": config.MAGIC_NUMBER,
        "comment": "AsianSweep_BOS",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    raw = mt5.order_send(request)
    if raw is None or raw.retcode != mt5.TRADE_RETCODE_DONE:
        return ExecutionResult(ok=False, reason="order_send_failed", raw=str(raw))
    result["ticket"] = int(raw.order)
    result["fill_price"] = float(raw.price)
    return result


def maybe_move_to_breakeven(state: DailyState) -> bool:
    if not state.trade_open or state.entry_price is None or state.sl_price is None or state.direction is None:
        return False
    tick = latest_tick()
    if tick is None:
        return False
    current = float(tick.bid if state.direction == "SELL" else tick.ask)
    risk = abs(state.entry_price - state.sl_price)
    progress = (state.entry_price - current) if state.direction == "SELL" else (current - state.entry_price)
    if progress < risk * config.MOVE_TO_BE_AT_R:
        return False
    if state.breakeven_done:
        return False

    if config.DRY_RUN or mt5 is None or not state.ticket:
        state.breakeven_done = True
        state.sl_price = state.entry_price
        return True

    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": config.SYMBOL,
        "position": state.ticket,
        "sl": state.entry_price,
        "tp": state.tp_price,
        "magic": config.MAGIC_NUMBER,
    }
    raw = mt5.order_send(request)
    if raw is None or raw.retcode != mt5.TRADE_RETCODE_DONE:
        return False
    state.breakeven_done = True
    state.sl_price = state.entry_price
    return True


def force_close_positions() -> dict:
    # TODO: implement robust live/demo close handling and journaling of each closure.
    return {"ok": True, "dry_run": config.DRY_RUN, "reason": "time_exit_scaffold"}

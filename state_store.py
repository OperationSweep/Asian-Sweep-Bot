from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Optional

import config


@dataclass
class DailyState:
    trade_date: Optional[str] = None
    bias: str = "NEUTRAL"
    asian_high: Optional[float] = None
    asian_low: Optional[float] = None

    sweep_detected: bool = False
    sweep_type: Optional[str] = None
    sweep_extreme: Optional[float] = None
    sweep_time_iso: Optional[str] = None

    bos_level: Optional[float] = None
    bos_confirmed: bool = False
    bos_time_iso: Optional[str] = None

    invalidated: bool = False
    invalidation_reason: Optional[str] = None

    trade_open: bool = False
    ticket: Optional[int] = None
    direction: Optional[str] = None
    signal_price: Optional[float] = None
    entry_price: Optional[float] = None
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    stop_distance_pips: Optional[float] = None
    breakeven_done: bool = False

    exit_price: Optional[float] = None
    result_label: Optional[str] = None
    exit_reason: Optional[str] = None
    pip_result: Optional[float] = None
    pnl: Optional[float] = None

    day_closed: bool = False

    def reset(self) -> None:
        for f in fields(self):
            setattr(self, f.name, f.default)


class StateStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or config.STATE_FILE)

    def load(self) -> DailyState:
        if not self.path.exists():
            return DailyState()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        state = DailyState()
        for f in fields(state):
            if f.name in data:
                setattr(state, f.name, data[f.name])
        return state

    def save(self, state: DailyState) -> None:
        self.path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")

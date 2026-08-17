from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import config


class Journal:
    def __init__(self) -> None:
        self.events_path = Path(config.EVENT_JOURNAL_FILE)
        self.signals_path = Path(config.SIGNAL_JOURNAL_FILE)
        self.trades_path = Path(config.TRADE_JOURNAL_FILE)

    def log_event(self, event_type: str, payload: dict[str, Any]) -> None:
        row = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "payload": payload,
        }
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def append_signal_row(self, row: dict[str, Any]) -> None:
        self._append_csv(self.signals_path, row)

    def append_trade_row(self, row: dict[str, Any]) -> None:
        self._append_csv(self.trades_path, row)

    @staticmethod
    def _append_csv(path: Path, row: dict[str, Any]) -> None:
        write_header = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(row)

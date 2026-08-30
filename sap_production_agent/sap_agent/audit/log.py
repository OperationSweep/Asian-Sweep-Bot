"""Append-only audit log, written as both CSV and JSON Lines.

One row per meaningful event. Never contains credentials - the writer drops any
field whose name looks like a secret rather than trusting callers.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

FIELDS = [
    "timestamp", "run_id", "operator", "workbook", "event", "work_order",
    "transaction", "serial_count", "serials", "result", "message_class",
    "sap_message", "document", "pdf", "attempt", "error",
]

SECRET_HINTS = ("password", "passwd", "secret", "token", "api_key", "apikey", "bcode")


@dataclass
class AuditLog:
    directory: Path
    run_id: str
    operator: str = "unknown"
    workbook: str = ""

    def __post_init__(self) -> None:
        self.directory = Path(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.directory / f"run_{self.run_id}.csv"
        self.json_path = self.directory / f"run_{self.run_id}.jsonl"
        if not self.csv_path.exists():
            with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
                csv.DictWriter(handle, fieldnames=FIELDS).writeheader()

    def record(self, event: str, **fields: Any) -> Dict[str, Any]:
        row: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": self.run_id,
            "operator": self.operator,
            "workbook": self.workbook,
            "event": event,
        }
        for key, value in fields.items():
            if any(hint in key.lower() for hint in SECRET_HINTS):
                continue
            if isinstance(value, (list, tuple)):
                value = ";".join(str(v) for v in value)
            row[key] = value

        with self.csv_path.open("a", newline="", encoding="utf-8") as handle:
            csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore").writerow(row)
        with self.json_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        return row

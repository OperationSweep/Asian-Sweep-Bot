"""Run state: the record of what has been posted, and the guard against
posting it twice.

Persisted to disk after every transition, so a crashed or cancelled run resumes
from the last verified work order instead of starting over. This file is the
authority on whether a work order was posted - not the operator's memory.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class Phase(str, Enum):
    LOAD_EXCEL = "LOAD_EXCEL"
    VALIDATE = "VALIDATE"
    CONNECT_SAP = "CONNECT_SAP"
    AWAIT_CONFIRMATION = "AWAIT_CONFIRMATION"
    ZPRO = "ZPRO"
    VALIDATE_COMPLETION = "VALIDATE_COMPLETION"
    CO04 = "CO04"
    PRINT = "PRINT"
    VERIFY_FILES = "VERIFY_FILES"
    COMPLETE = "COMPLETE"
    HALTED = "HALTED"


class OrderState(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    POSTED = "POSTED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    # Entered ZPRO but the outcome could not be established. Never retried
    # automatically: a human must check SAP before it is posted again.
    UNCERTAIN = "UNCERTAIN"


TERMINAL = {OrderState.POSTED, OrderState.SKIPPED}


@dataclass
class OrderRecord:
    work_order: str
    state: OrderState = OrderState.PENDING
    serial_count: int = 0
    attempts: int = 0
    sap_message: str = ""
    message_class: str = ""
    document: str = ""
    screenshot: str = ""
    started_at: str = ""
    finished_at: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass
class RunState:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    operator: str = field(default_factory=lambda: os.environ.get("USERNAME") or "unknown")
    workbook: str = ""
    workbook_fingerprint: str = ""
    dry_run: bool = True
    phase: Phase = Phase.LOAD_EXCEL
    orders: Dict[str, OrderRecord] = field(default_factory=dict)
    pdf_paths: Dict[str, str] = field(default_factory=dict)
    halt_reason: str = ""
    _path: Optional[Path] = None

    # -- registration ------------------------------------------------------

    def register(self, work_order: str, serial_count: int) -> OrderRecord:
        """Add an order, keeping any state a previous run already recorded."""
        existing = self.orders.get(work_order)
        if existing:
            existing.serial_count = serial_count
            return existing
        record = OrderRecord(work_order=work_order, serial_count=serial_count)
        self.orders[work_order] = record
        return record

    # -- the idempotency guard --------------------------------------------

    def may_post(self, work_order: str) -> tuple[bool, str]:
        """Whether this order may be posted now, and why not if it may not.

        The only states that permit a posting attempt are PENDING and FAILED.
        POSTED is refused because the goods issue already happened; UNCERTAIN is
        refused because we do not know whether it did, and guessing wrong posts
        stock twice.
        """
        record = self.orders.get(work_order)
        if record is None:
            return False, f"{work_order} is not part of this run"
        if record.state is OrderState.POSTED:
            return False, f"{work_order} was already posted in run {self.run_id}"
        if record.state is OrderState.SKIPPED:
            return False, f"{work_order} was skipped by the operator"
        if record.state is OrderState.UNCERTAIN:
            return False, (
                f"{work_order} was left in an uncertain state - check ZPRO in SAP "
                f"by hand and mark it posted or failed before retrying"
            )
        if record.state is OrderState.IN_PROGRESS:
            return False, (
                f"{work_order} is marked in progress, which means a previous run "
                f"died mid-transaction - check SAP before retrying"
            )
        return True, ""

    # -- transitions -------------------------------------------------------

    def begin(self, work_order: str) -> None:
        record = self.orders[work_order]
        record.state = OrderState.IN_PROGRESS
        record.attempts += 1
        record.started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.save()

    def finish(
        self,
        work_order: str,
        state: OrderState,
        sap_message: str = "",
        message_class: str = "",
        document: str = "",
        error: str = "",
        screenshot: str = "",
    ) -> None:
        record = self.orders[work_order]
        record.state = state
        record.sap_message = sap_message
        record.message_class = message_class
        record.document = document
        record.error = error
        record.screenshot = screenshot
        record.finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.save()

    def halt(self, reason: str) -> None:
        self.phase = Phase.HALTED
        self.halt_reason = reason
        self.save()

    def set_phase(self, phase: Phase) -> None:
        self.phase = phase
        self.save()

    # -- queries -----------------------------------------------------------

    @property
    def posted(self) -> List[str]:
        return [w for w, r in self.orders.items() if r.state is OrderState.POSTED]

    @property
    def pending(self) -> List[str]:
        return [w for w, r in self.orders.items() if r.state is OrderState.PENDING]

    @property
    def failed(self) -> List[str]:
        return [
            w for w, r in self.orders.items()
            if r.state in (OrderState.FAILED, OrderState.UNCERTAIN)
        ]

    def print_range(self) -> tuple[str, str]:
        """First and last successfully posted order, for CO04.

        Sorted numerically where possible so the range matches SAP's own
        ordering rather than string order.
        """
        if not self.posted:
            raise ValueError("no orders were posted, so there is no print range")
        try:
            ordered = sorted(self.posted, key=int)
        except ValueError:
            ordered = sorted(self.posted)
        return ordered[0], ordered[-1]

    def contiguous_range(self) -> bool:
        """True when the posted orders form an unbroken numeric run."""
        return len(self.contiguous_blocks()) <= 1

    def contiguous_blocks(self) -> List[tuple[str, str]]:
        """Split the posted orders into unbroken numeric runs.

        CO04 selects by range, so one From/To over a set with a gap would
        reprint every order sitting in the gap - orders this run never touched.
        A real batch is not always contiguous: a sheet may carry, say, two
        orders from one series and twenty-two from another, where a single
        range would span hundreds of unrelated orders.

        So the print step runs once per block. Blocks are derived from posted
        orders only, which also means an order that failed mid-run splits the
        block around it and is excluded from the reprint.
        """
        try:
            numbers = sorted(int(w) for w in self.posted)
        except ValueError:
            return [(w, w) for w in sorted(self.posted)]
        if not numbers:
            return []

        blocks: List[tuple[str, str]] = []
        start = previous = numbers[0]
        for number in numbers[1:]:
            if number == previous + 1:
                previous = number
                continue
            blocks.append((str(start), str(previous)))
            start = previous = number
        blocks.append((str(start), str(previous)))
        return blocks

    def orders_in_block(self, first: str, last: str) -> List[str]:
        """The posted orders inside one block, in numeric order."""
        try:
            low, high = int(first), int(last)
            return [w for w in sorted(self.posted, key=int) if low <= int(w) <= high]
        except ValueError:
            return [w for w in sorted(self.posted) if first <= w <= last]

    def unposted_in_range(self) -> List[str]:
        """Orders that fall inside the print range but were not posted."""
        if not self.posted:
            return []
        try:
            posted = {int(w) for w in self.posted}
        except ValueError:
            return []
        return [
            str(n) for n in range(min(posted), max(posted) + 1) if n not in posted
        ]

    # -- persistence -------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "operator": self.operator,
            "workbook": self.workbook,
            "workbook_fingerprint": self.workbook_fingerprint,
            "dry_run": self.dry_run,
            "phase": self.phase.value,
            "halt_reason": self.halt_reason,
            "orders": {w: r.to_dict() for w, r in self.orders.items()},
            "pdf_paths": self.pdf_paths,
        }

    def save(self, path: Optional[Path] = None) -> None:
        target = path or self._path
        if target is None:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        # Write then replace, so a crash mid-write cannot corrupt the record
        # that says what has already been posted.
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        temporary.replace(target)

    def bind(self, path: Path) -> "RunState":
        self._path = path
        return self

    @classmethod
    def load(cls, path: Path) -> "RunState":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        state = cls(
            run_id=data["run_id"],
            started_at=data["started_at"],
            operator=data.get("operator", "unknown"),
            workbook=data.get("workbook", ""),
            workbook_fingerprint=data.get("workbook_fingerprint", ""),
            dry_run=data.get("dry_run", True),
            phase=Phase(data.get("phase", Phase.LOAD_EXCEL.value)),
            halt_reason=data.get("halt_reason", ""),
            pdf_paths=data.get("pdf_paths", {}),
        )
        for work_order, record in data.get("orders", {}).items():
            record = dict(record)
            record["state"] = OrderState(record["state"])
            state.orders[work_order] = OrderRecord(**record)
        return state.bind(Path(path))


def fingerprint(path: Path) -> str:
    """Identify a workbook by content, so a resumed run cannot use a changed one."""
    import hashlib

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]

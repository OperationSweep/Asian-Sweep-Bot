"""Normalised representation of the kitting workbook.

The workbook is column-oriented: each column from B rightwards is one fibre
pair and one work order, and each row from the work-order row downwards is one
component material. A serial number therefore lives at the intersection of a
work order (column) and a material (row).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKER = "BLOCKER"


@dataclass(frozen=True)
class Anomaly:
    """Something in the workbook that a human should look at before posting."""

    severity: Severity
    code: str
    message: str
    cell: Optional[str] = None
    work_order: Optional[str] = None

    def line(self) -> str:
        where = f" [{self.cell}]" if self.cell else ""
        return f"{self.severity.value:<8} {self.code}{where}: {self.message}"


@dataclass(frozen=True)
class ComponentSerial:
    """One serial number, and the material it belongs to."""

    material: str
    serial: str
    sheet_row: int
    sequence: int


@dataclass
class Job:
    """One work order: a spreadsheet column, with its serials in sheet order."""

    work_order: str
    fibre_pair: str
    column_letter: str
    column_index: int
    serials: List[ComponentSerial] = field(default_factory=list)
    anomalies: List[Anomaly] = field(default_factory=list)

    @property
    def serial_numbers(self) -> List[str]:
        return [s.serial for s in self.serials]

    @property
    def blocked(self) -> bool:
        return any(a.severity is Severity.BLOCKER for a in self.anomalies)

    def to_dict(self) -> dict:
        """The flat shape used by the agent tools and the audit log."""
        return {
            "work_order": self.work_order,
            "fibre_pair": self.fibre_pair,
            "serial_numbers": self.serial_numbers,
        }


@dataclass
class Workbook:
    """Everything discovered from one spreadsheet."""

    path: str
    sheet_name: str
    jobs: List[Job] = field(default_factory=list)
    # Materials listed in column A that carry no serial anywhere in the sheet.
    # These are why SAP raises "Serial Number missing for <material>".
    non_serialised_materials: List[str] = field(default_factory=list)
    serialised_materials: List[str] = field(default_factory=list)
    anomalies: List[Anomaly] = field(default_factory=list)

    @property
    def all_anomalies(self) -> List[Anomaly]:
        return self.anomalies + [a for job in self.jobs for a in job.anomalies]

    @property
    def blockers(self) -> List[Anomaly]:
        return [a for a in self.all_anomalies if a.severity is Severity.BLOCKER]

    @property
    def warnings(self) -> List[Anomaly]:
        return [a for a in self.all_anomalies if a.severity is Severity.WARNING]

    def job(self, work_order: str) -> Optional[Job]:
        return next((j for j in self.jobs if j.work_order == work_order), None)

    def to_jobs(self) -> List[dict]:
        return [job.to_dict() for job in self.jobs]


class KittingError(Exception):
    """Fatal: stop, do not post."""


def normalise_work_order(raw: object) -> str:
    """Excel stores order numbers as numbers; SAP wants clean digits."""
    if raw is None:
        raise ValueError("work order is empty")
    text = str(raw).strip()
    if not text:
        raise ValueError("work order is empty")
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def normalise_serial(raw: object) -> Optional[str]:
    """Return a clean serial, or None for a cell that holds no serial.

    A literal 0 means "not scanned" in this workbook - row 3 uses it for the
    amp-tray serial on orders that have not had a tray fitted yet. It must
    never reach SAP as the string "0".
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        if raw == 0:
            return None
        text = str(int(raw)) if float(raw).is_integer() else str(raw)
    else:
        text = str(raw).strip()
    return text or None

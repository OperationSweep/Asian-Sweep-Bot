"""Plain data structures shared across the package."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Component:
    """One scanned line: an optic filter, a coupler, or anything else."""

    part_number: str
    serial: Optional[str] = None
    quantity: float = 1.0
    component_type: Optional[str] = None
    source_row: Optional[int] = None


@dataclass
class WorkOrder:
    """A work order and every component scanned against it."""

    order_number: str
    components: List[Component] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.order_number = normalise_order_number(self.order_number)

    @property
    def total_quantity(self) -> float:
        return sum(c.quantity for c in self.components)

    def summary(self) -> str:
        kinds = {c.component_type for c in self.components if c.component_type}
        kind_text = ", ".join(sorted(kinds)) if kinds else "components"
        return (
            f"{self.order_number}: {len(self.components)} {kind_text} "
            f"(qty {self.total_quantity:g})"
        )


def normalise_order_number(raw: object) -> str:
    """Excel turns order numbers into floats; SAP wants the digits.

    ``12345678`` read back as ``12345678.0`` would be rejected by ZPRO, and a
    number stored as text may carry padding. Both are normalised here so the
    rest of the code only ever sees a clean string.
    """
    if raw is None:
        raise ValueError("work order number is empty")

    text = str(raw).strip()
    if not text:
        raise ValueError("work order number is empty")

    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]

    return text


class KittingError(Exception):
    """Anything that should stop or skip a work order, with a readable cause."""


class SapMessage(KittingError):
    """SAP returned a message we did not classify as success."""

    def __init__(self, msg_type: str, text: str) -> None:
        self.msg_type = msg_type
        self.text = text
        super().__init__(f"SAP {msg_type}: {text}")

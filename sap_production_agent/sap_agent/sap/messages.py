"""Classify what SAP says back, so the run knows whether to continue.

The important finding from the sample workbook concerns the message the
operator described:

    Serial Number missing for <material>

That argument is a *material* number, not a serial. Column A of the workbook
holds materials in exactly that shape, and none of the serial families in the
sheet look like it - they follow entirely different patterns. Ten materials in
the production sample carry no serial anywhere in the sheet, which is precisely
why SAP asks for them.

That distinction is what makes the message safe to classify:

  * missing serial for a material the sheet never serialises -> EXPECTED_WARNING
  * missing serial for a material the sheet *does* serialise -> CRITICAL, because
    it means the serials we typed did not land.

The second case looks identical on screen. Without the workbook to compare
against, an automation that pattern-matched the text alone would happily
confirm past a real posting failure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence


class MessageClass(str, Enum):
    SUCCESS = "SUCCESS"
    EXPECTED_WARNING = "EXPECTED_WARNING"
    RETRYABLE_ERROR = "RETRYABLE_ERROR"
    CRITICAL_ERROR = "CRITICAL_ERROR"
    UNKNOWN_MESSAGE = "UNKNOWN_MESSAGE"


@dataclass(frozen=True)
class Classification:
    message_class: MessageClass
    reason: str
    raw_type: str = ""
    raw_text: str = ""
    material: Optional[str] = None
    # True when SAP's reply does not establish whether the posting landed.
    # Such an order is never retried automatically - a human checks first.
    uncertain: bool = False

    @property
    def may_continue(self) -> bool:
        """Only these two let the run move to the next work order unattended."""
        return self.message_class in (
            MessageClass.SUCCESS, MessageClass.EXPECTED_WARNING
        )


SERIAL_MISSING = re.compile(
    r"serial\s*number\s*missing\s*for\s*[:\-]?\s*(?P<material>[A-Z0-9]{6,})",
    re.IGNORECASE,
)

POSTED_OK = re.compile(
    r"(document\s+\d+\s+(posted|created))"
    r"|(goods\s+issue\s+.*(posted|saved))"
    r"|(order\s+\d+\s+saved)",
    re.IGNORECASE,
)

# (pattern, reason, outcome_unknown). A lock or a busy object means SAP refused
# before posting, so the order can simply be retried. A timeout or a terminated
# update means we do not know whether the goods issue went through.
RETRYABLE = [
    (re.compile(r"locked\s+by\s+user", re.IGNORECASE),
     "object locked by another user", False),
    (re.compile(r"being\s+processed\s+by", re.IGNORECASE),
     "object in use", False),
    (re.compile(r"try\s+again\s+later", re.IGNORECASE),
     "SAP asked us to retry", False),
    (re.compile(r"time\s*out", re.IGNORECASE),
     "timeout - the posting may or may not have completed", True),
    (re.compile(r"update\s+was\s+terminated", re.IGNORECASE),
     "update terminated - the posting may or may not have completed", True),
]

CRITICAL = [
    (re.compile(r"not\s+authori[sz]ed", re.IGNORECASE), "authorisation failure"),
    (re.compile(r"no\s+authori[sz]ation", re.IGNORECASE), "authorisation failure"),
    (re.compile(r"does\s+not\s+exist", re.IGNORECASE), "object does not exist"),
    (re.compile(r"deletion\s+flag", re.IGNORECASE), "order flagged for deletion"),
    (re.compile(r"already\s+been\s+posted", re.IGNORECASE), "already posted"),
    (re.compile(r"deficit\s+of", re.IGNORECASE), "stock deficit"),
    (re.compile(r"period\s+.*not\s+open", re.IGNORECASE), "posting period closed"),
]


def classify(
    message_type: str,
    text: str,
    non_serialised_materials: Sequence[str] = (),
    serialised_materials: Sequence[str] = (),
) -> Classification:
    """Classify one SAP message against what the workbook says to expect.

    message_type is SAP's own letter: S success, W warning, E error, A abort,
    I information. It is a hint, not the verdict - a warning that names a
    material we *did* serialise is treated as critical regardless.
    """
    text = (text or "").strip()
    message_type = (message_type or "").strip().upper()

    if not text:
        return Classification(
            MessageClass.SUCCESS, "no message on the status bar",
            message_type, text,
        )

    match = SERIAL_MISSING.search(text)
    if match:
        material = match.group("material").upper()
        known_bulk = {m.upper() for m in non_serialised_materials}
        known_serialised = {m.upper() for m in serialised_materials}

        if material in known_bulk:
            return Classification(
                MessageClass.EXPECTED_WARNING,
                f"{material} carries no serial anywhere in the workbook, so SAP "
                f"asking for one is expected for this build",
                message_type, text, material,
            )
        if material in known_serialised:
            return Classification(
                MessageClass.CRITICAL_ERROR,
                f"{material} IS serialised in the workbook, so SAP should have "
                f"received its serial - the entry did not land",
                message_type, text, material,
            )
        return Classification(
            MessageClass.UNKNOWN_MESSAGE,
            f"{material} does not appear in the workbook at all - operator must "
            f"confirm whether this component is expected on this order",
            message_type, text, material, uncertain=True,
        )

    if POSTED_OK.search(text):
        return Classification(
            MessageClass.SUCCESS, "SAP confirmed the posting", message_type, text
        )

    for pattern, reason in CRITICAL:
        if pattern.search(text):
            return Classification(
                MessageClass.CRITICAL_ERROR, reason, message_type, text
            )

    for pattern, reason, outcome_unknown in RETRYABLE:
        if pattern.search(text):
            return Classification(
                MessageClass.RETRYABLE_ERROR, reason, message_type, text,
                uncertain=outcome_unknown,
            )

    if message_type in ("E", "A"):
        return Classification(
            MessageClass.CRITICAL_ERROR,
            f"unrecognised SAP {message_type}-type message", message_type, text,
        )
    if message_type == "S":
        return Classification(
            MessageClass.SUCCESS, "SAP success message", message_type, text
        )

    return Classification(
        MessageClass.UNKNOWN_MESSAGE,
        "message not recognised by any rule - stopping rather than guessing",
        message_type, text, uncertain=True,
    )


def classify_all(
    messages: List[tuple[str, str]],
    non_serialised_materials: Sequence[str] = (),
    serialised_materials: Sequence[str] = (),
) -> List[Classification]:
    return [
        classify(kind, text, non_serialised_materials, serialised_materials)
        for kind, text in messages
    ]


def worst(classifications: Sequence[Classification]) -> Classification:
    """The classification that decides what the run does next."""
    if not classifications:
        return Classification(MessageClass.SUCCESS, "no messages")
    rank = {
        MessageClass.CRITICAL_ERROR: 0,
        MessageClass.UNKNOWN_MESSAGE: 1,
        MessageClass.RETRYABLE_ERROR: 2,
        MessageClass.EXPECTED_WARNING: 3,
        MessageClass.SUCCESS: 4,
    }
    return min(classifications, key=lambda c: rank[c.message_class])

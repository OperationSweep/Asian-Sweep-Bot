"""Pre-flight validation. Nothing reaches SAP until this passes.

Reader-level anomalies (missing serials, stray cells, duplicate orders) are
found during parsing. This module adds the cross-cutting checks that need the
whole workbook in view, and renders the operator preview.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import List, Optional

from ..models import Anomaly, Severity, Workbook

# Material codes in this workbook are two digits, three letters, five digits,
# three letters.
MATERIAL_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{3}[0-9]{5}[A-Z]{3}$")
# Work orders are 9-digit numbers.
WORK_ORDER_PATTERN = re.compile(r"^[0-9]{6,12}$")


def validate(book: Workbook, expected_pairs: Optional[int] = None) -> List[Anomaly]:
    """Return every anomaly, including the reader's, worst first."""
    found: List[Anomaly] = list(book.all_anomalies)

    found.extend(_check_work_order_format(book))
    found.extend(_check_duplicate_serials(book))
    found.extend(_check_serial_counts(book))
    found.extend(_check_row_labels(book))
    found.extend(_check_expected_pairs(book, expected_pairs))

    order = {Severity.BLOCKER: 0, Severity.WARNING: 1, Severity.INFO: 2}
    return sorted(found, key=lambda a: (order[a.severity], a.code, a.cell or ""))


def _check_work_order_format(book: Workbook) -> List[Anomaly]:
    return [
        Anomaly(
            Severity.BLOCKER, "MALFORMED_WORK_ORDER",
            f"{job.work_order!r} does not look like a work order number",
            cell=f"{job.column_letter}", work_order=job.work_order,
        )
        for job in book.jobs
        if not WORK_ORDER_PATTERN.match(job.work_order)
    ]


def _check_duplicate_serials(book: Workbook) -> List[Anomaly]:
    """A serial appearing twice means a scan was repeated - never post it."""
    seen: dict[str, str] = {}
    counts = Counter(
        component.serial for job in book.jobs for component in job.serials
    )
    anomalies = []
    for job in book.jobs:
        for component in job.serials:
            if counts[component.serial] == 1:
                continue
            where = f"{job.column_letter}{component.sheet_row}"
            if component.serial in seen:
                anomalies.append(Anomaly(
                    Severity.BLOCKER, "DUPLICATE_SERIAL",
                    f"serial {component.serial} appears on work order "
                    f"{job.work_order} and again at {seen[component.serial]}",
                    cell=where, work_order=job.work_order,
                ))
            else:
                seen[component.serial] = where
    return anomalies


def _check_serial_counts(book: Workbook) -> List[Anomaly]:
    """Flag orders whose serial count differs from the rest of the batch.

    An odd count is not necessarily wrong - the sample has 16 orders with 21
    serials and 8 with 20, because the amp tray is not fitted on those - but it
    is always worth a human glance before posting.
    """
    if not book.jobs:
        return []

    counts = Counter(len(job.serials) for job in book.jobs)
    if len(counts) == 1:
        return []

    typical, _ = counts.most_common(1)[0]
    return [
        Anomaly(
            Severity.WARNING, "SERIAL_COUNT_OUTLIER",
            f"work order {job.work_order} has {len(job.serials)} serials; "
            f"most orders in this batch have {typical}",
            cell=job.column_letter, work_order=job.work_order,
        )
        for job in book.jobs
        if len(job.serials) != typical
    ]


def _check_row_labels(book: Workbook) -> List[Anomaly]:
    """Row labels that are not material codes cannot be matched to SAP by code."""
    return [
        Anomaly(
            Severity.INFO, "NON_MATERIAL_LABEL",
            f"row label {label!r} is not a material code, so its SAP component "
            f"row has to be matched by position rather than by material",
        )
        for label in book.serialised_materials
        if not MATERIAL_PATTERN.match(label)
    ]


def _check_expected_pairs(book: Workbook, expected: Optional[int]) -> List[Anomaly]:
    if expected is None:
        return []
    if expected == len(book.jobs):
        return []
    if expected > len(book.jobs):
        return [Anomaly(
            Severity.BLOCKER, "PAIR_COUNT_MISMATCH",
            f"operator asked for {expected} fibre pairs but the sheet holds "
            f"only {len(book.jobs)}",
        )]
    return [Anomaly(
        Severity.INFO, "PARTIAL_BATCH",
        f"processing the first {expected} of {len(book.jobs)} work orders",
    )]


def print_blocks(jobs) -> List[tuple]:
    """Contiguous runs of work orders, which become the CO04 selections.

    Shown in pre-flight because a batch spanning two order series prints as two
    ranges, not one - and one range across the gap would select every order in
    between.
    """
    try:
        numbers = sorted(int(job.work_order) for job in jobs)
    except ValueError:
        return []
    if not numbers:
        return []

    blocks = []
    start = previous = numbers[0]
    for number in numbers[1:]:
        if number == previous + 1:
            previous = number
            continue
        blocks.append((str(start), str(previous), previous - start + 1))
        start = previous = number
    blocks.append((str(start), str(previous), previous - start + 1))
    return blocks


def preview(book: Workbook, anomalies: List[Anomaly], limit: Optional[int] = None) -> str:
    """The operator-facing summary shown before any posting begins."""
    jobs = book.jobs[:limit] if limit else book.jobs
    total_serials = sum(len(job.serials) for job in jobs)

    lines = [
        "=" * 56,
        "PRE-FLIGHT",
        "=" * 56,
        f"Workbook:   {book.path}",
        f"Worksheet:  {book.sheet_name}",
        "",
        f"Work orders detected: {len(jobs)}"
        + (f" (of {len(book.jobs)} in sheet)" if limit and limit < len(book.jobs) else ""),
        f"Serial numbers:       {total_serials}",
        "",
        f"First order: {jobs[0].work_order}" if jobs else "First order: -",
        f"Last order:  {jobs[-1].work_order}" if jobs else "Last order:  -",
        "",
    ]

    for job in jobs:
        pair = f" [{job.fibre_pair}]" if job.fibre_pair else ""
        lines.append(
            f"  {job.column_letter:>2}  {job.work_order}{pair}"
            f"  serials: {len(job.serials)}"
        )

    blocks = print_blocks(jobs)
    if blocks:
        lines += ["", f"CO04 print range{'s' if len(blocks) > 1 else ''}:"]
        for first, last, count in blocks:
            lines.append(f"  {first} - {last}  ({count} orders)")
        if len(blocks) > 1:
            span = int(blocks[-1][1]) - int(blocks[0][0]) + 1
            lines.append(
                f"  These orders are not one unbroken run. Printed as a single "
                f"{blocks[0][0]}-{blocks[-1][1]} range, CO04 would select "
                f"{span} orders instead of {len(jobs)}, so each block is "
                f"selected separately."
            )

    if book.non_serialised_materials:
        lines += [
            "",
            "Materials with no serials in this sheet "
            f"({len(book.non_serialised_materials)}):",
            "  " + ", ".join(book.non_serialised_materials),
            "  SAP is expected to report 'Serial Number missing' for these.",
        ]

    blockers = [a for a in anomalies if a.severity is Severity.BLOCKER]
    warnings = [a for a in anomalies if a.severity is Severity.WARNING]
    infos = [a for a in anomalies if a.severity is Severity.INFO]

    if blockers or warnings or infos:
        lines += ["", "-" * 56]
        for anomaly in blockers + warnings + infos:
            lines.append("  " + anomaly.line())

    lines += ["", "-" * 56]
    if blockers:
        lines.append(f"NOT READY - {len(blockers)} blocker(s) must be resolved.")
    else:
        lines.append(
            f"Ready to process. ({len(warnings)} warning(s) to review.)"
            if warnings else "Ready to process."
        )
    lines.append("=" * 56)
    return "\n".join(lines)

"""The state machine that runs a kitting batch.

    LOAD_EXCEL -> VALIDATE -> CONNECT_SAP -> AWAIT_CONFIRMATION
      -> ZPRO (per order) -> VALIDATE_COMPLETION
      -> CO04 -> PRINT -> VERIFY_FILES -> COMPLETE
                                       \\-> HALTED

Every transition is persisted before the next begins, so an interrupted run
resumes from the last verified work order.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..agents.mistral_agent import MistralAdvisor
from ..audit.log import AuditLog
from ..excel.reader import read_workbook
from ..excel.validator import preview, validate
from ..models import Job, KittingError, Severity, Workbook
from ..printing import pdf_validator, pdf_writer
from ..sap import messages as msg
from ..sap.co04 import Co04Flow
from ..sap.connection import Session
from ..sap.controls import Controls
from ..sap.zpro import ZproFlow
from .state import OrderState, Phase, RunState, fingerprint

log = logging.getLogger(__name__)

Confirmer = Callable[[str], bool]


@dataclass
class RunReport:
    state: RunState
    book: Optional[Workbook] = None
    pdf_report: Optional[pdf_validator.PdfReport] = None
    halted: bool = False
    halt_reason: str = ""
    narrative: Dict[str, object] = field(default_factory=dict)

    def summary(self) -> str:
        state = self.state
        posted, failed = state.posted, state.failed
        jobs = list(state.orders.values())

        lines = [
            "=" * 44,
            "PRODUCTION AUTOMATION " + ("HALTED" if self.halted else "COMPLETE"),
            "=" * 44,
            "",
            f"Run ID:       {state.run_id}",
            f"Mode:         {'DRY RUN' if state.dry_run else 'LIVE'}",
            f"Work orders:  {len(jobs)}",
            f"Successful:   {len(posted)}",
            f"Failed:       {len(failed)}",
            "",
        ]

        if posted:
            blocks = state.contiguous_blocks()
            lines.append(f"Print range{'s' if len(blocks) > 1 else ' '}:")
            for first, last in blocks:
                count = len(state.orders_in_block(first, last))
                lines.append(f"  {first} - {last}  ({count} orders)")
            lines.append("")

        for record in jobs:
            lines.append(
                f"  [{record.state.value:<11}] {record.work_order}"
                + (f"  {record.sap_message[:60]}" if record.sap_message else "")
            )

        if self.pdf_report:
            lines += ["", self.pdf_report.summary()]

        if self.halted:
            lines += ["", f"HALTED: {self.halt_reason}"]

        lines += ["", "=" * 44]
        return "\n".join(lines)


class Orchestrator:
    def __init__(
        self,
        config: dict,
        session: Session,
        controls: Controls,
        advisor: Optional[MistralAdvisor] = None,
        confirmer: Optional[Confirmer] = None,
        state_path: Optional[Path] = None,
    ) -> None:
        self.config = config
        self.session = session
        self.controls = controls
        self.advisor = advisor
        self.confirmer = confirmer
        self.state_path = state_path

    # -- entry points ------------------------------------------------------

    def run(
        self,
        workbook_path: str | Path,
        limit: Optional[int] = None,
        do_zpro: bool = True,
        do_print: bool = True,
        resume: bool = False,
    ) -> RunReport:
        book, state, audit = self._prepare(workbook_path, limit, resume)
        report = RunReport(state=state, book=book)

        jobs = book.jobs[:limit] if limit else book.jobs

        if do_zpro:
            state.set_phase(Phase.ZPRO)
            if not self._process_orders(jobs, book, state, audit, report):
                return report

        state.set_phase(Phase.VALIDATE_COMPLETION)
        if not state.posted:
            return self._halt(report, state, audit, "no work orders posted")

        if do_print:
            if not self._print_documents(state, audit, report):
                return report

        state.set_phase(Phase.COMPLETE)
        audit.record("run_complete", result="SUCCESS")
        self._narrate(report, state)
        return report

    # -- phases ------------------------------------------------------------

    def _prepare(
        self, workbook_path: str | Path, limit: Optional[int], resume: bool
    ) -> tuple[Workbook, RunState, AuditLog]:
        path = Path(workbook_path)
        book = read_workbook(
            path,
            sheet_name=self.config.get("excel", {}).get("sheet_name"),
            work_order_label=self.config.get("excel", {}).get(
                "work_order_label", "work order"
            ),
        )

        anomalies = validate(book, expected_pairs=limit)
        blockers = [a for a in anomalies if a.severity is Severity.BLOCKER]
        report_text = preview(book, anomalies, limit)
        print(report_text)

        if blockers:
            raise KittingError(
                f"{len(blockers)} pre-flight blocker(s). Nothing was sent to SAP."
            )

        state = self._load_or_create_state(path, resume)
        jobs = book.jobs[:limit] if limit else book.jobs
        for job in jobs:
            state.register(job.work_order, len(job.serials))
        state.save()

        audit = AuditLog(
            directory=Path(self.config.get("logs_dir", "logs")),
            run_id=state.run_id,
            operator=state.operator,
            workbook=str(path),
        )
        audit.record(
            "run_start",
            result="DRY_RUN" if state.dry_run else "LIVE",
            serial_count=sum(len(job.serials) for job in jobs),
        )
        for anomaly in anomalies:
            audit.record(
                "preflight_anomaly", work_order=anomaly.work_order or "",
                result=anomaly.severity.value, error=f"{anomaly.code}: {anomaly.message}",
            )

        if not self._confirm(book, jobs, state):
            raise KittingError("operator cancelled at the confirmation prompt")

        state.set_phase(Phase.CONNECT_SAP)
        self.session.connect() if hasattr(self.session, "connect") else None
        return book, state, audit

    def _load_or_create_state(self, path: Path, resume: bool) -> RunState:
        target = self.state_path or Path(
            self.config.get("state_dir", "logs")
        ) / f"state_{path.stem}.json"

        if resume and target.exists():
            state = RunState.load(target)
            current = fingerprint(path)
            if state.workbook_fingerprint and state.workbook_fingerprint != current:
                raise KittingError(
                    f"{path.name} has changed since run {state.run_id} started. "
                    f"Resuming against different data risks double-posting - "
                    f"start a fresh run instead."
                )
            log.info(
                "resuming run %s: %d posted, %d pending",
                state.run_id, len(state.posted), len(state.pending),
            )
            return state

        state = RunState(
            workbook=str(path),
            workbook_fingerprint=fingerprint(path),
            dry_run=getattr(self.session, "dry_run", True),
        ).bind(target)
        state.save()
        return state

    def _confirm(self, book: Workbook, jobs: List[Job], state: RunState) -> bool:
        if self.confirmer is None or state.dry_run:
            return True

        state.set_phase(Phase.AWAIT_CONFIRMATION)
        prompt = (
            f"{len(jobs)} work orders detected.\n"
            f"First: {jobs[0].work_order}\n"
            f"Last:  {jobs[-1].work_order}\n"
            f"Serial numbers: {sum(len(j.serials) for j in jobs)}\n"
            f"Warnings: {len(book.warnings)}\n\n"
            f"This will POST GOODS ISSUES in SAP. Begin?"
        )
        return self.confirmer(prompt)

    def _process_orders(
        self,
        jobs: List[Job],
        book: Workbook,
        state: RunState,
        audit: AuditLog,
        report: RunReport,
    ) -> bool:
        flow = ZproFlow(self.session, self.controls, book, self.config.get("zpro", {}))
        max_retries = int(self.config.get("run", {}).get("max_retries", 1))

        for index, job in enumerate(jobs, start=1):
            allowed, why = state.may_post(job.work_order)
            if not allowed:
                log.info("[%d/%d] skipping %s: %s", index, len(jobs), job.work_order, why)
                audit.record(
                    "order_skipped", work_order=job.work_order, result="SKIPPED", error=why
                )
                continue

            attempt = 0
            while True:
                attempt += 1
                state.begin(job.work_order)
                log.info(
                    "[%d/%d] %s attempt %d", index, len(jobs), job.work_order, attempt
                )
                result = flow.post(job)

                if result.posted:
                    state.finish(
                        job.work_order, OrderState.POSTED,
                        sap_message=_first_text(result.raw_messages),
                        message_class=(
                            result.classification.message_class.value
                            if result.classification else ""
                        ),
                        document=result.document,
                    )
                    audit.record(
                        "order_posted", work_order=job.work_order, transaction="ZPRO",
                        serial_count=result.serials_written,
                        serials=job.serial_numbers, result="POSTED",
                        message_class=(
                            result.classification.message_class.value
                            if result.classification else ""
                        ),
                        sap_message=_first_text(result.raw_messages),
                        document=result.document, attempt=attempt,
                    )
                    break

                decision = self._decide(job, result, book)
                audit.record(
                    "order_failed", work_order=job.work_order, transaction="ZPRO",
                    serial_count=result.serials_written, result=decision,
                    message_class=(
                        result.classification.message_class.value
                        if result.classification else ""
                    ),
                    sap_message=_first_text(result.raw_messages),
                    error=result.error, attempt=attempt,
                )

                if decision == "retry" and attempt <= max_retries:
                    continue

                final = (
                    OrderState.UNCERTAIN if result.uncertain else OrderState.FAILED
                )
                shot = self._screenshot(job.work_order)
                state.finish(
                    job.work_order, final,
                    sap_message=_first_text(result.raw_messages),
                    message_class=(
                        result.classification.message_class.value
                        if result.classification else ""
                    ),
                    error=result.error, screenshot=str(shot or ""),
                )

                if decision in ("stop", "retry"):
                    self._halt(
                        report, state, audit,
                        f"{job.work_order}: {result.error}",
                    )
                    return False
                break

        return True

    def _decide(self, job: Job, result, book: Workbook) -> str:
        """Rule first; ask Mistral only for what the rules could not place."""
        classification = result.classification
        if classification is None:
            return "stop"

        if classification.message_class is msg.MessageClass.CRITICAL_ERROR:
            return "stop"
        if classification.message_class is msg.MessageClass.RETRYABLE_ERROR:
            return "retry"
        if classification.message_class is not msg.MessageClass.UNKNOWN_MESSAGE:
            return "stop"

        if self.advisor is None:
            return "stop"

        try:
            advice = self.advisor.interpret_message(
                work_order=job.work_order,
                message_type=classification.raw_type,
                message_text=classification.raw_text,
                serialised_materials=book.serialised_materials,
                non_serialised_materials=book.non_serialised_materials,
                serials_written=result.serials_written,
            )
        except Exception as exc:  # noqa: BLE001 - advisory only, never fatal
            log.warning("Mistral unavailable (%s) - stopping, as the rules say", exc)
            return "stop"

        # An advisory "continue" past an unknown message still does not post
        # anything new; it only lets the batch move on. Anything less than
        # confident is treated as stop.
        if advice.recommendation == "continue" and not advice.safe_to_continue:
            log.info("advice was 'continue' at %.0f%% - too low, stopping",
                     advice.confidence * 100)
            return "stop"
        return advice.recommendation

    def _print_documents(
        self, state: RunState, audit: AuditLog, report: RunReport
    ) -> bool:
        """Reprint the posted orders, one CO04 run per contiguous block.

        A batch is not always one unbroken range - the orders may come from two
        series - and a single From/To would reprint everything in between. So
        each block is selected and printed separately, and the PDFs are pooled.
        """
        state.set_phase(Phase.CO04)
        blocks = state.contiguous_blocks()
        if not blocks:
            return self._halt(report, state, audit, "no posted orders to print") and False

        if len(blocks) > 1:
            log.info(
                "posted orders form %d blocks; running CO04 once per block "
                "so the reprint cannot pull in orders this run did not post: %s",
                len(blocks),
                ", ".join(f"{first}-{last}" for first, last in blocks),
            )

        flow = Co04Flow(self.session, self.controls, self.config.get("co04", {}))
        collected: Dict[str, Path] = {}

        for first, last in blocks:
            orders = state.orders_in_block(first, last)
            result = flow.reprint(first, last, len(orders))

            if not result.printed:
                self._halt(report, state, audit, f"CO04 {first}-{last}: {result.error}")
                return False

            audit.record(
                "co04_printed", transaction="CO04", result="PRINTED",
                work_order=f"{first}-{last}", serial_count=result.selected_count,
            )

            if state.dry_run:
                continue

            state.set_phase(Phase.PRINT)
            try:
                output = pdf_writer.capture(self.config.get("printing", {}), orders)
            except KittingError as exc:
                self._halt(report, state, audit, f"PDF capture {first}-{last}: {exc}")
                return False
            collected.update(output.pdfs)

        if state.dry_run:
            log.info("[dry-run] skipping PDF capture")
            state.set_phase(Phase.VERIFY_FILES)
            return True

        state.pdf_paths = {w: str(p) for w, p in collected.items()}
        state.set_phase(Phase.VERIFY_FILES)

        report.pdf_report = pdf_validator.verify(
            collected, sorted(state.posted, key=int)
        )
        for check in report.pdf_report.checks:
            audit.record(
                "pdf_written", work_order=check.work_order,
                pdf=str(check.path), result="OK" if check.ok else "FAIL",
                error=check.problem,
            )

        if not report.pdf_report.ok:
            self._halt(
                report, state, audit,
                f"PDF verification failed:\n{report.pdf_report.summary()}",
            )
            return False
        return True

    # -- helpers -----------------------------------------------------------

    def _halt(
        self, report: RunReport, state: RunState, audit: AuditLog, reason: str
    ) -> RunReport:
        log.error("HALTED: %s", reason)
        state.halt(reason)
        audit.record("run_halted", result="HALTED", error=reason)
        report.halted = True
        report.halt_reason = reason
        self._narrate(report, state)
        return report

    def _screenshot(self, work_order: str) -> Optional[Path]:
        directory = self.config.get("run", {}).get("screenshot_dir")
        if not directory:
            return None
        return self.session.screenshot(Path(directory) / f"{work_order}.png")

    def _narrate(self, report: RunReport, state: RunState) -> None:
        if self.advisor is None:
            return
        try:
            report.narrative = self.advisor.explain_run({
                "run_id": state.run_id,
                "dry_run": state.dry_run,
                "posted": state.posted,
                "failed": state.failed,
                "halt_reason": state.halt_reason,
                "orders": {w: r.to_dict() for w, r in state.orders.items()},
            })
        except Exception as exc:  # noqa: BLE001
            log.warning("could not generate run narrative: %s", exc)


def _first_text(raw_messages: List[tuple]) -> str:
    return raw_messages[0][1] if raw_messages else ""

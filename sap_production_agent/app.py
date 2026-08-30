"""SAP ZPRO + CO04 kitting automation.

    python app.py inspect  --sheet ZPRO.xlsx           # what is in the workbook
    python app.py validate --sheet ZPRO.xlsx           # full pre-flight
    python app.py zpro     --sheet ZPRO.xlsx           # dry run (default)
    python app.py zpro     --sheet ZPRO.xlsx --execute
    python app.py print    --sheet ZPRO.xlsx --execute # CO04 + PDFs only
    python app.py full     --sheet ZPRO.xlsx --execute # everything
    python app.py resume   --sheet ZPRO.xlsx --execute # continue a halted run

Dry run is the default everywhere. --execute is the only thing that lets a
keystroke reach SAP.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

from sap_agent.agents import mistral_agent
from sap_agent.excel.reader import read_workbook
from sap_agent.excel.validator import preview, validate
from sap_agent.models import KittingError, Severity
from sap_agent.sap.connection import SapSession
from sap_agent.sap.controls import Controls
from sap_agent.workflow.orchestrator import Orchestrator


def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


def load_yaml(path: Path, what: str) -> dict:
    if not path.exists():
        raise KittingError(
            f"{path} not found. Copy {path.stem}.example.yaml to {path.name} "
            f"and fill in your {what}."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def confirm(prompt: str) -> bool:
    print("\n" + "=" * 56)
    print(prompt)
    print("=" * 56)
    return input("Type START to begin, anything else to cancel: ").strip() == "START"


def cmd_inspect(args) -> int:
    """Show the normalised jobs, without validating or touching SAP."""
    book = read_workbook(args.sheet)
    jobs = book.to_jobs()
    if args.json:
        print(json.dumps(jobs[: args.limit] if args.limit else jobs, indent=2))
        return 0

    print(f"Worksheet: {book.sheet_name}   work orders: {len(book.jobs)}")
    print(f"Serialised materials:     {', '.join(book.serialised_materials)}")
    print(f"Non-serialised materials: {', '.join(book.non_serialised_materials)}")
    print()
    for job in book.jobs[: args.limit] if args.limit else book.jobs:
        print(f"  {job.column_letter:>2} {job.work_order} [{job.fibre_pair}] "
              f"{len(job.serials)} serials")
        if args.verbose:
            for component in job.serials:
                print(f"       {component.material:<16} {component.serial}")
    return 0


def cmd_validate(args) -> int:
    book = read_workbook(args.sheet)
    anomalies = validate(book, expected_pairs=args.limit)
    print(preview(book, anomalies, args.limit))

    controls_path = Path(args.controls)
    if controls_path.exists():
        gaps = Controls.load(controls_path).missing()
        if gaps:
            print(f"\nControl IDs still unset in {controls_path} ({len(gaps)}):")
            for gap in gaps:
                print(f"  {gap}")
            print("\nRun: python tools/discover_controls.py")
    else:
        print(f"\n{controls_path} not found - copy controls.example.yaml to it.")

    return 1 if any(a.severity is Severity.BLOCKER for a in anomalies) else 0


def cmd_run(args, do_zpro: bool, do_print: bool, resume: bool = False) -> int:
    config = load_yaml(Path(args.config), "settings")
    dry_run = not args.execute
    # A dry run may rehearse with unset controls; a live run may not.
    controls = Controls.load(Path(args.controls), permissive=dry_run)

    session = SapSession(config.get("sap", {}), dry_run=dry_run)
    advisor = mistral_agent.load(config) if not args.no_mistral else None

    orchestrator = Orchestrator(
        config=config,
        session=session,
        controls=controls,
        advisor=advisor,
        confirmer=None if (dry_run or args.yes) else confirm,
    )

    report = orchestrator.run(
        workbook_path=args.sheet,
        limit=args.limit,
        do_zpro=do_zpro,
        do_print=do_print,
        resume=resume,
    )

    print("\n" + report.summary())
    if report.narrative:
        print("\n" + report.narrative.get("headline", ""))
        print(report.narrative.get("what_happened", ""))
        for action in report.narrative.get("next_actions", []):
            print(f"  - {action}")

    return 1 if report.halted else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", choices=[
        "inspect", "validate", "zpro", "print", "full", "resume",
    ])
    parser.add_argument("--sheet", required=True, help="the scan workbook")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--controls", default="controls.yaml")
    parser.add_argument("--execute", action="store_true",
                        help="actually drive SAP (default is a dry run)")
    parser.add_argument("--limit", type=int, default=None,
                        help="process only the first N work orders (fibre pairs)")
    parser.add_argument("--yes", action="store_true",
                        help="skip the confirmation prompt")
    parser.add_argument("--no-mistral", action="store_true",
                        help="force the fully deterministic path")
    parser.add_argument("--json", action="store_true", help="inspect: emit JSON")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)

    try:
        if args.command == "inspect":
            return cmd_inspect(args)
        if args.command == "validate":
            return cmd_validate(args)
        if args.command == "zpro":
            return cmd_run(args, do_zpro=True, do_print=False)
        if args.command == "print":
            return cmd_run(args, do_zpro=False, do_print=True)
        if args.command == "full":
            return cmd_run(args, do_zpro=True, do_print=True)
        if args.command == "resume":
            return cmd_run(args, do_zpro=True, do_print=True, resume=True)
    except KittingError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrupted - run state is saved; use 'resume' to continue",
              file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

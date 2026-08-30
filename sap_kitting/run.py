"""Kitting run: spreadsheet -> ZPRO -> one PDF per work order.

    python run.py --sheet kitting.xlsx                 # dry run, prints the plan
    python run.py --sheet kitting.xlsx --execute       # actually drives SAP
    python run.py --sheet kitting.xlsx --only 4500123456
    python run.py --sheet kitting.xlsx --suggest-columns   # ask Mistral to map headers

Dry run is the default on purpose: this posts against a production ERP.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

from kitting import brain as brain_module
from kitting import zpro
from kitting.models import KittingError
from kitting.sap import SapSession
from kitting.sheet import read_workbook

MAX_RETRIES = 2


def setup_logging(log_file: str | None, verbose: bool) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )


def load_config(path: Path) -> dict:
    if not path.exists():
        raise KittingError(
            f"{path} not found. Copy config.example.yaml to config.yaml and "
            f"fill in your ZPRO field IDs."
        )
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def suggest_columns(sheet_path: Path, config: dict) -> int:
    """Ask Mistral to map the sheet's headers, then print YAML to paste in."""
    import pandas as pd

    frame = pd.read_excel(sheet_path, header=config["sheet"].get("header_row", 0))
    headers = [str(c) for c in frame.columns]
    sample = frame.head(5).to_dict(orient="records")

    forced = dict(config)
    forced.setdefault("brain", {})["mode"] = "mistral"
    engine = brain_module.load(forced)
    if engine is None:
        raise KittingError("could not construct the Mistral brain")

    mapping = engine.map_columns(headers, sample)

    print("\nPaste into config.yaml under sheet.columns, after checking it:\n")
    print("  columns:")
    for logical, header in mapping.items():
        print(f"    {logical}: {header!r}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sheet", required=True, help="path to the scan spreadsheet")
    parser.add_argument("--config", default="config.yaml", help="config file")
    parser.add_argument("--execute", action="store_true",
                        help="actually drive SAP (default is a dry run)")
    parser.add_argument("--only", action="append", default=None,
                        help="process only this work order; repeatable")
    parser.add_argument("--suggest-columns", action="store_true",
                        help="ask Mistral to map the sheet headers, then exit")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    try:
        config = load_config(Path(args.config))
    except KittingError as exc:
        print(exc, file=sys.stderr)
        return 2

    setup_logging(config.get("run", {}).get("log_file"), args.verbose)
    log = logging.getLogger("run")

    try:
        if args.suggest_columns:
            return suggest_columns(Path(args.sheet), config)

        orders = read_workbook(args.sheet, config["sheet"])

        if args.only:
            wanted = {str(o).strip() for o in args.only}
            orders = [o for o in orders if o.order_number in wanted]
            if not orders:
                log.error("none of %s found in the sheet", sorted(wanted))
                return 1

        dry_run = not args.execute
        log.info(
            "%d work order(s) to process%s",
            len(orders), " [DRY RUN - SAP will not be touched]" if dry_run else "",
        )
        for order in orders:
            log.info("  %s", order.summary())

        engine = brain_module.load(config)
        sap = SapSession(config["sap"], dry_run=dry_run).connect()

        results = _run_with_triage(sap, orders, config, engine, log)

    except KittingError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130

    ok = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]

    print(f"\n{'-' * 60}")
    print(f"{len(ok)} succeeded, {len(failed)} failed, "
          f"{len(orders) - len(results)} not attempted")
    for result in results:
        print(result.line())

    return 0 if not failed else 1


def _run_with_triage(sap, orders, config, engine, log):
    """Process each order, letting the brain classify failures when enabled."""
    stop_on_error = config.get("run", {}).get("stop_on_error", True)
    results = []

    for order in orders:
        attempt = 0
        while True:
            result = zpro.process_order(sap, order, config)
            if result.ok or engine is None:
                break

            attempt += 1
            if attempt > MAX_RETRIES:
                log.error("giving up on %s after %d attempts", order.order_number, attempt)
                break

            status_type, status_text = sap.status_message()
            verdict = engine.triage(
                order_number=order.order_number,
                error=result.error or "",
                status_message=f"{status_type} {status_text}".strip(),
                popup_text=sap.modal_text(),
            )
            result.error = f"{result.error} | triage: {verdict.reason}"

            if verdict.verdict != "retry":
                break
            log.info("retrying %s (attempt %d)", order.order_number, attempt + 1)

        results.append(result)
        if not result.ok and stop_on_error:
            log.error("stopping: run.stop_on_error is true")
            break

    return results


if __name__ == "__main__":
    raise SystemExit(main())

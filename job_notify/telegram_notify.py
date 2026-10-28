#!/usr/bin/env python3
"""Telegram notifications for the job-application workflow (@BaksAstraBot).

Standard library only, so it runs on the cloud container and on the Windows PC
with any Python 3.8+.

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (default 5373117361) from the
environment. The token is
never printed or logged; error output is scrubbed of it.

Usage:
  telegram_notify.py test
  telegram_notify.py submitted --company X --role Y --link URL --confirmation "Reed: 'Application sent'"
  telegram_notify.py failed    --company X --role Y --link URL --reason "Upload rejected"
  telegram_notify.py blocker   --company X --role Y --link URL --reason "Needs sign-in" [--action URL]
  telegram_notify.py summary   --submitted 12 --failed 1 --blocked 2 --skipped 3 [--details "..."]
  telegram_notify.py summary   --ledger path/to/ledger.csv

A "submitted" message is only sent as SUBMITTED when --confirmation is given
(the confirmation page text, email or portal status that proves it). Without it
the message is downgraded to "UNCONFIRMED", so it never claims success that
was not seen.

Exit codes: 0 sent and Telegram replied ok, 1 Telegram refused or network
error, 2 missing configuration or bad arguments.
"""

import argparse
import csv
import html
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone

API = "https://api.telegram.org"
DEFAULT_CHAT_ID = "5373117361"  # Nuru's chat with @BaksAstraBot (not a secret)
TIMEOUT = 20


def _token():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set in the environment.")
    return token


def _chat_id():
    return os.environ.get("TELEGRAM_CHAT_ID", "").strip() or DEFAULT_CHAT_ID


def _scrub(text, token):
    return text.replace(token, "<TOKEN>") if token else text


def send(text):
    """Send an HTML message. Returns the parsed Telegram response."""
    token, chat = _token(), _chat_id()
    payload = json.dumps({
        "chat_id": chat,
        "text": text[:4096],
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        f"{API}/bot{token}/sendMessage", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except ValueError:
            return {"ok": False, "error_code": e.code, "description": _scrub(str(e), token)}
    except (urllib.error.URLError, OSError) as e:
        return {"ok": False, "error_code": None,
                "description": "network error: " + _scrub(str(e), token)}


def _esc(value):
    return html.escape(str(value)) if value else ""


def _job_lines(a):
    lines = []
    if a.company:
        lines.append(f"<b>Company:</b> {_esc(a.company)}")
    if a.role:
        lines.append(f"<b>Role:</b> {_esc(a.role)}")
    if getattr(a, "board", None):
        lines.append(f"<b>Board:</b> {_esc(a.board)}")
    if a.link:
        lines.append(f'<b>Link:</b> <a href="{_esc(a.link)}">{_esc(a.link)}</a>')
    return lines


def _stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def build_message(a):
    if a.event == "test":
        return ("🔔 <b>Test notification</b>\n"
                "Job-application alerts from @BaksAstraBot are set up.\n"
                f"<i>{_stamp()}</i>")
    if a.event == "submitted":
        if a.confirmation:
            head = "✅ <b>Application SUBMITTED (confirmed)</b>"
            tail = [f"<b>Confirmation:</b> {_esc(a.confirmation)}"]
        else:
            head = "❔ <b>Application UNCONFIRMED</b>"
            tail = ["No confirmation was seen, so this is NOT counted as submitted. Check the portal or inbox."]
        return "\n".join([head, *_job_lines(a), *tail, f"<i>{_stamp()}</i>"])
    if a.event == "failed":
        return "\n".join(["❌ <b>Application FAILED</b>", *_job_lines(a),
                          f"<b>Reason:</b> {_esc(a.reason or 'not given')}", f"<i>{_stamp()}</i>"])
    if a.event == "blocker":
        lines = ["⚠️ <b>Needs your input</b>", *_job_lines(a),
                 f"<b>What's needed:</b> {_esc(a.reason or 'not given')}"]
        if a.action:
            lines.append(f'<b>Do it here:</b> <a href="{_esc(a.action)}">{_esc(a.action)}</a>')
        lines.append(f"<i>{_stamp()}</i>")
        return "\n".join(lines)
    if a.event == "summary":
        counts = Counter()
        if a.ledger:
            counts = summarise_ledger(a.ledger)
        for key in ("submitted", "failed", "blocked", "skipped"):
            val = getattr(a, key)
            if val is not None:
                counts[key] = val
        lines = ["📋 <b>Run summary</b>" + (f" — {_esc(a.run)}" if a.run else ""),
                 f"✅ Submitted (confirmed): {counts['submitted']}",
                 f"❔ Unconfirmed: {counts['unconfirmed']}" if counts["unconfirmed"] else None,
                 f"❌ Failed: {counts['failed']}",
                 f"⚠️ Waiting on you: {counts['blocked']}",
                 f"⏭ Skipped: {counts['skipped']}"]
        if a.details:
            lines.append(_esc(a.details))
        lines.append(f"<i>{_stamp()}</i>")
        return "\n".join(l for l in lines if l is not None)
    raise SystemExit(f"unknown event {a.event}")


# Ledger statuses mapped to summary buckets. Anything that is not clearly a
# confirmed submission is never counted as submitted.
_STATUS_MAP = {
    "submitted": "submitted", "confirmed": "submitted", "sent": "submitted",
    "failed": "failed", "error": "failed",
    "blocked": "blocked", "blocker": "blocked", "needs_input": "blocked", "waiting": "blocked",
    "skipped": "skipped", "declined": "skipped",
}


def summarise_ledger(path):
    """Count rows in a CSV ledger with a 'status' column.

    A row counts as submitted only if it also has a non-empty 'confirmation'
    (or 'evidence') column; otherwise it is reported as unconfirmed.
    """
    counts = Counter()
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            bucket = _STATUS_MAP.get(row.get("status", "").lower(), "unconfirmed")
            if bucket == "submitted" and not (row.get("confirmation") or row.get("evidence")):
                bucket = "unconfirmed"
            counts[bucket] += 1
    return counts


def parse_args(argv):
    p = argparse.ArgumentParser(description="Send job-application updates to Telegram.")
    sub = p.add_subparsers(dest="event", required=True)
    sub.add_parser("test")
    for name in ("submitted", "failed", "blocker"):
        s = sub.add_parser(name)
        s.add_argument("--company")
        s.add_argument("--role")
        s.add_argument("--link")
        s.add_argument("--board")
        if name == "submitted":
            s.add_argument("--confirmation", help="proof of submission (confirmation text, ref no., email)")
        else:
            s.add_argument("--reason")
        if name == "blocker":
            s.add_argument("--action", help="URL where Nuru can act")
    s = sub.add_parser("summary")
    s.add_argument("--run", help="run label, e.g. '2026-10-28 morning'")
    s.add_argument("--ledger", help="CSV with status[,confirmation] columns")
    for key in ("submitted", "failed", "blocked", "skipped"):
        s.add_argument(f"--{key}", type=int)
    s.add_argument("--details")
    p.add_argument("--dry-run", action="store_true", help="print the message instead of sending")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv if argv is not None else sys.argv[1:])
    text = build_message(a)
    if a.dry_run:
        print(text)
        return 0
    try:
        resp = send(text)
    except SystemExit as e:
        print(f"telegram_notify: {e}", file=sys.stderr)
        return 2
    if resp.get("ok"):
        msg_id = resp.get("result", {}).get("message_id")
        print(f"telegram_notify: sent ({a.event}), message_id={msg_id}")
        return 0
    print(f"telegram_notify: Telegram refused ({resp.get('error_code')}): {resp.get('description')}",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

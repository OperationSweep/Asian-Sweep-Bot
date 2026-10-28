# Job-application Telegram alerts (@BaksAstraBot)

Sends Nuru a Telegram message for each confirmed submission, failure, blocker
that needs Nuru, and an end-of-run summary.

| File | Use where |
|---|---|
| `telegram_notify.py` | Cloud sessions, or the PC if Python 3.8+ is installed (stdlib only) |
| `Send-JobTelegram.ps1` | The Windows PC apply run (no Python needed) |

## Configuration

- `TELEGRAM_BOT_TOKEN` (required, secret). Set it in the cloud environment's
  variables, or on the PC as a user environment variable. Never commit, print
  or log it.
- `TELEGRAM_CHAT_ID` (optional). Defaults to `5373117361`.
- Nuru must have pressed **Start** on https://t.me/BaksAstraBot once, or
  Telegram returns `403 bot can't initiate conversation`.

## Events

```
python telegram_notify.py test
python telegram_notify.py submitted --company "Acme" --role "IT Ops Lead" --link URL --board Reed --confirmation "Reed: 'Your application has been sent'"
python telegram_notify.py failed    --company "Acme" --role "..." --link URL --reason "CV upload rejected"
python telegram_notify.py blocker   --company "Acme" --role "..." --link URL --reason "Sign in to Totaljobs" --action https://www.totaljobs.com/account/signin
python telegram_notify.py summary   --run "28 Oct morning" --submitted 12 --failed 1 --blocked 2 --skipped 3
python telegram_notify.py summary   --run "28 Oct morning" --ledger applications/2026-10-28/ledger.csv
```

PowerShell takes the same names: `.\Send-JobTelegram.ps1 -Event submitted -Company ... -Confirmation ...`.
Add `--dry-run` / `-DryRun` to print the message without sending.

## Accuracy rule

Only send `submitted` with `--confirmation` after the portal's confirmation
page, a confirmation email or a "sent" status was actually seen. Without
`--confirmation` the message goes out as **UNCONFIRMED** and is never counted
as a submission. In `--ledger` mode a row only counts as submitted if its
`confirmation` (or `evidence`) column is filled.

Exit codes: `0` Telegram replied `ok`, `1` Telegram refused or network error
(the message is printed with the token scrubbed), `2` token missing.

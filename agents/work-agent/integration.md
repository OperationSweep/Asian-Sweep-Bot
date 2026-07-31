# Integration with the work system

Per-connector policy and the n8n workflows that make the agent part of the operation
rather than a window you have to remember to open.

The governing principle: **an agent that only responds is a tool; an agent that observes
and reports is a colleague.** The connectors below exist so it can see the work, and the
n8n workflows exist so it speaks without being asked.

---

## Connector policy

Mistral registers MCP servers as managed connectors — tools are discovered automatically
and executed server-side. Read scopes first; write scopes are earned one at a time, and
each one gets a golden-set case *before* it gets the permission.

| Connector | Read | Write | Rationale |
|---|---|---|---|
| **Gmail** | Search, read threads/labels | **Drafts only** | Drafting is most of the value. Sending is where an agent can embarrass you in front of a supplier. |
| **Calendar** | List, search, availability | **Propose only** | May create events when explicitly asked with a specific time. Ambiguity → propose. |
| **Drive** | Search, read | **Create only** | Never overwrite. New files with dated names; the human moves and replaces. |
| **GitHub** | Issues, PRs, commits, Actions, code | **Draft PRs only** | Never pushes to `main`, never merges, never force-pushes. |
| **Shopify** | Products, orders, customers, inventory, analytics | **Unpublished only** | Analytics is the real prize. Live storefront changes and inventory commitments are human. |
| **Stripe** | Charges, subscriptions, payouts *(needs OAuth)* | **None** | Read-only forever. Money movement is never an agent action. |
| **n8n** | Workflow status and history | **None** | Reads its own plumbing to report failures. Editing workflows that trigger it is a loop nobody wants to debug. |
| **Motion** | — | **Human-initiated only** | Spends credits. The agent may write briefs; a human presses the button. |

### Why read scopes come first

Read access removes the largest tax on working with an agent — telling it what is going
on. An agent that can see last week's orders, the open PRs and tomorrow's calendar answers
in one turn what would otherwise take four. It is also where the risk is lowest, so it is
where trust should be built.

### On Stripe

Currently unauthorised. The OAuth flow needs an interactive session — it cannot be
completed from a headless run. Until then the agent has no revenue visibility, which
mostly limits pre-launch usefulness but will matter a great deal on day one of trading.

---

## Where each connector earns its place

**Ecommerce, pre-launch.** Gmail carries the supplier RFQ thread — the agent normalises
quotes into `PLB-002`'s comparison table as replies arrive, instead of you rebuilding a
spreadsheet five times. Drive holds label and claims review documents. GitHub tracks the
launch checklist as issues.

**Ecommerce, trading.** Shopify analytics is the highest-value connector in the whole set:
bundle mix, subscription retention, AOV, repeat rate — every `[NOT MEASURED]` row in
`30-metrics.md` is a Shopify query away, and each one that gets measured supersedes an
estimate the entire financial model currently rests on.

**Trading.** GitHub for config diffs and the weekly review issue. The journals —
`signals.csv`, `trades.csv`, `events.jsonl` — parsed via code interpreter for `PLB-001`.
Note they are gitignored, so they reach the agent by upload or by a local run, not through
the GitHub connector. The durable journal is the main thing the scaffold rebuild bought;
without it, a weekly signal review would have nothing to read.

**Ops.** Calendar and Gmail for the daily brief. n8n for its own health.

---

## The n8n workflows

Four. The first three are the learning loop; the fourth is what makes the agent visible
day to day.

### WF-1 · Capture

**Trigger:** webhook, fired after each agent conversation.
**Does:** extracts the fenced ```learning``` block, validates against `SCHEMA.md`, appends
JSON to `memory/inbox/YYYY-MM-DD.jsonl` in the repo.
**Fails if:** the block is malformed. Log and continue — never block a response on capture.

### WF-2 · Consolidate

**Trigger:** cron, 02:00 daily.
**Does:** reads the inbox, calls `mistral-small-latest` with the consolidation prompt
(dedupe → detect supersession → assign IDs → reject rule violations → route by type),
writes candidates to `memory/candidates/`.
**Fails if:** the inbox is empty. Exit quietly; that is a normal night.

### WF-3 · Promotion PR

**Trigger:** cron, Friday 09:00.
**Does:** applies candidates to the memory files on a branch
`memory/week-<iso-week>`, opens a **draft PR**, assigns you, clears `candidates/`.
**Fails if:** no candidates. Skip — do not open an empty PR, or the review becomes noise
you learn to ignore.

### WF-4 · Daily brief

**Trigger:** cron, 07:00 Dubai.
**Does:** starts a conversation with the agent: *"Daily brief. Overnight trading result,
today's calendar, anything needing a reply in Gmail, movement on the standing priorities
in CHR-010, and any kill-criterion or working-capital warning. Lead with anything
requiring a decision today."*
**Delivers to:** wherever you actually read things.

WF-4 is the one that changes how the agent feels. Everything else is infrastructure; this
is the agent turning up to work.

---

## Deployment

Not alongside the bot. Its host stays boring — the bot modules and nothing else. (The
README is explicit that the bot is not cleared for VPS deployment for live money at all
yet; this keeps the two concerns separate either way.)

`deploy.py` and `evaluate.py` run in GitHub Actions on merge to `main`. n8n runs wherever it
runs today. The only shared secret is `MISTRAL_API_KEY`, which lives in Actions secrets and
in n8n credentials, and nowhere in this repository.

**Never commit** `MISTRAL_API_KEY`, MT5 credentials, Shopify or Stripe tokens. Note that
`config.py` currently holds placeholder MT5 credentials in plaintext — before this repo
goes anywhere near a shared runner, move them to environment variables. That is a
pre-existing issue, not one introduced here, but it becomes materially worse the moment CI
touches this repository.

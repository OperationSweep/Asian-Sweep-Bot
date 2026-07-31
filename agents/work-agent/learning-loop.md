# The learning loop

How the agent actually improves, end to end.

The premise to be clear about first: **a model does not learn from conversation.** Nothing
persists between sessions and no amount of prompting changes that. Continuous learning is
therefore something you *build* — a loop that captures what was established, distils it,
gates it, deploys it, and proves it helped.

Five stages. Each has an owner, a trigger, and a failure mode.

```
   ┌──────────┐   ┌─────────────┐   ┌────────┐   ┌────────┐   ┌──────────┐
   │ CAPTURE  │──▶│ CONSOLIDATE │──▶│ PROMOTE│──▶│ DEPLOY │──▶│ EVALUATE │
   │  agent   │   │ n8n nightly │   │ human  │   │   CI   │   │   CI     │
   └──────────┘   └─────────────┘   └────────┘   └────────┘   └────┬─────┘
        ▲                                                          │
        └────────────────── rollback on regression ────────────────┘
```

---

## 1 · Capture — the agent, every session

The agent ends substantive tasks with a fenced `learning` block (format in
`instructions.md` §2). n8n's capture workflow parses conversation outputs and appends each
block to `memory/inbox/` as JSON.

**Failure mode: over-capture.** An agent that emits a block every turn produces a memory
full of restated documents, and a memory full of everything retrieves nothing. The
instructions push hard against this, and the weekly PR is where you enforce it — if a PR
contains twenty records, tighten the instruction rather than merging them.

**Failure mode: under-capture.** Three empty PRs in a row means the capture step is broken,
not that there was nothing to learn. Check the parser before concluding the loop is idle.

---

## 2 · Consolidate — n8n, nightly

A cheap model pass (`mistral-small-latest` is sufficient) over the inbox:

1. **Deduplicate** against existing memory. Semantically, not by string match — "CAC is
   £71" and "blended CAC measured at £71" are one record.
2. **Detect supersession.** A new `METRIC` on a subject that already has one sets
   `supersedes` on the new record and `superseded-by` on the old.
3. **Assign IDs** — next available per type.
4. **Reject** anything failing the `SCHEMA.md` write rules: not falsifiable, restates an
   indexed document, more than one claim, inferred rather than observed.
5. **Write** survivors into the right file by type.

Consolidation is deliberately mechanical. It does not judge whether a claim is *true* —
that is the human's job at stage 3, and a model that tries to do it here will approve its
own errors.

---

## 3 · Promote — human, weekly

n8n opens a pull request against `agents/work-agent/memory/` every Friday. Title:
`memory: N candidate records for week of <date>`. The diff *is* the review — each record is
a self-contained markdown block.

Merge, edit-then-merge, or reject. Five minutes, per `PLB-004`.

**This gate is the design's load-bearing element.** An agent that writes freely to its own
memory eventually learns something false, retrieves it, acts on it, and records the
outcome as confirmation. Every step in that chain is locally consistent, so no automated
check catches it. The human gate is the only reliable interruption.

The specific thing to watch for: **`DECISION` records the operator never made.** An agent
inferring a decision from context, recording it, then retrieving it as precedent is how a
system starts confidently enforcing rules nobody set.

---

## 4 · Deploy — CI, on merge to main

`deploy.py` runs:

1. Uploads changed memory files to the Mistral Library, replacing prior versions by name.
2. `PATCH /v1/agents/{agent_id}` with the current `instructions.md`, tools and
   `completion_args`, plus `version_message` set to the commit subject and `metadata`
   carrying the git SHA.

Mistral versions agents natively, which is what makes this safe: every deploy is a new
version, `version_message` records why, and `PATCH /v1/agents/{agent_id}/version?version=N`
rolls back instantly. **Agent versions map one-to-one onto commits.** Given a version
number you can find the exact diff that produced it.

---

## 5 · Evaluate — CI, immediately after deploy

`evaluate.py` runs the golden set (`eval/golden-set.yaml`) against the new version and
scores each case with a judge model against `eval/rubric.md`, plus deterministic
`must_include` / `must_not_include` checks.

- **Score ≥ baseline** → new baseline committed.
- **Score < baseline − tolerance** → `--rollback` switches the live agent to the last good
  version and opens an issue with the failing cases.

Without this stage the loop is not learning, it is accumulation. Memory grows, the prompt
drifts, quality moves in some direction, and nobody knows which — because degradation from
a bloated prompt or a false memory produces no error, just worse answers. **The eval set is
what makes "it's learning" a claim with evidence behind it.**

Grow the golden set as failures occur: every `FAILURE` record should become a case. That is
the ratchet — each mistake is made once, then permanently guarded.

---

## What promotion into the system prompt requires

Retrieved memory is the default. Moving something into always-on `instructions.md` needs
all three:

1. It is needed on **most** turns, not merely often.
2. Retrieval demonstrably fails on it — shown by a golden-set case, not by intuition.
3. It fits in one or two sentences.

Everything else stays in the Library. The prompt is a budget of attention, not a filing
cabinet, and the reason to be strict is that overspending it has no visible symptom.

---

## Cadence

| When | What | Who |
|---|---|---|
| Every session | Capture blocks | Agent |
| Nightly 02:00 | Consolidate inbox | n8n |
| Friday 09:00 | Promotion PR | n8n → human |
| On merge | Deploy + evaluate | CI |
| Monthly | Prune superseded records; review eval coverage | Human |
| Quarterly | Re-read `instructions.md` end to end; cut what has stopped earning its tokens | Human |

The quarterly read matters more than it sounds. System prompts accrete — every incident
adds a line, nothing ever removes one, and after a year the agent is carrying a paragraph
about a problem that was fixed in month two.

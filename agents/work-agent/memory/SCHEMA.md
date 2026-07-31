# Memory record schema

Every memory file is a list of records in this format. The format exists to satisfy three
constraints at once: it must chunk cleanly for retrieval, diff cleanly in git, and be
readable by a human deciding whether to merge it.

---

## The record

```
### <ID> · <one-line claim>

- **type:** DECISION | FACT | METRIC | PLAYBOOK | PREFERENCE | FAILURE
- **venture:** trading | ecommerce | ops
- **recorded:** YYYY-MM-DD
- **confidence:** high | medium | low
- **evidence:** where this came from
- **supersedes:** <ID> (omit if none)

<Body. Two to six sentences. What is true, why it matters, and what would
change it. For a FAILURE, the last line is always the rule it produced.>
```

**IDs** are `<TYPE>-<NNN>`, monotonic within type: `DEC-004`, `MET-011`, `FAIL-002`. Never
reuse an ID, never renumber. A superseded record is *edited in place* to add
`**superseded-by:** <ID>` and is left where it is — the reasoning that produced a decision
stays valuable after the decision changes, and deleting it destroys the audit trail.

---

## Types

| Type | For | Example |
|---|---|---|
| `DECISION` | A choice made, with its reasoning and its reversal condition | "Launching 3 SKUs not 5" |
| `FACT` | An observed truth about the business | "Supplier X quotes 6-week lead times" |
| `METRIC` | A measured number with an as-of date | "Blended CAC £71 as of 2026-07-12" |
| `PLAYBOOK` | A procedure that worked and should be repeated | "How the weekly trading review runs" |
| `PREFERENCE` | How the operator wants things done | "Wants numbers in tables, not prose" |
| `FAILURE` | Something that went wrong, plus the rule it produced | "Quoted stale CAC; now always check METRIC first" |

---

## Write rules

**Record when durable and non-obvious.** A decision and its reasoning. A measured number. A
procedure that worked. A stated preference. A failure and its rule.

**Do not record**: restatements of documents already indexed, one-off arithmetic,
speculation, or anything inferred rather than observed. Memory that contains everything is
memory that retrieves nothing — every low-value record dilutes the ones that matter.

**One claim per record.** If it needs "and", it is two records.

**Falsifiable.** "CAC is high" is not a record. "Blended CAC £71 over 340 orders,
2026-07-12" is.

**Dated at the source.** Every METRIC carries its as-of date in the body, not just in
`recorded`. A number without a date is a number that will be wrong later and nobody will
know when it went wrong.

---

## Supersession

Newer beats older, always, and it is stated rather than silent. When a record replaces
another:

1. New record gets `**supersedes:** <old-ID>`.
2. Old record gets `**superseded-by:** <new-ID>` added, and stays in the file.
3. The agent, on retrieving both, uses the newer **and says which it is overriding**.

This is what stops the "planning number vs actual number" failure that kills financial
models — the £62 planning CAC and the measured CAC are both true, of different things, and
the system has to know which one it is holding.

---

## Confidence

| Level | Means |
|---|---|
| `high` | Measured, or stated directly by the operator |
| `medium` | Single source, or a small sample |
| `low` | Provisional. Reconfirm before acting on it |

`low` records are still worth keeping — they are hypotheses with a timestamp, and knowing
what you suspected in July is useful in October. But the agent must flag confidence when
it uses one.

---

## Review gate

**No record enters memory without a human merging it.** The agent proposes records via its
`learning` block; n8n batches them into a weekly pull request; you merge or you don't.

The friction is deliberate. An agent that writes freely to its own memory eventually
learns something false, retrieves it, acts on it, and records the confirmation. The gate
is the only reliable interruption of that loop, and a weekly five-minute PR review is a
low price for it.

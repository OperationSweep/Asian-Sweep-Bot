# Decision log

Append-only. A decision that gets reversed is **superseded, not deleted** — the reasoning
that produced it stays valuable, and knowing why you once believed the opposite is often
the most useful thing in the file.

Each record answers three questions: what was decided, why, and **what would reverse it**.
That third one is the one people skip, and skipping it is how a decision quietly becomes an
assumption nobody remembers making.

---

### DEC-001 · Git is the source of truth for the agent; Studio is a deploy target

- **type:** DECISION
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** agent design

Instructions, memory, tool policy and evals live in this repository. `deploy.py` pushes to
Mistral. The console is never edited directly.

**Why:** eleven unmaintained console agents demonstrated the alternative. Without version
control there is no diff, no review, no rollback, and "learning" degenerates into retyping
the prompt from memory.

**Reverses if:** the Mistral API stops supporting programmatic agent management, or a
console-only feature becomes load-bearing.

---

### DEC-002 · Memory is retrieved by default, resident only by exception

- **type:** DECISION
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** agent design

Learned material goes into the Library and is retrieved on demand. The system prompt holds
only identity, policy and protocol. Promotion into the prompt requires an eval showing
retrieval alone is insufficient.

**Why:** resident tokens are paid on every turn and compete for attention with the actual
task. The common failure is a system prompt that accretes to 4k tokens of trivia and
degrades quality invisibly — no error, just worse answers.

**Reverses if:** retrieval measurably fails on high-frequency facts. Fix retrieval first;
promote only when that fails.

---

### DEC-003 · Every memory write passes a human review gate

- **type:** DECISION
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** agent design; `SCHEMA.md`

Agent-proposed records batch into a weekly pull request. Nothing enters memory unmerged.

**Why:** self-writing memory has a specific failure mode — the agent learns something
false, retrieves it, acts on it, and records the outcome as confirmation. There is no
internal check that catches this because every step is locally consistent. A human gate is
the only reliable interruption.

**Reverses if:** volume makes weekly review impractical. The correct response then is
auto-merging *only* `METRIC` records from trusted tool output, never `DECISION`, `FACT` or
`PLAYBOOK`.

---

### DEC-004 · Bundles and subscription are the business model

- **type:** DECISION
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `07-unit-economics.md`, `13-cac-pressure-test.md`

Foundation Stack (£64.99) is the default offer. Single-SKU purchase is a fallback, never
the promoted path.

**Why:** `[DERIVED]` no single-unit order covers CAC. Best single-unit contribution is
£20.23 against a best-case £38 CAC and a base case of £62. Bundle mix 30% → 70% lifts
contribution per order ~70% at zero extra ad spend.

**Reverses if:** measured bundle conversion runs so far below single-SKU that blended
contribution per *visitor* inverts. Measure per visitor, not per order — per-order figures
flatter bundles and will confirm this decision whether or not it is right.

---

### DEC-005 · Self-funding ad ramp, capped at 130% of trailing contribution

- **type:** DECISION
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `09-financial-model.md`, `11-risks-and-decision.md`

Ad spend never exceeds 130% of trailing 30-day contribution.

**Why:** peak working capital at full speed is ~£80k, 3–8× what the £25k commitment
supports. The cap converts a solvency risk into a timeline risk — 18–24 months instead of
insolvency. Slower is survivable; broke is not.

**Reverses if:** external funding lands, or a validated channel shows LTV:CAC durably
above 3:1 with sub-60-day payback. **Both conditions, not either.**

---

### DEC-006 · Build for an asset, not an income

- **type:** DECISION
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `01-market-analysis.md`, `11-risks-and-decision.md`

Optimise for retention, subscription base and brand equity over near-term owner earnings.

**Why:** `[FACT]` Huel makes 7.6% net at £254m revenue; £1m revenue produces ~£58k EBITDA.
Comparable exits: Huel to Danone at ~€1bn (~3.9× revenue), AG1 ~$600m on effectively one
SKU, Applied Nutrition listed at £107m. A high-retention subscription brand is worth far
more sold than milked. **If the goal is monthly income, this is the wrong business** — and
that is a live question worth re-asking, not a settled one.

**Reverses if:** the operator's objective changes to near-term cash. Then the entire plan
needs rebuilding, not adjusting.

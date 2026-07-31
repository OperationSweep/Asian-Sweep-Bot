# Failures

The highest-value file here. Every record is something that went wrong plus **the rule it
produced** — a failure without a rule is just a bad memory, and the rule is the entire
point.

Records seeded from failures the research corpus explicitly identified and corrected. As
the agent operates, its own failures join them; a `FAILURE` record about the agent's own
mistake is the single most useful thing it can write.

---

### FAIL-001 · The original business model was arithmetically loss-making

- **type:** FAILURE
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `README.md` finding 1, `07-unit-economics.md`

The brief — faceless social, 50 products, single-product selling — could not work at any
execution quality. `[DERIVED]` no single-unit order in the Top 10 covers even a best-case
£38 CAC. Best contribution £20.23, worst £5.21.

It failed **arithmetically**, not operationally, and no amount of better marketing would
have rescued it. It survived until someone did the unit economics.

**Rule:** run unit economics before evaluating any go-to-market idea. If contribution per
order does not exceed CAC, the idea is dead regardless of how good the plan sounds.
Check the arithmetic first, then the strategy.

---

### FAIL-002 · The first CAC model contained a learning-phase contradiction

- **type:** FAILURE
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `13-cac-pressure-test.md`

The original financial model assumed an ad-spend ramp incompatible with its own
learning-phase assumptions — the ramp required volume the learning phase could not
produce. Caught only by a deliberate bottom-up pressure test, which also moved base CAC
from £55 to £62 and added missing seasonality.

**Rule:** a model that is internally consistent is not thereby correct. Pressure-test the
two or three assumptions carrying the most weight by rebuilding them from the bottom up,
independently of the model that uses them.

---

### FAIL-003 · Product-level revenue does not exist as public data

- **type:** FAILURE
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `02-product-database.md`, `README.md` critical data rule

The standard failure in this category is presenting company-wide or segment revenue as
revenue from a single supplement. Public companies report at group or segment level. The
one derivable brand-level figure in the whole investigation was Optimum Nutrition — only
because Glanbia disclosed it as 75% of Performance Nutrition revenue.

**Rule:** when product-level revenue or margin is requested, the answer is `[NOT PUBLIC]`
unless a company has explicitly disclosed the attribution. Never dress segment revenue as
product revenue. `[NOT PUBLIC]` is a complete answer.

---

### FAIL-004 · Global market figures produce false confidence

- **type:** FAILURE
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `01-market-analysis.md`

"$200bn global supplement market" is true and commercially useless for a UK DTC launch.
The number that governs is £1.5bn growing 1.0%. The global figure implies a rising tide;
the UK figure correctly says every pound must be taken from an incumbent.

**Rule:** always answer with the *addressable* market for the actual jurisdiction and
channel. Global figures are quoted only when explicitly asked for, and always alongside
the addressable one.

---

### FAIL-005 · Memory was seeded from a stale branch and called the bot "live"

- **type:** FAILURE
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** agent build; caught by diffing the working branch against `origin/main`

The first draft of this memory described the Asian Sweep Bot as *"live algorithmic FX —
capital at risk today"*, with `confidence: high` and `config.py` cited as evidence. It was
read from a branch whose base did not include main's scaffold rebuild. On main the bot runs
`DRY_RUN = True` with every `order_send` gated behind that flag, and the README states it
is not cleared for live deployment.

The record was internally consistent, correctly cited, and wrong. Nothing in the writing
process could have caught it — the citation was real, it just pointed at a stale file. It
was caught only by fetching `origin/main` and diffing, which happened for an unrelated
reason.

Note what would have followed: the agent would have answered trading questions in a live
frame, treated simulated results as performance, and recorded those answers as memory.
Every downstream step would have been locally consistent too.

**Rule:** before recording any `FACT` sourced from a repository file, confirm the file is
current on the default branch — not merely present in the working tree. A citation proves
where a claim came from, never that it is still true. When a `FACT` is about deployment
status, safety flags or anything gating real money, re-read the source at the time of use
rather than trusting the record.

---

## Template for the agent's own failures

When the agent gets something wrong, the record looks like this:

```
### FAIL-0NN · <what went wrong, in one line>

- **type:** FAILURE
- **venture:** trading | ecommerce | ops
- **recorded:** YYYY-MM-DD
- **confidence:** high
- **evidence:** conversation of <date>; corrected by operator

<What was claimed or done. What was actually true. How it was caught —
and whether it would have been caught if nobody had checked.>

**Rule:** <the specific, checkable behaviour that prevents recurrence>
```

A rule must be **checkable**. "Be more careful with numbers" prevents nothing. "Before
quoting CAC, search memory for a `METRIC` record superseding the planning figure" is a rule
that can actually fire.

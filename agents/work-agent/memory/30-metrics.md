# Metrics

Measured numbers with as-of dates. **These supersede planning figures in the research
corpus.** When the agent retrieves both a plan number and a measured number, the measured
one wins and the agent says which it is overriding.

A number without a date is a number that will be wrong later with nobody able to say when
it went wrong. Every record here carries its date in the body, not only in `recorded`.

---

### MET-001 · Planning CAC baseline — £62

- **type:** METRIC
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** medium
- **evidence:** `13-cac-pressure-test.md`

`[ESTIMATE]` **£62 blended CAC**, revised upward from £55 in the original model following
the bottom-up rebuild. Category benchmark: supplements carry the highest CAC in DTC at
~$89 ≈ £70 `[FACT]`.

**This is a planning assumption, not a measurement.** It is here so the agent has a
baseline to compare against, and it must be superseded by a real blended CAC as soon as
one exists. Until then, every use of it is labelled `[ESTIMATE]`.

---

### MET-002 · TikTok Shop affiliate is first-order profitable; paid social is not

- **type:** METRIC
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** medium
- **evidence:** `13-cac-pressure-test.md`

`[DERIVED]` At the modelled commission and AOV, TikTok Shop affiliate covers its
acquisition cost on the **first** order. Paid social does not, and requires the second or
third order to break even — which is what makes retention structural rather than
aspirational.

Materially changes channel sequencing: affiliate before paid. Reconfirm against real
orders before scaling spend behind it.

---

### MET-003 · UK online supplement channel — £1.5bn, +1.0%

- **type:** METRIC
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** IBISWorld, via `01-market-analysis.md`

`[FACT]` **£1.5bn, +1.0% for 2025-26.** There is no rising tide; every pound is taken from
an incumbent.

The agent never quotes global "$200bn supplement market" figures for this venture. They are
true and commercially useless, and using them produces optimism that the £1.5bn figure
correctly refuses.

---

### MET-004 · Industry margin structure

- **type:** METRIC
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** company filings, via `01-market-analysis.md`

`[FACT]` Huel: **7.6% net margin at £254m revenue.** Applied Nutrition: 46.7% gross margin
*with its own factory*. Glanbia Performance Nutrition: EBITDA margin **fell 380bps** on
whey inflation.

`[DERIVED]` **£1m revenue → ~£58k EBITDA.** The agent uses this whenever a revenue target
is discussed, because revenue targets in this industry are routinely mistaken for income.

---

### MET-005 · Creatine category growth — 26.2% CAGR

- **type:** METRIC
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `01-market-analysis.md`

`[FACT]` **26.2% global CAGR, 28.3% US** — the fastest of any category researched. COGS
£3–£4, register-authorised health claim available, audience broadening beyond gym men to
women, over-45s and cognitive/healthy-ageing users.

This is the single strongest number in the entire investigation and the reason creatine is
the hero SKU.

---

### MET-006 · Peak working capital — ~£80k

- **type:** METRIC
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** medium
- **evidence:** `09-financial-model.md`

`[DERIVED]` ~**£80,000** peak working capital if the plan runs at full speed — 3–8× typical
founder budgeting, and 3.2× the £25k committed. Mitigated by the self-funding ramp
(DEC-005), which trades speed for solvency.

The agent tracks actual cash position against this and **warns before the trajectory
crosses it**, not after. A warning issued at the crossing point is a warning issued too
late to act on.

---

## Awaiting first measurement

The agent should notice these gaps and ask for them rather than substituting planning
figures. Each one, once measured, supersedes an `[ESTIMATE]` above.

| Metric | Supersedes | Status |
|---|---|---|
| Actual blended CAC | MET-001 | `[NOT MEASURED]` |
| Actual COGS per SKU (from RFQ) | CHR-006 estimates | `[NOT MEASURED]` |
| Subscription retention M1 / M3 / M6 | LTV model in `07` | `[NOT MEASURED]` |
| Bundle mix (% of orders) | DEC-004 assumption | `[NOT MEASURED]` |
| Dry-run signal count and skip-reason breakdown | — | `[NOT MEASURED]` |
| Spec-conformance rate (observed vs `strategy_spec.md`) | — | `[NOT MEASURED]` |
| Content engine conversion (videos → orders) | `10-launch-and-content.md` | `[NOT MEASURED]` |

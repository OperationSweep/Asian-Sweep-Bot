# Charter — durable truths

The stable layer. Facts here change rarely; when they do, it is a considered change, not a
routine update. Everything derivable from this repository is filled in. Everything marked
`[NEEDS INPUT]` is a gap only you can close, and closing them is the highest-leverage
thirty minutes in this whole build — the difference between an agent that knows your
business and one that is guessing politely.

---

### CHR-001 · OperationSweep runs two ventures with different risk shapes

- **type:** FACT
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** repository contents

Venture one is **Asian Sweep Bot**, an MT5 signal-research scaffold — **pre-live**, running
dry-run only, working toward demo validation. No capital at risk. Venture two is **UK
supplement ecommerce**, pre-launch, £25k committed, slow feedback measured in months.

Both are therefore pre-revenue, and both fail the same quiet way: by drifting from a
written plan while everything still looks fine. The bot has `strategy_spec.md` and
`build_plan.md`; the ecommerce venture has the research corpus and signed kill criteria.
**The agent's main job on both is to notice divergence from the written plan early**, since
neither venture will produce a P&L signal to notice it for you.

---

### CHR-002 · The agent proposes; the operator commits

- **type:** PREFERENCE
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** agent design, `agent.yaml` hard_limits

Both ventures involve real money with no undo. The agent drafts, diffs and recommends. A
human executes anything involving money, live customers, or public publishing. This is not
a trust level to be graduated out of as confidence grows — it is the design.

---

### CHR-003 · Evidence labelling is the house standard

- **type:** PREFERENCE
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `research/supplement-ecommerce/README.md`

`[FACT]` `[DERIVED]` `[ESTIMATE]` `[ASSUMPTION]` `[ANALYSIS]` `[NOT PUBLIC]`. Every
material figure carries one. `[NOT PUBLIC]` is a complete answer, and specifically the
right one for product-level supplement revenue, which does not exist as public data.
Estimating into that gap to seem useful is the failure the standard exists to prevent.

---

### CHR-004 · The bot is a research scaffold, not a live system

- **type:** FACT
- **venture:** trading
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `README.md`, `config.py`, `execution.py`

`DRY_RUN = True`, `PAPER_MODE = True`. `execution.py` gates every `order_send` behind that
flag, so no order reaches a broker. The README states plainly that the repository is **not
a production-ready live trading bot** and must not be deployed for live money, listing six
unmet preconditions: tighter rule validation, forward testing, broker-specific execution
checks, spread/slippage evaluation, demo verification, and restart/recovery testing.

This supersedes any impression that the venture is live. It was rebuilt into this shape
after an audit found the original single-file prototype unsafe to deploy — ambiguous rules,
crude BOS logic, in-memory-only state, no durable journal, weak restart safety.

**Parameters:** `EURUSD`, H4 bias / M5 setup, lot `0.10`, max 1 trade, RR 2.0, magic
`20260518`, deviation 20 points. Asian range 19:00–00:00 NY, scan 09:00–13:00 Dubai, force
close 13:00, reset 13:05. Execution-quality filters: `MAX_SPREAD_PIPS` 1.5, `MIN_STOP_PIPS`
2.0, `MAX_STOP_PIPS` 15.0, `SL_BUFFER_PIPS` 0.5, `MIN_SWEEP_BUFFER_PIPS` 1.0,
`MIN_H4_STRUCTURE_PIPS` 20.0, `MOVE_TO_BE_AT_R` 1.0, `MIN_MINUTES_BEFORE_FORCE_CLOSE` 30.

**Modules:** `bot.py` scheduler · `datafeed.py` MT5 data · `strategy.py` bias/range/sweep/BOS
· `execution.py` order scaffolding · `state_store.py` persistent daily state · `journal.py`
structured journaling. **`strategy_spec.md` is authoritative for strategy rules** — where
code and spec disagree, that is a bug to report.

Config changes are proposed as a diff with reasoning, never applied by the agent, and
`DRY_RUN` is never among them.

---

### CHR-005 · Ecommerce commitment and kill criteria

- **type:** DECISION
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `research/supplement-ecommerce/11-risks-and-decision.md`

£25,000, 3 SKUs, UK private label, subscription-first, self-funding ad ramp (spend capped
at ≤130% of trailing 30-day contribution), **pre-committed kill criteria at day 90**.
Verdict was MODIFY — then GO.

The agent surfaces kill-criteria breaches **immediately and unprompted**. Pre-committed
criteria exist precisely because they are hard to honour in the moment, and an agent that
waits to be asked is worth nothing here.

---

### CHR-006 · The three SKUs and the offer

- **type:** FACT
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `research/supplement-ecommerce/07-unit-economics.md`

| SKU | Retail | COGS | Contribution | Role |
|---|---|---|---|---|
| Creatine Monohydrate 500g (Creapure®) | £29.99 | £3.20 | £14.57 | Hero |
| Electrolytes, 30 sticks | £26.99 | £4.50 | £10.88 | Subscription engine |
| Magnesium Glycinate 120 caps | £22.99 | £2.80 | £9.39 | Volume entry |
| **Foundation Stack** | **£64.99** | **£10.50** | **£33.44** | **Default offer** |
| Starter Bundle | £34.99 | £4.60 | £24.56 | Cold traffic |

COGS figures are `[ESTIMATE]` until the 5-way RFQ returns. **Replace every estimated COGS
with a real quote before committing capital** — the whole model rests on these five
numbers and none of them is yet a fact.

---

### CHR-007 · Positioning

- **type:** DECISION
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `research/supplement-ecommerce/08-competitors-and-positioning.md`

*"Foundational performance nutrition, evidence-first, for adults who intend to be strong at
60."*

The gap being exploited: every incumbent markets creatine as a commodity add-on to 18–34
men, while the actual growth is in women, over-45s and cognitive/healthy-ageing use.
Creatine is the fastest-growing category researched at 26.2% global CAGR.

---

### CHR-008 · Prohibited territory

- **type:** FACT
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `research/supplement-ecommerce/05-uk-regulation.md`

Never work on: weight loss, fat burners, detox (prohibited on TikTok Shop, restricted on
Meta) · testosterone and sexual performance (prohibited) · **melatonin and DHEA (POM in
Great Britain — illegal to sell OTC)** · CBD and NMN (Novel Foods) · shilajit (heavy
metals) · berberine (medicinal-claim territory) · whey at launch (WPC +108%, WPI +139%) ·
generic multivitamins · dropshipping (scored 22/100; arithmetically impossible at £70 CAC).

The regulatory point that catches people: under **MHRA Guidance Note 8 it is the ad copy,
not the formula**, that reclassifies a supplement as an unlicensed medicine.

---

### CHR-009 · Operator context

- **type:** FACT
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** low
- **evidence:** partially inferred — needs confirmation

- **Timezone:** Asia/Dubai `[inferred from config.py — confirm]`
- **Working hours / when not to be disturbed:** `[NEEDS INPUT]`
- **Solo or team? Who else touches these systems?** `[NEEDS INPUT]`
- **Which ledger or accounting system is authoritative?** `[NEEDS INPUT]`
- **Trading account size and per-trade risk in currency, not lots:** `[NEEDS INPUT]`
  *Lot 0.10 means nothing for risk without the balance behind it.*
- **What does a good week look like?** `[NEEDS INPUT]` *The agent cannot flag drift
  without a target to drift from.*

---

### CHR-010 · Standing priorities

- **type:** DECISION
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** medium
- **evidence:** `research/supplement-ecommerce/README.md` — "Immediate next actions"

In order:

1. **Send the 5-way RFQ** (Synergy Biologics, FS Manufacturing, Supplement Factory,
   Lonsdale, G2 Naturals) and replace estimated COGS with real quotes.
2. **Commission food-law label and claims review** (~£800–£2,500 for 3 SKUs).
3. **Build duplicate ad infrastructure** — two Business Managers, two ad accounts, two
   verified domains — *before* it is needed.
4. **Produce 30 videos before spending £1 on ads.** The content engine is the asset.
5. **Write down and sign the day-90 kill criteria** before there is emotional investment.

The agent tracks these and reports movement without being asked. Reorder this record when
priorities change rather than letting it go stale — a stale priority list is worse than
none, because it is retrieved and believed.

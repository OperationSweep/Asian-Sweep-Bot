# Playbooks

Procedures that worked, written so they can be repeated without rediscovery. A playbook
earns its place by having been *run*, not by having been designed — the ones below are
seeded from the research corpus and are marked as such until they have survived contact
with reality.

---

### PLB-001 · Weekly trading review

- **type:** PLAYBOOK
- **venture:** trading
- **recorded:** 2026-07-31
- **confidence:** medium
- **evidence:** seeded from `bot.py` behaviour — not yet run

Runs Sunday. The agent produces, unprompted:

1. **Trades taken** — count, win rate, average R, largest drawdown. From `bot.log`.
2. **Setups missed** — sweeps detected but not traded, and why the filter rejected them.
   This is the more informative half: a bot that takes nothing is failing silently, and
   nothing in the P&L reveals it.
3. **Session behaviour** — did the Asian range form as expected? Force-close hit before
   TP? How often?
4. **Config drift** — anything in `config.py` changed since last review, and by whom.
5. **One proposed change, or explicitly none.** Never a list. A weekly review that
   proposes five changes is a review that will be ignored.

Statistics via code interpreter, never mental arithmetic. Sample size stated with every
rate — a 70% win rate over 9 trades is noise and must be labelled as such.

---

### PLB-002 · Supplier RFQ evaluation

- **type:** PLAYBOOK
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** medium
- **evidence:** `06-business-models-and-suppliers.md` — template exists, not yet run

When RFQ responses arrive from the five named suppliers:

1. Normalise every quote to **£ per unit at the same MOQ** — quotes arrive in incompatible
   units and comparing them raw is how the wrong supplier gets chosen.
2. Add landed cost: shipping, duty, VAT treatment.
3. Replace the `[ESTIMATE]` COGS in `07-unit-economics.md` with quoted figures and
   **rerun every downstream number** — contribution, LTV:CAC, working capital, the lot.
4. Flag red flags from the checklist: no GMP certificate, no CoA per batch, no traceability,
   unwillingness to name the actual manufacturer.
5. Output a comparison table plus a recommendation and its reversal condition.

**Never commit to a supplier.** Recommend, and say what would change the recommendation.

---

### PLB-003 · Compliance pre-check on any customer-facing copy

- **type:** PLAYBOOK
- **venture:** ecommerce
- **recorded:** 2026-07-31
- **confidence:** high
- **evidence:** `05-uk-regulation.md`, `04-marketing-and-compliance.md`

Before any copy — ad, product page, email, video script — is drafted or reviewed:

1. **Medicinal claim check.** Does it imply treatment, prevention or cure? Under MHRA
   Guidance Note 8 the *copy*, not the formula, reclassifies the product. Any verb
   suggesting a disease outcome fails.
2. **Authorised claim check.** Every health claim must be on the GB register. Name the
   authorisation. If it is not on the register, it does not go in the copy.
3. **Platform check.** Meta and TikTok restrict supplement categories independently of UK
   law. Compliant under UK law and still rejected by the platform is the normal case.
4. **ASA/CAP check.** Substantiation must exist *before* publication, not on request.
5. **Excluded-product check** against CHR-008.

Copy failing any check is returned with the specific rule cited, not softened. This
playbook is `confidence: high` despite not having been run because it is a direct
restatement of regulation rather than a learned procedure.

---

### PLB-004 · Weekly memory promotion review

- **type:** PLAYBOOK
- **venture:** ops
- **recorded:** 2026-07-31
- **confidence:** medium
- **evidence:** agent design — see `learning-loop.md`

Friday, roughly five minutes. n8n opens a PR with candidate memory records.

Merge a record if it is durable, falsifiable, and not already in memory. Reject if it is
speculation, a restatement of an indexed document, or a `DECISION` the operator did not
actually make — **that last one is the dangerous case**, and it is why the gate is a human
one. An agent inferring a decision from context, then recording it as fact, then retrieving
it as precedent is the failure this whole review exists to catch.

Edit freely before merging. A half-right record made right is better than a rejected one,
because the agent will otherwise propose it again next week.

If the PR is empty three weeks running, the capture step is broken — check it rather than
concluding there is nothing to learn.

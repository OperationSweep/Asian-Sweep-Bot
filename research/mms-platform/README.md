# MMS / Enterprise Operations Platform — Independent Review, Architecture Critique and Pricing

An adversarial review of the MMS proposal in `00-original-proposal.md`, as §36 of that document requested, plus a costed answer to "what should I charge."

## Contents

| File | What it covers |
|---|---|
| `00-original-proposal.md` | The original proposal, unedited, for reference |
| `01-verdict-and-critique.md` | What is strong, what is wrong, and the one data-model decision that would sink the project |
| `02-what-is-missing.md` | Power-generation domain, PTW, statutory duties, OT/IT security boundary, NIS, business continuity, KPI integrity |
| `03-architecture-changes.md` | Modular monolith, state table not workflow engine, outbox not broker, asset model, permissions, AI governance, what to delete |
| `04-build-vs-buy.md` | Market pricing, honest 3-year TCO, and the option the proposal never considered |
| `05-scope-and-delivery-plan.md` | The honest answer on "perfection", the true MVP, a 21-week plan, 18 acceptance tests |
| `06-pricing.md` | **The pricing answer** — IP prerequisite, bespoke project pricing, product/SaaS pricing, the clause worth more than the fee |
| `07-answers-to-the-28-questions.md` | Direct answers to all 28 questions in §36 |
| `08-sources.md` | Sources, with quality caveats |

## The three answers in short

**Is the idea good?** The strategy is right and one feature in it — cross-departmental delay attribution (§10) — is genuinely differentiated and worth building. Everything else in the proposal is commodity. The architecture is roughly 30% over-engineered and missing most of the power-generation domain: no preventive maintenance, no statutory inspections, no permit timestamps, no OT/IT security position, no business continuity, and — the biggest gap — no plan for the human beings whose honest button-pressing the entire KPI engine depends on.

**Can it be done to perfection?** No, by anyone, and aiming at perfection is the specific failure mode that kills this category of project. What is achievable: the eight irreversible decisions made correctly, production quality throughout, one department live in 12–16 weeks, and a fast enough iteration loop that being wrong about the other twenty-six decisions costs days rather than quarters.

**What to charge?**

| | |
|---|---|
| Paid discovery & blueprint | **£15,000** fixed, 3 weeks, creditable against Phase 1 |
| Phase 1 delivery | **£110,000** fixed (defensible range £95k–£140k), milestone-paid |
| Data migration | **£8,000–£20,000**, scoped after discovery — never fixed-price before seeing the spreadsheets |
| Security assurance | **£8,000–£20,000** |
| Support & evolution | **£22,000–£30,000/year** (£2,000/mo + 2 dev days/mo) |
| Later modules | **£60,000–£150,000** each |
| Fallback option | Buy the CMMS, build the intelligence layer: **£40,000–£70,000** |
| As a product instead | Site platform fee **£1,500–£4,000/mo** + **£30–£60**/maintenance seat/mo + **free unlimited reporters** + **£15,000–£60,000** onboarding |

**Read `06-pricing.md` §6.0 before anything else.** If you are employed by the power-generation company, s.11(2) of the Copyright, Designs and Patents Act 1988 means your employer owns the copyright in software you write in the course of your employment by default — and most employment contracts widen that further. Settle the IP position in writing before discovery, or the rest of the numbers are academic.

## The one thing to take away

The delay-attribution engine is the product. Everything else — the Warehouse business case, the Procurement business case, the AI cost analysis — is derived from it. And its accuracy depends entirely on a technician in gloves, in the rain, honestly coding *why* they stopped work, at the moment they stop. Get that interaction down to two taps and make sure nobody is punished for what it reveals in year one, and the whole roadmap works. Get it wrong and you have built a ticketing system with very good charts.

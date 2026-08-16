# Phase 6 — What To Charge

Two different questions are hiding inside "how much should I charge for this service and platform":

- **Scenario A** — you are delivering this to one power-generation client as a bespoke build. Project pricing.
- **Scenario B** — you are building a product and selling it to many industrial clients. Subscription pricing.

They have different answers and different economics. Both are below. But there is a prerequisite that outranks both.

---

## 6.0 Before any number: who owns it?

**`[ANALYSIS]` If you are employed by the power-generation company, the pricing question may already be settled against you, and you need to resolve this in writing before you write a line of code.**

`[FACT]` Under section 11(2) of the Copyright, Designs and Patents Act 1988, where a literary work — which includes software — is made by an employee in the course of their employment, **the employer is the first owner of the copyright**, subject to any agreement to the contrary.

Consequences:

- You cannot licence to your employer software they already own. If you build this as part of your job, there is nothing to charge for.
- "I built it at home, at the weekend" is a weaker defence than it feels. Where the work is in the employer's field of business, relates to your role, and was informed by knowledge from it, "in the course of employment" is argued broadly — and most UK employment contracts add an express IP assignment clause that is wider than the statutory default, often covering work outside hours in related fields.
- `[ANALYSIS]` This is not a technicality that gets waved through. The moment the system is valuable, someone in legal will ask the question, and the worst possible time to discover the answer is after two years of unpaid evenings.

**Your realistic routes:**

| Route | What it means | Realistic pricing outcome |
|---|---|---|
| **Internal project** | Build it as an employee, on work time, with a proper budget | You cannot charge. Value is captured through role, scope, budget authority and career. Legitimate and often the right call — but be clear-eyed that you are not going to be paid a licence fee. |
| **Negotiated carve-out** | Written agreement, signed before you start, that you retain ownership of the underlying platform and grant the company a perpetual licence | Hard to obtain, occasionally granted, and worth more than any fee in this document. Needs a solicitor, not a template. |
| **Supplier relationship** | You contract in through your own limited company, or a third party does, with an IP position agreed in the contract | The scenarios below apply directly |

`[ANALYSIS]` **Get this settled first, in writing, before discovery.** Everything below assumes you have a clean position. If you do not, the numbers are academic.

Two related points if you are contracting through your own company:

- **IR35.** A fixed-price, deliverable-based engagement with your own equipment and a right of substitution points towards outside-IR35, but the determination belongs to the client and a large generator will typically be a medium/large business making the assessment. `[ANALYSIS]` Get a written determination before signing; an inside-IR35 outcome changes your net by roughly 20–25% and must be priced in, not discovered later.
- **Insurance and liability.** A supplier to a generator will be asked for professional indemnity cover, commonly `£1m–£5m`. `[ANALYSIS]` And you must cap your liability — typically at fees paid, or a multiple of them, with an explicit exclusion of consequential loss. If a plant incident is ever argued to involve your system and your liability is uncapped, the exposure is unbounded and uninsurable. **Never sign without a cap.**

---

## 6.1 What the market charges — your pricing anchors

`[FACT]` UK contract rates, 2026: median developer day rate **£500** (up from £457 in early 2024); average across all IT roles **£576**. By level, roughly £400–500 junior, £500–600 mid, **£650–900+ senior**, ~£1,200 principal/scarce specialist. Solution architects and specialist AI engineers **£800–£1,200**. Regional agencies charge **£350–£550/day** for a blended team; London firms **£600–£900**. London adds 20–30%, though remote hiring is eroding it.

`[FACT]` UK custom software project costs, 2026: simple internal tools **£10k–£30k**; standard business application **£30k–£80k**; complex platform **£70k–£150k**; enterprise-grade **£150k–£500k+**. A focused custom platform from a regional UK or hybrid UK-offshore agency typically costs **£120k–£300k** for an initial 6–9 month build.

`[FACT]` Ongoing maintenance, monitoring, security patching and iteration typically run **15–25% of build cost per year**.

`[FACT]` Competing CMMS/EAM subscription pricing is tabulated in `04-build-vs-buy.md` §4.1 — mid-market **$16–$85/user/month**, IBM Maximo SaaS Essentials **from ~$3,150/month** for up to 25 users.

---

## 6.2 Cost-based floor for Scenario A

`[ESTIMATE]` Effort for the Phase 1 scope in `05-scope-and-delivery-plan.md`, one senior engineer working AI-assisted:

| Stage | Person-days |
|---|---:|
| Discovery & blueprint | 15 |
| Spine | 15 |
| Work management | 20 |
| Intelligence & data | 15 |
| Hardening | 10 |
| Pilot support (part-time over 6 weeks) | 15 |
| Project management, governance, client meetings | 20 |
| **Total** | **110** |

`[DERIVED]` At £800/day (senior/architect, mid-range): **£88,000**. At £900/day: **£99,000**. Add a subcontracted penetration test and remediation.

`[ANALYSIS]` That is a *floor*, not a price. It assumes no overrun, and fixed-price work must carry a risk contingency — 20–25% is normal for a first engagement with an unfamiliar client and domain. It also ignores that an agency quoting the same scope would be at £150k–£300k per the benchmarks above, which means there is headroom and you should use it.

---

## 6.3 Scenario A — recommended pricing structure

### Stage 0 — Discovery & Blueprint: **£15,000 fixed** (3 weeks)

`[ANALYSIS]` **Never do this free.** Four reasons, and they all matter:

1. It is the highest-value work in the engagement. The eight locked decisions, the asset model against the real tagging standard, the security position and the migration assessment are what make everything afterwards cheap.
2. It is the natural small commitment before the large one. A client who will not spend £15k to find out will not spend £110k to build.
3. Free discovery is priced by the client as worthless, and is where unpaid scope creep begins.
4. It de-risks your own fixed price. You cannot responsibly quote a fixed price for Phase 1 without it — quoting blind is how fixed-price projects lose money.

Deliverables: blueprint, data model, security and hosting position, migration assessment on the actual spreadsheets, hold-reason taxonomy v1 derived from real historical delays, acceptance criteria, **an explicit build-vs-buy recommendation**, and a fixed-price proposal for Phase 1.

`[ANALYSIS]` Offer to credit the £15k against Phase 1 if they proceed within 60 days. It costs you nothing in the case you want, and it removes the last objection.

### Stage 1–5 — Phase 1 delivery: **£110,000 fixed** (headline)

Defensible range **£95,000 – £140,000**, moving on six variables — state all six in the proposal so the client can see what drives the number:

| Variable | Baseline (£110k) | Pushes up |
|---|---|---|
| Sites | 1 | +£12k–£20k per additional site in Phase 1 |
| Named users | ≤ 300 | +£8k above 1,000 |
| Hosting | Cloud | +£10k–£18k for on-premises deployment and handover |
| Identity | Standard OIDC/Entra SSO | +£5k–£10k for legacy or non-standard directory |
| Migration | ≤ 50,000 rows, ≤ 3 source workbooks | see below |
| Integrations | None | +£8k–£25k each (PTW, historian read, ERP) |

Payment schedule — **milestone-based, never monthly**:

| Milestone | % | £ |
|---|---:|---:|
| Contract signature | 25% | £27,500 |
| Stage 1 spine demonstrated | 25% | £27,500 |
| Stage 3 KPI reconciliation gate passed | 25% | £27,500 |
| Security sign-off / pilot start | 15% | £16,500 |
| Pilot acceptance criteria met | 10% | £11,000 |
| | | **£110,000** |

`[ANALYSIS]` Retaining only 10% against final acceptance is deliberate. Adoption criteria (`05` §5.4, items 15–18) depend heavily on client-side behaviour you do not control, so do not put a large share of your fee behind them. Put the large tranches behind gates you *can* control — the spine demo and the KPI reconciliation.

### Priced separately — say so explicitly

| Item | Price | Note |
|---|---|---|
| Data migration | **£8,000 – £20,000** | Scoped after discovery. `[ANALYSIS]` Never fixed-price migration before seeing the spreadsheets — it is the single most reliable source of overrun in this kind of project. |
| Security assurance | **£8,000 – £20,000** | Third-party pen test at cost plus remediation. Pass through the test at cost and be seen to. |
| Additional integrations | **£8,000 – £25,000** each | PTW, historian read, ERP |
| Training delivery beyond train-the-trainer | **£1,200/day** | |
| Change requests outside scope | **£850/day** or fixed-priced per item | |

### Stage 6+ — Support and evolution: **£22,000 – £30,000/year**

`[DERIVED]` 20–27% of build cost, against the `[FACT]` 15–25% industry norm — slightly above midpoint, justified because a single-supplier bespoke system carries higher availability expectations than an agency's shared support desk.

Structure as **£2,000/month base** (hosting oversight, patching, backups, monitoring, incident response to agreed SLA) **+ a bank of 2 development days per month** (rolling, expiring quarterly). `[ANALYSIS]` The development bank is what stops support becoming a grudge purchase — it converts the renewal conversation from "what did we get for that?" into a discussion about what to build next.

Later modules — Warehouse, Call-Off, Procurement — priced separately at **£60,000 – £150,000** each after their own short discovery.

### The three-year story to put in the proposal

| | Your proposal | Mid-market CMMS |
|---|---:|---:|
| Year 1 | £153,000 | £112,000 |
| Year 2 | £26,000 | £62,000 |
| Year 3 | £26,000 | £62,000 |
| **3-year total** | **£205,000** | **£236,000** |
| Year 4 onward | £26,000/yr | £62,000/yr |

`[ANALYSIS]` Present this honestly, including the fact that years 1–3 are roughly a wash. The divergence from year four is real and material, and a client who has been told the truth about years 1–3 will believe you about year four. A client who has been sold a fictional year-one saving will not believe anything else in the document.

### How to frame value without pricing on it

`[VENDOR]` Vendor-published figures put an hour of unplanned power-plant downtime at $50,000–$500,000, and give a worked example of a 500 MW combined-cycle plant at a $70/MWh margin losing ~$35,000 per hour of forced outage. Treat these as vendor content marketing, not evidence — they are published by companies selling maintenance software.

`[ANALYSIS]` Even discounted heavily, the arithmetic is one-sided: if the system removes 40 hours a year of material- and permit-driven delay on production-affecting work, the avoided loss is an order of magnitude above the build cost. **Use this to make £110k feel small. Do not price as a share of it.**

Do not propose gainshare or a percentage of savings. Three reasons: attribution is unprovable and you will not win the argument; it invites a finance scrutiny process you cannot control; and corporate procurement is not built to pay variable sums against contested baselines. `[ANALYSIS]` You will do a lot of work and get paid late, or not at all.

### The smaller option to keep in your pocket

If the budget is not there, `04-build-vs-buy.md` §4.4 — commercial CMMS as system of record, your intelligence layer on top — prices at **£40,000 – £70,000** plus **£10,000–£15,000/year**. `[ANALYSIS]` Have this ready. Walking into a budget objection with a genuine £50k alternative is far stronger than discounting the £110k, because discounting tells the client the first number was invented.

---

## 6.4 Scenario B — pricing the platform as a product

If the goal is a product sold to many industrial clients, the design of the pricing model matters more than the level.

### The structural decision

**`[ANALYSIS]` Do not price purely per user.** Doing so puts your commercial interest in direct conflict with the thing that makes the product work. Delay attribution is only as good as reporting coverage, and reporting coverage means *everyone on site* raises faults. Charging per head taxes exactly the behaviour you need. `[FACT]` The market has already reached this conclusion — Limble includes unlimited requesters on every plan, MaintainX includes unlimited requester users even on the free tier, UpKeep's entry plan includes unlimited request-user licences. Anything less will be uncompetitive on the first page of the comparison.

### Recommended three-part tariff

| Component | Price | Rationale |
|---|---|---|
| **Platform fee per site** | **£1,500 – £4,000/month**, banded by functional-location count (e.g. <2k / 2k–10k / 10k–50k) | Covers unlimited reporters, dashboards, support, the site itself. Revenue that does not collapse when the client freezes headcount. |
| **Maintenance seats** | **£30 – £60/user/month** — technicians, supervisors, planners, engineers who *execute* work | Where value density sits. Benchmarks directly against MaintainX Premium $49 / Fiix Professional $75 / eMaint Professional $85 / Limble $28–69. |
| **Reporter seats** | **Free, unlimited** | Non-negotiable. Market standard, and strategically essential. |
| **Modules** (Warehouse, Procurement, Reliability/AI) | **+20 – 40%** of platform + seat spend, each | Land and expand — the same logic as your §4 roadmap, applied commercially |
| **Onboarding / implementation** | **£15,000 – £60,000**, one-off, banded by site size and migration volume | **Never free.** `[ANALYSIS]` Free implementation attracts customers who will not do the configuration and data work, and those customers churn at renewal and write the reviews. |

`[DERIVED]` **Worked example** — 400-person site, 80 maintenance seats, 6,000 functional locations: £2,500/month platform + (80 × £45) £3,600/month seats = **£6,100/month ≈ £73,000/year**, plus a **£30,000** onboarding fee in year one.

`[ANALYSIS]` That positions you above mid-market list (MaintainX ≈ £45k, Fiix ≈ £69k, eMaint ≈ £78k at 100 seats) and far below Maximo once its implementation multiple is counted. **That is the right slot** — a specialist industrial product with power-generation domain depth, statutory compliance, an on-premises option and the attribution engine. But it is only the right slot if you can *articulate* the specialism in one sentence on a website. If you cannot, you are a more expensive MaintainX and you will lose every deal on price.

### Alternative model worth considering

**Per managed asset**, roughly `£0.80–£2.00` per functional location per month. `[ANALYSIS]` Scales with plant size, aligns with value, and never penalises adoption. Downsides: buyers cannot forecast it, "what counts as an asset" becomes a negotiation in every deal, and it makes you hard to compare — which cuts both ways. Use asset count to set the **platform fee band** rather than as the primary meter. That captures most of the alignment with none of the ambiguity.

### First customers

`[ANALYSIS]` Price design partners at **40–60% off** for the first two or three, in exchange for: reference rights, a written case study with real numbers, named-logo permission, and design-partner access to their maintenance team. Put the **step-up to standard pricing in the original contract**, dated, at renewal. An open-ended founder discount becomes permanent, anchors every subsequent negotiation, and is the most common self-inflicted wound in early vertical SaaS.

### The anti-pattern to avoid

`[ANALYSIS]` Do not sign a first customer on a bespoke "we will build whatever you ask" basis while telling yourself it is a product. That produces a consultancy with one client's assumptions welded into the codebase and no second customer. If the first deal is bespoke — and it probably will be — **say so honestly, price it as Scenario A, and keep the IP position that lets you productise the general parts later.** Which brings us to the last point, which is the most important one in this file.

---

## 6.5 The clause worth more than the fee

`[ANALYSIS]` In the Scenario A contract, the IP terms are worth more than the price. If the client's standard purchase terms apply unamended — and large utilities' standard terms usually assign all IP created under the contract to the customer — then you will have been paid £153,000 to build someone else's product, and Scenario B becomes impossible.

Ask for:

1. **Client receives a perpetual, irrevocable, worldwide, non-exclusive licence** to use, modify and have modified the software for their own business purposes, including affiliates. This gives them everything they actually need.
2. **Supplier retains ownership** of the underlying platform, framework and generic modules, and the unrestricted right to reuse them for other customers.
3. **Client owns their data outright** — all of it, exportable in a documented open format on demand and at termination, with no exit fee.
4. **Client-specific configuration, branding, and anything genuinely bespoke to their plant is theirs.**
5. **Source code escrow** with release on defined insolvency or sustained-failure-to-support triggers.

`[ANALYSIS]` Points 1, 3, 4 and 5 give a risk-averse enterprise buyer everything they are genuinely worried about: they can never be held hostage, they always have their data, and they are covered if you are hit by a bus. Framed that way, this is usually acceptable — it addresses the real concern, which is continuity, not ownership. It is a normal position for a software supplier and an abnormal one for a contractor, so **the framing is: you are a software supplier granting a licence, not a contractor delivering a work product.** Establish that in the first conversation, before anyone sends terms.

**That distinction is the difference between a £153,000 project and a company.** Negotiate it before you discuss price, because once a price is agreed the client has no reason to concede anything else.

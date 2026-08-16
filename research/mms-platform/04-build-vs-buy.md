# Phase 4 — Build vs Buy: The Question §36 Asks and Never Answers

Your §36 asks (Q21) what would make the MMS materially better than buying an existing CMMS/EAM, and (Q22) at what point buying Maximo, SAP or IFS is more sensible. The document never answers either. This file does, including the parts that are uncomfortable.

---

## 4.1 What the market actually charges

`[FACT]` Published/reported pricing, as of 2026. All figures are list; enterprise deals are negotiated below list, and every vendor charges implementation on top.

| Product | Published rate | Notes |
|---|---|---|
| MaintainX | Essential ~**$16**/user/mo; Premium ~**$49**/user/mo; Enterprise custom | Free tier includes unlimited **requester** users |
| Limble | Starter ~**$28–35**/user/mo billed annually (min 2 users); top tier ~**$69**/user/mo; 50+ users custom, reported **$70–90**/user/mo on the richer tiers with multi-year commitment | **Every plan includes unlimited requesters** |
| Fiix | Basic **$45**/user/mo; Professional **$75**/user/mo; Enterprise custom | Free tier limited to 3 users |
| eMaint | Team ~**$69**/user/mo; Professional ~**$85**/user/mo; Enterprise custom | Stronger fit for multi-site governance, SCADA/ERP ties |
| IBM Maximo Application Suite | AppPoints credit pool. SaaS **Essentials from ~$3,150/month** for up to 25 users and one production environment | `[FACT]` Reported that implementation, customisation, infrastructure and partner fees "routinely double or triple first-year spend", that AppPoint pools are commonly oversized by 15–35% because sizing is done on headcount rather than concurrency, and that OpenShift/platform costs add 10–20% not in the original business case |

`[ASSUMPTION]` FX at 1.30 USD/GBP for the conversions below; adjust as needed.

`[DERIVED]` **100 maintenance seats at list:** MaintainX Premium ≈ £45k/yr · Fiix Professional ≈ £69k/yr · eMaint Professional ≈ £78k/yr · Limble mid-tier ≈ £26k–£64k/yr. `[ESTIMATE]` Implementation, configuration, data migration and training typically add **£30k–£80k** in year one for a site of this complexity.

### The finding that damages the build case

`[FACT]` **Several major vendors include unlimited requester (report-only) users at no extra cost** — Limble includes unlimited requesters on every plan; MaintainX includes unlimited requester users even on its free tier; UpKeep's entry plan includes unlimited request-user licences.

`[ANALYSIS]` This matters because "we have 600 staff who need to report faults and per-seat licensing makes that unaffordable" is the most intuitive argument for building, and **it is largely false for this product category.** The vendors have already solved it, because they all discovered the same thing you did: adoption dies if reporting costs money per head. If you were planning to lead the internal business case with licence-cost avoidance, that argument will not survive first contact with a procurement team that reads a pricing page. Do not build the case on it.

---

## 4.2 Three-year total cost, honestly

`[ESTIMATE]` Single site, ~100 maintenance seats, unlimited reporters, cloud-hosted, moderate migration.

| | Buy (mid-market CMMS) | Build (per `06-pricing.md`) |
|---|---:|---:|
| Year 1 implementation / build | £50,000 | £125,000 |
| Year 1 security assurance | included | £14,000 |
| Year 1 data migration | included above | £14,000 |
| Year 1 licence / support | £62,000 | £0 |
| Year 2 | £62,000 | £26,000 |
| Year 3 | £62,000 | £26,000 |
| **3-year total** | **£236,000** | **£205,000** |

`[ANALYSIS]` **Read that honestly: on a three-year horizon, for one site, building is not meaningfully cheaper.** It is roughly a wash — inside the error bars of both estimates. Anyone presenting this as a cost-saving project is going to be caught out, and deservedly.

The build only pulls clearly ahead on a **five-to-seven-year** horizon, and only if support costs stay near 20% and the key-person risk is genuinely managed. Against that, the buy option carries someone else's product roadmap, someone else's security patching, someone else's SOC 2 report, and no dependency on one person's continued availability.

`[ANALYSIS]` **So the build must be justified on capability and strategy, not on cost.** That is a perfectly good justification — it is just a different argument, and it needs to be made explicitly rather than smuggled in.

---

## 4.3 The genuinely strong arguments for building

Four survive scrutiny:

1. **The delay-attribution layer is not well served off the shelf.** Every CMMS has hold reasons. `[ANALYSIS]` What they do not have is the thing §10 describes: waiting time attributed to a *named accountable department*, decomposed per work order, aggregated to a departmental scorecard, and defensible enough to survive a management meeting where two directors disagree. That is a cross-departmental accountability instrument dressed as a maintenance feature, and it is genuinely differentiated.

2. **The multi-module vision is real and coherent.** `[ANALYSIS]` MMS → Warehouse → Call-Off → Procurement on shared identity, assets and events is a real product. Stitching that together from four SaaS products is an integration project that never ends, and buying it as one product means buying SAP or IFS, which is a different order of magnitude of cost and disruption.

3. **Deployment constraints.** `[ANALYSIS]` If the operator restricts cloud hosting or data residency — plausible for a generator under NIS obligations (see `02-what-is-missing.md` §2.2) — a large part of the SaaS market is eliminated at the outset, the remaining vendors charge a premium for on-premises, and the build case strengthens sharply. **Establish this in discovery. It is the single highest-leverage question you can ask,** because a "no cloud" answer changes the whole analysis in your favour.

4. **You may be building a product, not a project.** Discussed in §4.5 below — and given that you asked what to charge, this is probably the real story.

### The arguments that do not survive

- ❌ "Licensing 600 reporters is unaffordable" — false, per §4.1.
- ❌ "Off-the-shelf can't be configured to our process" — usually means nobody has configured it. `[ANALYSIS]` If the site already owns SAP PM or Maximo and nobody uses it, building a second system will produce a second system nobody uses. The problem there is adoption, not software.
- ❌ "We'll save money" — per §4.2, roughly untrue at three years.
- ❌ "We can add AI" — every vendor in the table is shipping AI features funded by revenue you do not have.

---

## 4.4 The option the proposal does not consider, and should

**`[ANALYSIS]` Buy the system of record. Build the intelligence layer on top of it.**

```text
   Commercial CMMS (work orders, assets, PM, mobile, statutory, attachments)
                              │  API / webhooks
                              ▼
   ┌────────────────────────────────────────────────┐
   │  YOUR LAYER — the differentiated 20%           │
   │  · delay attribution + departmental scorecards │
   │  · working-time / shift-calendar KPI engine    │
   │  · cross-department accountability reporting   │
   │  · management intelligence and cost hooks      │
   │  · the future Warehouse / Procurement modules  │
   └────────────────────────────────────────────────┘
```

`[ESTIMATE]` This is roughly **£40k–£70k** to build rather than £125k+, carries no responsibility for mobile apps, offline sync, statutory scheduling, attachments or the security posture of the system of record, and delivers most of the differentiated value.

**Honest assessment of this option:**

- *For:* dramatically lower risk, faster to value, you never maintain a work-order engine, and the security review is far easier because the system of record is a vendor product with existing certifications.
- *Against:* you are dependent on the vendor's API and data model, you cannot control the hold-capture UX — **and hold-capture UX is precisely where the data quality is won or lost** (see `01` §1.2.2) — and you do not own a product you could sell to anyone else.

`[ANALYSIS]` That middle objection is the serious one, and it is close to fatal for the pure version of this option. If the vendor's hold-reason capture is a three-tap dropdown buried in a menu, your attribution layer is analysing bad data no matter how good it is. **Evaluate two or three vendors specifically on hold-reason capture UX and API event granularity before dismissing this route.** That evaluation costs you two days and might save you £100k and a year.

---

## 4.5 Answering §36 Q22 directly: when to buy Maximo, SAP or IFS instead

Buy the tier-one EAM when **any** of these is true:

| Condition | Why it settles the question |
|---|---|
| The company already runs SAP as its ERP and has SAP PM licensed | `[ANALYSIS]` You will lose this argument. The integration story, the existing licence, and the group IT standard beat any technical case you can make. Build the intelligence layer on top of SAP PM instead — same conclusion as §4.4. |
| Multiple sites, thousands of assets, formal reliability engineering function | Tier-one EAM earns its cost at that scale; the reliability, RCM and linear-asset modules are decades deep. |
| The organisation is regulated to a level where "who else runs this software" is part of assurance | A bespoke system with one deployment is a harder assurance conversation than a product half the sector runs. |
| There is no appetite to carry long-term software ownership internally | `[ANALYSIS]` This is the real one. A bespoke platform needs an owner in ten years' time. If nobody in the organisation will accept that accountability, the build will become abandonware regardless of quality — and it will be abandonware that maintenance depends on. |

Buy a **mid-market CMMS** (MaintainX / Limble / eMaint / Fiix) when: one or two sites, the requirement is 80% standard, and the organisation wants it running this quarter.

**Build** when: the delay-attribution capability is genuinely the point rather than a nice-to-have, cloud/hosting constraints rule out the market, the multi-module roadmap is real and funded, **and** there is a named long-term owner.

---

## 4.6 The recommendation

`[ANALYSIS]` **Run a three-week paid discovery that ends with a build-vs-buy recommendation, and be genuinely willing to recommend "buy".**

This sounds like it costs you the project. It does the opposite:

1. It is the highest-credibility thing you can do. A supplier who says "here are three products that might do this for less" and *then* explains why building still wins is trusted on everything afterwards. A supplier who never mentions the alternatives is assumed not to have looked.
2. It is what the client's procurement and audit functions will demand anyway. Doing it yourself, first, means you frame it.
3. The discovery is paid work either way (`06-pricing.md` §6.3).
4. `[ANALYSIS]` If discovery genuinely concludes "buy", you have saved everyone £200k and you are the obvious candidate to run the selection and implementation — which is a smaller but real engagement, delivered with far less risk.

Three questions decide it, and all three are answerable in discovery:

1. **Is cloud hosting permitted?** If no → build case strengthens sharply.
2. **Does the company already own SAP PM, Maximo or an equivalent?** If yes → do not build a second CMMS; build the intelligence layer on top.
3. **Is there a named person who will own this system in five years?** If no → do not build. This one is a veto, and it is a veto regardless of how good the answers to the first two are.

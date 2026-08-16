# Phase 1 — Verdict and Critique of the MMS / Enterprise Operations Platform Proposal

**Evidence labelling used throughout this folder**

| Label | Meaning |
|---|---|
| `[FACT]` | Published by a vendor, regulator, standards body or government source, cited |
| `[DERIVED]` | Calculated by me from `[FACT]` inputs; the arithmetic is shown |
| `[ESTIMATE]` | A defensible estimate with stated reasoning, not a published number |
| `[ASSUMPTION]` | A planning input I have chosen; change it and the conclusion changes |
| `[ANALYSIS]` | My engineering / commercial judgement |
| `[VENDOR]` | Figure originates in vendor content marketing — directionally useful, not evidence |

You asked three questions. Short answers first, then the reasoning.

> **1. What do I think of the idea?**
> The strategy is right, one feature in it is genuinely differentiated and worth building, and the architecture section is about 30% over-engineered and missing the half of the domain that actually decides whether a maintenance system survives contact with a power station.

> **2. Can I do it to perfection?**
> No. Nobody can, "perfection" is the wrong target, and aiming at it is the specific failure mode that kills projects like this. See `05-scope-and-delivery-plan.md` for what I can commit to instead, which is a lot.

> **3. What should you charge?**
> `£110k–£140k` fixed price for a single-site Phase 1, preceded by a paid `£12k–£20k` blueprint, followed by `£22k–£30k/yr` support. If you productise it: platform fee per site plus `£30–£60`/maintenance seat/month. Full model, benchmarks and the one contract clause worth more than the fee are in `06-pricing.md`.

---

## 1.1 What is genuinely good in the proposal

**`[ANALYSIS]` Section 10 — Delay Accountability — is the actual product.** Everything else in the 1,772-line document is commodity functionality available off the shelf. This is not.

The insight that a work order taking 87 hours to close does not mean Maintenance spent 87 hours working, and that the *waiting* is attributable to a named department, is the one idea in the document that changes organisational behaviour rather than just recording it. It reframes the system from "a fault log that makes Maintenance look bad" into "the instrument that proves Maintenance is not the problem." That reframing is also, not coincidentally, what will get technicians to actually use it.

Everything downstream — the Warehouse business case, the Procurement business case, the AI cost analysis in §28 — is derived from this single mechanism. If hold-reason capture works, the whole roadmap works. If it doesn't, you have built a ticketing system with charts.

**`[ANALYSIS]` The land-and-expand sequencing (§4) is strategically correct.** Using MMS-generated evidence to fund the Warehouse project, and Warehouse evidence to fund Procurement, is a genuinely good way to navigate corporate capital approval. It converts an unfundable £2m transformation ask into a sequence of fundable £150k asks, each justified by data the previous phase produced. Keep this. It is the strongest commercial idea in the document.

**`[ANALYSIS]` Treating time and status change as immutable event history (§11, §12) rather than mutable fields is right,** and it is the decision that is most expensive to retrofit. Most homegrown maintenance systems store `status` as a column and lose the ability to compute anything. You have avoided that. Good.

**`[ANALYSIS]` "One enterprise backbone, multiple modules" (§3) is the right principle,** though `03-architecture-changes.md` argues the implementation you have sketched is heavier than it needs to be.

---

## 1.2 The three things that are wrong

### 1.2.1 The blueprint gate (§32) is a waterfall specification phase wearing modern clothing

You propose locking down 34 items before any code is written, including KPI formulas, SLA rules, escalation rules, delay reasons, fault categories, dashboard requirements and acceptance tests.

**`[ANALYSIS]` Roughly 26 of those 34 items cannot be known before real users have run real work orders through the system, and attempting to fix them on paper produces a document everyone signs and nobody follows.** Delay reason taxonomies in particular are always wrong on the first pass — you will discover within three weeks of a pilot that "Awaiting material" needs splitting into "not in stock", "in stock but not found", and "wrong part issued", and that distinction is worth more than the entire rest of the taxonomy.

The correct move is to separate decisions by **cost of reversal**, not by importance:

| Lock hard before coding (expensive to change) | Leave soft and configurable (cheap to change) |
|---|---|
| Identity, authentication, SSO model | Fault categories |
| Tenancy and site scoping model | Delay / hold reasons |
| Asset identification scheme — **functional location vs serialised equipment** (see §3.1) | Priority levels |
| Append-only event log and audit schema | SLA targets and escalation timers |
| Permission model shape (RBAC + scope) | KPI thresholds |
| Work order state machine *as data*, not as code | Dashboard layouts |
| API contract and versioning policy | Notification routing rules |
| Where cost and material hooks attach | Report definitions and exports |

Eight locked decisions, not thirty-four. That is a two-to-three week blueprint, not a three-month one, and it protects exactly the things §33 is right to want protected.

**`[ANALYSIS]` Your §33 principle — "do not let AI agents improvise the enterprise architecture while coding" — is correct and I strongly agree with it.** But the answer to that is a tight architectural spine plus review discipline, not a 34-item pre-approval gate. The gate does not actually prevent improvisation; it just moves the improvisation to the parts of the spec nobody read.

### 1.2.2 There is no adoption or change-management plan, and that is what kills these projects

The document spends approximately 1,700 lines on architecture and zero on the human beings who have to press the buttons.

**`[ANALYSIS]` This is the single biggest gap in the proposal.** Consider how the system looks from a technician's chair:

- Every feature in §10, §11, §12 and §13 is, from their point of view, a **surveillance feature**. Timestamped acknowledgement. Measured response time. Recorded work start. Audit trail of every edit. Departmental performance comparison.
- The delay-accountability engine — the one differentiated feature — depends entirely on technicians accurately coding *why* they stopped work, at the exact moment they stop work, on a phone, in a plant, possibly in PPE, possibly in the rain.
- If they code holds inaccurately or skip them, the KPI engine produces confident, precise, wrong numbers. And confident wrong numbers in a departmental blame context are worse than no numbers.

**`[ANALYSIS]` The proposal also creates a direct incentive to mis-code.** §13.3 lists "Department comparison where appropriate" and §13.4 lists "Compare departmental performance." The moment Maintenance discovers that coding a hold as "Awaiting material" moves blame to Warehouse and coding it as "Awaiting manpower" keeps blame in Maintenance, the data stops describing the plant and starts describing the politics. §12's answer — calculate KPIs from trusted event history — does not help, because the event history is only as honest as the person who pressed the button.

Concrete mitigations that need to be in the design, not bolted on later:

1. **Make hold capture two taps, never a form.** Big buttons, most-common reasons first, ranked by that user's own history. Free text optional and never mandatory. If it takes more than five seconds, it will be done at the end of the shift from memory, and end-of-shift reconstruction destroys the timing data that the whole system exists to collect.
2. **Auto-derive what you can.** If a material request exists and is unfulfilled, the hold reason is inferable — propose it and let the user confirm. Every field you derive is a field that cannot be gamed or forgotten.
3. **For the first two quarters, publish system-level and department-level metrics only. No individual technician league tables.** Individual measurement in month one buys you data quality sabotage that you will never recover from. You can add individual views later once the system is trusted; you cannot remove them once people have learned to defend against them.
4. **Give technicians something back on day one.** Asset history at the point of work, previous fixes for this fault, no more chasing paper. If the only thing the app does is measure them, it will be used exactly as much as it is enforced and no more.
5. **Name and fund a pilot supervisor.** Not a project manager — a respected supervisor in the pilot department whose job for eight weeks is partly this. `[ESTIMATE]` This single role is worth more to the outcome than any two features in the Phase 1 scope.

### 1.2.3 Phase 1 as scoped is a fault-logging system, not a maintenance management system

§5 says "The MMS should not be designed as a basic ticketing system. It should be designed as a Work Management Engine." Agreed. But the Phase 1 scope in §31 contains no preventive maintenance.

**`[ANALYSIS]` A maintenance system with only reactive fault reporting is a fault log.** In a real power station, planned and preventive work is the majority of the maintenance function's workload and effectively all of its statutory exposure. Missing from §31:

- **PM / PPM routines** — calendar-triggered and running-hours-triggered schedules, task lists, PM compliance %. Without this you cannot answer "are we doing the maintenance we said we would," which is the first question any manager or auditor asks.
- **Statutory and compliance inspections** with an evidence trail — pressure systems (PSSR 2000), lifting equipment (LOLER), electrical, insurance-driven inspections. These have legal deadlines. A system that tracks corrective work but not statutory work will be run alongside a spreadsheet, and the spreadsheet will win.
- **Work order types.** Corrective, preventive, statutory, modification and outage work do not share one lifecycle. A statutory inspection has no "fault"; a modification needs engineering approval; an outage job needs a window. One state machine with a `type` discriminator and type-specific required fields, decided now.
- **Defect register with risk-accepted deferrals.** Real plants carry known defects deliberately. If the system has no legitimate way to record "we know, we have assessed it, we are not fixing it until the autumn outage," those items get closed falsely or left open forever, and either way your backlog number becomes fiction.
- **Outage / shutdown planning.** Power generation revolves around planned outage windows. Work orders need to be assignable to an outage, and "deferred to next outage" is one of the most important hold reasons in the entire taxonomy — and it is not in your §10 list.

`[ANALYSIS]` Adding PM, work-order types and a defect register is roughly a 25–35% increase in Phase 1 scope. It is not optional. A CMMS without PM will not be accepted as a CMMS by anyone who has used one.

---

## 1.3 One data-model decision that will cost you the project if you get it wrong

**`[ANALYSIS]` §7 models assets as a single hierarchy of assets. That is the single most common and most expensive mistake in homegrown maintenance systems.**

You need two linked concepts, not one:

- **Functional location** — the *position* in the plant. "Unit 1 → Cooling Water System → CW Pump A." This is permanent. It exists whether or not a pump is currently installed in it.
- **Equipment** — the *physical, serialised item* currently installed at that location. Serial number, manufacturer, the actual casting that gets removed, refurbished, and reinstalled somewhere else eighteen months later.

Why it matters, concretely:

- **Reliability analysis needs the location.** "CW Pump A position has failed four times this year" is the finding that triggers a design review — and it stays true across pump swaps.
- **Warranty, refurbishment and rotable spares need the equipment.** "This specific pump has been rebuilt three times and fails within 400 hours every time" is a different and equally important finding.
- If you conflate them, then the first time a rotable is swapped you either lose the location's failure history or lose the equipment's, and there is no way to reconstruct it afterwards. `[FACT]` Both SAP PM and IBM Maximo separate functional location from equipment; this is settled industry practice, not a preference.
- `[ANALYSIS]` This is also the hook the future Warehouse module needs. Spares attach to *equipment classes*; criticality and stocking policy attach to *locations*. Get it wrong now and the Warehouse module in §24 requires a data migration, not an integration.

A work order should carry **both** references: the functional location where the failure occurred, and the equipment serial installed there at that time. That second part — *at that time* — means installation history must be a dated record, not a current-value field.

Adopt the **ISO 14224** taxonomy for equipment classes and failure modes rather than inventing your own. `[FACT]` ISO 14224 is the international standard for collection and exchange of reliability and maintenance data, defining a nine-level equipment taxonomy and standard failure modes per equipment class; it originated in oil and gas and is widely applied in power generation. Adopting it costs you a week of mapping and buys benchmarkability against the rest of the industry forever. Inventing your own fault categories costs you the same week and buys nothing.

---

## 1.4 Summary scoring of the original proposal

| Area | Verdict |
|---|---|
| Strategic sequencing (MMS → Warehouse → Procurement) | **Strong.** Keep as is. |
| Delay accountability concept (§10) | **Strong.** This is the product. |
| Event history / audit model (§11, §12) | **Strong.** Right call, right time. |
| Shared backbone principle (§6) | **Right principle, heavy implementation.** See `03`. |
| Asset model (§7) | **Needs rework.** Functional location vs equipment. |
| Phase 1 scope (§31) | **Incomplete.** No PM, no statutory, no WO types, no defect register. |
| Workflow engine (§9) | **Over-engineered for Phase 1.** State machine as data, not an engine. |
| Event-driven architecture (§23) | **Over-engineered for Phase 1.** Outbox table, not a broker. |
| AI agent layer (§27) | **Ten agents specified, two worth building, neither in Phase 1.** |
| Notification channels (§19) | **Six channels specified, three needed.** |
| Blueprint gate (§32) | **Wrong shape.** 8 locked decisions, not 34. |
| Change management / adoption | **Absent.** Biggest single gap. |
| Power-generation domain specifics | **Largely absent.** See `02`. |
| Security / OT boundary / regulatory | **Absent.** See `02`. Non-negotiable for this sector. |
| Business continuity | **Absent.** See `02`. |
| Build-vs-buy analysis | **Asked as a question (§36), never answered.** See `04`. |

# Phase 2 — What Is Missing: Power-Generation Domain, Security, and Continuity

The original proposal is architecturally literate and domain-thin. This file covers the things that a power station will raise in the first governance meeting and which, if unanswered, will stop the project regardless of how good the code is.

---

## 2.1 Permit to Work and isolation are not an external black box

`[ANALYSIS]` §10 lists "Awaiting safety permit" and "Awaiting isolation" as hold reasons. That treats the Permit to Work (PTW) system as weather — something that happens to you and that you record.

In an operating power station, **PTW and isolation are the primary constraint on maintenance execution.** A large fraction of the "waiting" time the entire product exists to measure is permit and isolation time. If the MMS records only that a permit was awaited, and the actual permit lives in a separate system or on paper, then:

- Your headline metric is measured but not explicable. You can say "3,400 hours lost to permits" and not say why, which department, or which stage.
- Operations will reasonably dispute the number, because it was recorded by Maintenance about Operations with no shared source of truth.
- You cannot close the loop — the whole value proposition is turning a delay number into an action, and permit delays are among the most addressable.

**Minimum viable treatment for Phase 1:** a permit reference field on the work order, permit *requested* / *issued* / *returned* timestamps captured as first-class events, and the permit-holder identity. You are not building a PTW system — do not — but you must capture the three timestamps that let you decompose permit delay into "waiting for Operations to issue" versus "waiting for Maintenance to collect." Those are different problems with different owners.

`[ANALYSIS]` If the site already has an electronic PTW system, an integration to read those timestamps is worth more than any three features in §31. Ask this in discovery.

---

## 2.2 The regulatory and safety context the proposal does not mention

### Statutory inspection regimes

`[ANALYSIS]` A UK generating station carries a set of legally mandated inspection duties with hard deadlines and documentary evidence requirements — pressure systems written schemes of examination (PSSR 2000), lifting equipment (LOLER), electrical systems, and insurer-driven inspections. These are the maintenance activities with actual legal consequence attached.

If the MMS cannot show "every statutory inspection due this quarter, its status, and the certificate," it will not replace the spreadsheet that currently does. And a maintenance system that does not replace the spreadsheet ends up being a second place to type things.

**Required in Phase 1:** statutory work order type, due-date driven scheduling, non-negotiable evidence attachment, and a compliance view. `[ANALYSIS]` This is also, incidentally, an easy sell to management — statutory compliance visibility is a risk-reduction argument that needs no ROI model.

### Asset management standards

`[FACT]` **ISO 14224** defines a nine-level equipment taxonomy and standardised failure modes per equipment class for reliability and maintenance data collection. Adopt it for the fault category and failure mode taxonomy.

`[ANALYSIS]` **ISO 55000/55001** (asset management) is worth checking against — if the organisation holds or wants 55001 certification, the MMS becomes part of the evidence base for it, which is a strong additional funding argument and a set of requirements you would rather learn now than in year two.

### Cyber regulation — the one that can stop the project

`[FACT]` The Network and Information Systems Regulations 2018 designate operators of essential services in the energy sector. For electricity generation, the threshold is generators which, cumulated with affiliated undertakings, have total capacity input to a transmission system of **2 GW or more**; nuclear generators and generators not connected to a transmission system are excluded from that threshold. `[FACT]` Ofgem is joint competent authority with the sponsoring department for downstream gas and electricity in Great Britain. `[FACT]` A Cyber Security and Resilience Bill has been before Parliament to reshape this regime, and government has consulted on reshaping cyber regulation in downstream gas and electricity — so the obligations are tightening, not loosening.

**`[ANALYSIS]` Practical consequences, whether or not this particular station is over the threshold:**

1. If the operator is designated, it is assessed against the NCSC Cyber Assessment Framework, and any new system touching operational data enters that assessment scope. Expect a formal security assurance process, not a chat with IT.
2. Even below the threshold, the corporate parent will almost always apply the same standards group-wide. Assume you are in scope.
3. **Budget real time and money for security assurance.** `[ESTIMATE]` A penetration test, a threat model, secure SDLC evidence, and the associated remediation is `£8k–£20k` and 3–6 weeks of elapsed calendar time before production go-live. This is not in the original proposal's plan and it is not optional. Price it explicitly (see `06-pricing.md`).

---

## 2.3 The OT / IT boundary — the architectural constraint the proposal ignores

`[ANALYSIS]` §22 draws `UI → API → Business Logic → Database`. That is a web application diagram. It says nothing about where this system sits relative to the plant.

`[FACT]` The Purdue reference model places physical process at Level 0, basic control (PLCs, DCS) at Level 1, supervisory control (SCADA, HMI) at Level 2, site operations including the plant historian at Level 3, an industrial DMZ at Level 3.5, and business/enterprise IT at Levels 4–5. `[FACT]` IEC 62443 formalises this into zones and conduits, where every zone boundary requires a defined, controlled communication path. `[FACT]` Historians are a recognised lateral-movement vector precisely because they bridge OT and IT; the standard pattern is one-way replication from the OT historian to an IDMZ replica which IT systems then query, with no command path back into OT.

**Design rules this forces, which should be written into the blueprint:**

| Rule | Consequence |
|---|---|
| The MMS lives at Purdue Level 4/5. Always. | It is a business system. It is not plant equipment. |
| The MMS **never** writes to OT. Ever. No exceptions, no "just for the meter reading." | Running-hours-triggered PM needs a *read* of counter data, one-way, via the IDMZ replica. Design it as a pull from a replica, never a connection to a controller. |
| Asset IDs must reconcile with the OT tag naming convention (KKS, or whatever the station uses) | Get the station's tagging standard in discovery. If your asset IDs do not map to plant tags, engineers will not trust the system. This is the credibility test. |
| Any AI feature that sends fault text or asset data to a third-party model API is a **data classification decision owned by security, not by the project** | Do not design AI features that assume this will be approved. See `03`. |

`[ANALYSIS]` This section is also a *selling* asset. Turning up to the security review with the Purdue/62443 position already stated, and a written "no write path to OT" commitment, converts a hostile meeting into a formality. Very few internal project proposals do this.

---

## 2.4 The physical reality of mobile use in a power station

§21 proposes QR/NFC scanning and mobile-first design. Correct instinct. Underspecified reality:

- **Connectivity.** Turbine halls, boiler houses and basements are steel boxes. `[ANALYSIS]` Offline capability is not a "may later be required" (§21) — for the pilot department it is either a day-one requirement or you must scope the pilot to areas with confirmed coverage. Do a coverage survey in discovery; it is a half-day and it determines a large chunk of the build.
- **Offline is expensive.** True offline with conflict resolution is one of the most costly things in the whole scope. `[ANALYSIS]` The affordable 80% version: offline **read** of asset data and open work orders, plus offline **capture** queued for sync, with no offline editing of records others may have changed. Say this explicitly in the proposal so it is not assumed away.
- **Hazardous areas.** Zoned areas under DSEAR/ATEX may require intrinsically safe devices. Standard phones may be prohibited. This changes hardware cost and is the client's cost, not yours — say so in writing.
- **Cameras.** Some sites restrict photography. §5 and §21 make photos central. Confirm early.
- **Gloves, PPE, poor light, noise.** Large touch targets, no small dropdowns, no free-text-heavy flows, works one-handed. This is a real design constraint that should shape the UI, not a nicety.

---

## 2.5 Business continuity — absent from the proposal, first question from operations

`[ANALYSIS]` §36 lists DR as a question to be answered but the proposal contains no answer. Once maintenance depends on the MMS, the MMS becomes an availability concern. The question "what happens if this is down when a unit trips at 03:00" will be asked, and "it won't be" is not an answer that survives.

Minimum position to have ready:

| Item | Recommended Phase 1 position |
|---|---|
| RTO (recovery time objective) | 4 hours `[ASSUMPTION]` — confirm with the client |
| RPO (recovery point objective) | 15 minutes `[ASSUMPTION]` — point-in-time restore |
| Degraded mode | Documented paper fallback form + a defined catch-up entry process. Print it, put it in the control room, test it once during the pilot. |
| Read availability during partial failure | Read replica serving asset data and open work orders even when writes are failing — an engineer needs the asset history far more urgently than they need to log a status change |
| Backup testing | Restore rehearsal before go-live, then quarterly. An untested backup is a belief, not a control. |
| Data retention | Work order and audit history retained for the asset lifetime, not a 7-year default. `[ANALYSIS]` A turbine outlives your retention policy. |

---

## 2.6 KPI integrity problems the proposal has not solved

`[ANALYSIS]` §12 asserts that calculating KPIs from event history rather than editable fields prevents manipulation. It reduces one class of manipulation and leaves three untouched.

| Problem | Why it breaks the number | Fix |
|---|---|---|
| **Wall-clock vs working-time** | A job raised Friday 16:00 and started Monday 08:00 shows 64 hours' response time. Measured this way every KPI in §13 is wrong, and visibly unfair, which is worse. | Shift and roster calendar as a first-class object from day one. Every duration computed in both wall-clock and working-time. Clock-stop rules defined per SLA. This is very expensive to retrofit — put it in the locked-decision list. |
| **Overlapping holds** | Awaiting material *and* awaiting permit simultaneously. Naive summing double-counts and total waiting exceeds elapsed time. | Decide the rule now: one primary hold reason at a time with a documented precedence order is simpler and defensible. Attributing partial blame to two departments is a political argument you will lose. |
| **Late batch entry** | Technician logs six state changes at end of shift. The event log is honest — it faithfully records that all six happened at 17:45. The *timing data* is fiction. | Capture the difference between event time and record time on every event. Then report data-quality metrics — "% of events recorded within 15 minutes" — alongside the KPIs. Publishing the quality metric is what makes the KPI defensible. |
| **Gaming the reason code** | Coding a hold to move blame. | Precedence rules, derivation from linked records where possible, sampled supervisor verification, and — critically — not putting individual technicians in a league table in year one. |

`[ANALYSIS]` The fourth row is the one that matters most and the one that no amount of architecture fixes. Data quality in this system is a management practice, not a feature.

---

## 2.7 Consolidated list of what to add to Phase 1

| Addition | Why | Rough scope impact `[ESTIMATE]` |
|---|---|---|
| PM / PPM scheduling (calendar + running hours) | Without it this is not a CMMS | +15% |
| Work order types (corrective / preventive / statutory / modification / outage) | One lifecycle does not fit | +5% |
| Statutory compliance tracking + certificate evidence | Legal exposure; easiest management sell | +7% |
| Defect register with risk-accepted deferral | Otherwise backlog figures are fiction | +4% |
| Functional location vs serialised equipment split | Irreversible if wrong | +5% |
| Shift / roster calendar for working-time KPIs | Every KPI is wrong without it | +5% |
| Permit timestamps (request / issue / return) | Biggest single delay category | +3% |
| Outage window assignment | Power gen work is organised around it | +3% |
| Event-time vs record-time on all events | Makes KPIs defensible | +1% |
| Security assurance: threat model, pen test, remediation | Regulatory gate | +3 to 6 weeks calendar, `£8k–£20k` |
| Documented degraded mode + restore rehearsal | Operations will require it | +2% |

`[DERIVED]` Total functional scope increase over §31 as written: roughly **+48%**, offset by roughly **−30%** from removing the over-engineering identified in `03-architecture-changes.md` (workflow engine, message broker, three notification channels, microservice separation, AI layer). **Net Phase 1 scope is approximately +18% versus the original proposal, but pointed at materially more of the real problem.**

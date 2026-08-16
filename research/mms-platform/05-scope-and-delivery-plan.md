# Phase 5 — "Can You Do It To Perfection?" — Honest Answer, True MVP, Delivery Plan

---

## 5.1 The honest answer to the question you asked

**No. And I want to be precise about why, because the reason matters more than the answer.**

Three separate things are true:

**1. "Perfection" is not achievable by anyone, on any software of this kind.** Not by me, not by an agency, not by IBM. A maintenance system's correctness is defined by an organisation's actual working practices, and those are not fully known to anyone in the organisation — including the people who follow them. Roughly 30% of the requirements for this system do not exist yet in written form anywhere; they exist as habits in the heads of people who will not think to mention them until they see the wrong thing on a screen. `[ANALYSIS]` No specification phase extracts those. Only a working system in front of a real technician does.

**2. Aiming at perfection is the specific failure mode that kills this category of project.** It produces §32's thirty-four-item blueprint gate, then a long build against a spec that ages while it is being built, then a big-bang go-live where all the wrong assumptions surface simultaneously and there is no political capital left to fix them. `[ANALYSIS]` The projects that succeed here are the ones that get something narrow and real into one department's hands early and are cheerfully wrong about things they can still change.

**3. There is a large amount I *can* commit to, and it is more than would have been realistic a few years ago.**

### What I can commit to

- **Getting the eight irreversible decisions right** — the ones in `01` §1.2.1. Identity, tenancy, functional-location-vs-equipment, append-only event log, permission scoping, state machine as data, API contract and versioning, cost-hook placement. These are where "expensive to fix later" lives, and they are knowable in advance. Being right on these is the difference between a system that grows and one that gets replaced in year three.
- **Production quality, not prototype quality.** Automated tests on the state machine and KPI calculations, migrations under version control, structured logging, error tracking, backup and restore actually rehearsed, secrets managed properly, CI that blocks a merge that breaks module boundaries.
- **A working Phase 1 in one department in roughly 12–16 weeks**, not 12 months.
- **Speed on iteration.** `[ANALYSIS]` This is where AI-assisted development genuinely changes the economics, and it changes them in a specific way: not "the build is 5× faster" but "the *feedback loop* is 5× faster." A delay-reason taxonomy that is wrong on Monday can be right on Wednesday. Over a pilot, that compounds into a system that fits the plant far better than the calendar would normally allow.
- **Honest reporting.** If it is behind, you will hear it that week.

### What I cannot do, and what you must own

`[ANALYSIS]` This list is not a disclaimer. It is the list of things that actually determine whether the project succeeds, and none of them are code:

| Not mine | Whose |
|---|---|
| Knowing your plant's asset hierarchy, tagging standard, and which of the 4,000 tags matter | Yours, with plant engineers |
| Your PTW and isolation process as actually practised, not as documented | Yours |
| Getting Operations to agree that permit timestamps will be recorded | Yours — this is a negotiation, not a requirement |
| Security assurance sign-off | Client's security function. I can prepare everything; I cannot approve it. |
| Which manager will resist departmental KPI comparison, and how that is handled | Yours. `[ANALYSIS]` This is the biggest single risk in the whole programme and it is entirely political. |
| Technician training and the first eight weeks of adoption | Yours, with a named pilot supervisor |
| Data quality after go-live | Yours, permanently. No system fixes this. |
| Being accountable at 03:00 when a unit trips | Yours |

**`[ANALYSIS]` If I built this flawlessly and the pilot department did not code hold reasons honestly, the project would fail.** If I built it adequately and they did, it would succeed. That ratio is worth internalising before you set a budget: the software is maybe 40% of the outcome.

---

## 5.2 The true MVP — narrower than §31, and pointed at the real problem

Your §31 is a Phase-1 scope for a full CMMS. `[ANALYSIS]` The true MVP is smaller: the minimum that (a) one department will genuinely use instead of their current method, and (b) produces the delay data that funds everything after it.

### In the MVP

**Foundation**
- SSO (OIDC) sign-in, MFA, joiner/mover/leaver sync
- Organisation: company → site → unit → department
- RBAC with organisational scoping; field-level rule for cost fields
- Functional location hierarchy mapped to the plant tagging standard, with serialised equipment and dated installation records
- Append-only event log with event-time and record-time on every entry
- Shift / roster calendar (working-time KPI basis)
- Attachments with virus scanning

**Work management**
- Fault reporting: web + PWA on mobile, QR/NFC to asset, photo, 60 seconds start to finish for a reporter
- Work order types: corrective, preventive, statutory
- State machine as data, with required fields and required roles per transition
- Assignment, acknowledgement, start, pause, complete, verify, close
- **Hold capture: two taps, ranked reasons, optional note** — the highest-value 200 lines of UI in the system
- Permit reference plus requested / issued / returned timestamps
- Comments, watchers, escalation timers
- PM schedules: calendar-based and running-hours-based, with task lists
- Statutory inspections with mandatory certificate evidence
- Defect register with risk-accepted deferral and an outage-window field

**Intelligence**
- Work order timeline decomposed: active work · each hold category · verification
- Departmental delay attribution — **the headline report**
- Response time, acknowledgement, MTTR, backlog, overdue, PM compliance %, SLA — all in wall-clock and working-time
- Repeat-failure query by functional location
- Four dashboards: technician, supervisor, department manager, senior management
- **Data-quality metrics published beside the KPIs** (% of events recorded within 15 minutes, % of holds with a reason)

**Data**
- Excel import: staging → validation → mapping (with AI-assisted column suggestion) → duplicate scoring → exception review → human approval → load
- Legacy records land in a **separate, read-only legacy store** and are excluded from KPI baselines by default
- Filtered export to Excel/CSV, permission-scoped

**Non-functional**
- Threat model, pen test, remediation
- Documented degraded mode and rehearsed restore
- Structured logging, metrics, error tracking

### Explicitly out of the MVP

Warehouse · procurement · call-off contracts · invoicing · finance · full document management · workflow designer UI · message broker · SMS/WhatsApp/push · native apps · full offline editing · nine of the ten AI agents · predictive maintenance · contractor portal · multi-site rollout · reliability module · condition monitoring integration.

`[ANALYSIS]` Note one correction to §16 worth calling out separately: **do not merge legacy Excel data into live KPI baselines.** Legacy fault logs will not carry asset references that map cleanly, hold reasons will be absent, and timestamps will be dates rather than times. Migrate it for *search and history* — "has this pump failed before?" — and keep it out of the metrics. Otherwise your first six months of KPIs are contaminated by data that was never collected to that standard, and the first person to notice will use it to dismiss the whole system.

---

## 5.3 Delivery plan

`[ESTIMATE]` Assumes one senior engineer working AI-assisted, plus client-side time from a pilot supervisor and a plant engineer.

| Stage | Weeks | Output | Gate |
|---|---|---|---|
| **0 — Discovery & Blueprint** | 3 | Eight locked decisions; asset model against the real tagging standard; hold taxonomy v1 from real historical delays; security position (Purdue placement, hosting, data classification); migration assessment on the actual spreadsheets; **build-vs-buy recommendation**; acceptance criteria; fixed-price proposal | Client approves blueprint and proceeds, **or takes the buy recommendation and stops** |
| **1 — Spine** | 3 | Auth/SSO, org, RBAC, asset model, event log, shift calendar, state machine, API skeleton, CI with boundary enforcement | Demo: create asset, raise fault, move through lifecycle, inspect event log |
| **2 — Work management** | 4 | Full lifecycle, hold capture, permits, PM, statutory, defects, attachments, mobile PWA, notifications | Pilot supervisor runs five real jobs end to end and says it is faster than the current method |
| **3 — Intelligence & data** | 3 | KPI engine, four dashboards, delay attribution report, data-quality metrics, Excel import, exports | Numbers reconcile against a hand-calculated sample. **Non-negotiable gate.** |
| **4 — Hardening** | 2 | Pen test, remediation, DR rehearsal, degraded-mode doc, performance test, admin runbook | Security sign-off |
| **5 — Pilot** | 6 | One department live. Weekly iteration on taxonomy and UX. Training, floor support. | Acceptance criteria in §5.4 met |
| **6 — Rollout** | 4+ | Department by department. Never big-bang. | — |

`[DERIVED]` **Discovery to end of pilot: approximately 21 weeks** (~5 months), of which 12 weeks is engineering and 6 is pilot operation. Rollout follows.

`[ANALYSIS]` Stage 5 is where most of the value is created and most plans allocate nothing. Six weeks of pilot with weekly iteration is the difference between a system that gets adopted and one that gets tolerated. Do not let it be compressed — and price it as included work so nobody is tempted to cut it (see `06-pricing.md`).

---

## 5.4 Acceptance tests — answering §36 Q25

`[ANALYSIS]` These must be agreed **in the blueprint**, before the build. They are what converts "is it finished?" from an opinion into a measurement, and they are what protects a fixed price. Adoption and data-quality criteria matter more than functional ones here, because the functional ones are easy and the system fails on the others.

**Functional**
1. A reporter raises a fault from a phone by scanning an asset tag, with a photo, in **under 60 seconds**, first attempt, no training.
2. A technician places a job on hold with a reason in **two taps** in gloves.
3. Every state transition is rejected when its required fields are absent, and every rejection is logged.
4. A statutory work order cannot be closed without a certificate attached.
5. Work order timeline decomposes total elapsed time into active + each hold + verification, and the components sum to the total with no unattributed remainder.
6. A supervisor exports a filtered departmental report without administrator help.
7. Permission scoping verified: a Mechanical supervisor at Site A cannot see, edit or export Site B's records — checked via the API, not only the UI.

**Data integrity**
8. Ten randomly sampled work orders: system-calculated durations match hand calculation to the minute, in both wall-clock and working-time.
9. Migration: reconciliation report accounts for **100%** of source rows as loaded, rejected, or flagged duplicate. Zero silent drops.
10. Audit trail: for a sampled work order, reconstruct every change, who made it, when it happened and when it was recorded.

**Non-functional**
11. Restore from backup into a clean environment, rehearsed and timed, meeting the agreed RTO.
12. Pen test findings: no unresolved high or critical.
13. Search and dashboard load under 2 seconds at 3× projected data volume.
14. Degraded-mode procedure documented and walked through with the pilot department.

**Adoption — the ones that actually decide it**
15. ≥ **90%** of faults arising in the pilot department during the final pilot fortnight were raised in the system rather than by radio, email or paper. `[ANALYSIS]` This is the real test. Everything else is engineering.
16. ≥ **85%** of holds carry a reason code.
17. ≥ **70%** of events recorded within 15 minutes of occurring.
18. The pilot supervisor, asked privately, says they would object to it being taken away.

`[ANALYSIS]` Criterion 18 is not a joke and I would put it in the contract. It is the single best predictor of whether the rollout succeeds.

---

## 5.5 Answering §36 Q26 — performance assumptions to design for

`[ESTIMATE]` Design for these; they are comfortably above a single large station and cost almost nothing to accommodate up front.

| Dimension | Design target | Reasoning |
|---|---|---|
| Named users | 2,000 | Whole-site reporting population plus headroom |
| Concurrent users at shift handover | 300 | The genuine peak — everyone at once, twice a day |
| Functional locations | 50,000 | Large multi-unit station |
| Work orders per year | 60,000 | Corrective + PM + statutory across all departments |
| Events per work order | 25 | Every transition, hold, comment, attachment |
| Event rows after 5 years | ~7.5m | `[DERIVED]` 60k × 25 × 5. Trivial for Postgres with sane indexing. |
| Attachment volume | 2 TB over 5 years | `[DERIVED]` ~3 photos × 3 MB × 60k WOs × 5 yrs, rounded up. Object storage, not the database. |
| Migrated legacy rows | 250,000 | Separate read-only store |
| p95 API response | < 400 ms | |
| Dashboard load | < 2 s at 3× volume | Materialised views, refreshed on schedule |

`[ANALYSIS]` None of this is demanding. It is worth stating in the proposal precisely *because* it is undemanding — it tells the client's IT function that the system will not become their problem, which is the thing they are actually worried about.

# Phase 3 — Architecture: What I Would Change

This answers §36 questions 3, 4, 5, 10, 11, 16, 17, 18, 20 and 27 directly.

---

## 3.1 Overall shape: modular monolith, one database, hard internal boundaries

**`[ANALYSIS]` Answer to §36 Q3: modular monolith. Not microservices, not SOA. This is not a close call.**

Reasoning:

- Microservices solve *organisational* scaling — many teams shipping independently — and *heterogeneous* scaling. You have one team and, at a guess, a few hundred concurrent users at peak. `[ANALYSIS]` A single well-structured application on a single relational database will serve this workload for a decade.
- The cost of microservices here is paid immediately and forever: distributed transactions, eventual consistency in a system whose core value proposition is *precise event timing*, N deployment pipelines, N sets of secrets, N places to look when the KPI number is wrong. `[ANALYSIS]` The delay-accountability engine in particular wants strong consistency across work orders, holds and events. Splitting that across services is actively harmful.
- The genuine requirement behind §3's "one backbone, multiple modules" is **module boundaries you cannot accidentally violate**, not separate processes. Enforce that with package structure, a dependency-direction lint rule, and schema separation within one database. You get the future optionality without paying today.

```text
                 ┌─────────────────────────────────────────┐
                 │  Web (PWA)  │  Mobile (same PWA)         │
                 └──────────────────┬──────────────────────┘
                                    │  HTTPS / OIDC (corporate SSO)
                 ┌──────────────────▼──────────────────────┐
                 │            API layer (versioned)         │
                 ├──────────────────────────────────────────┤
                 │  core.identity   core.org   core.assets   │
                 │  core.documents  core.audit  core.notify  │
                 ├──────────────────────────────────────────┤
                 │  work.orders   work.holds   work.pm       │
                 │  work.statutory   work.defects            │
                 ├──────────────────────────────────────────┤
                 │  intel.kpi   intel.reporting              │
                 ├──────────────────────────────────────────┤
                 │  data.import   data.export                │
                 └──────────────────┬──────────────────────┘
                                    │
                 ┌──────────────────▼──────────────────────┐
                 │  PostgreSQL — schema per module          │
                 │  + append-only event table               │
                 │  + outbox table                          │
                 │  + read-replica for reporting            │
                 └──────────────────────────────────────────┘

  Dependency rule: work.* may depend on core.*  ·  intel.* may depend on
  work.* and core.*  ·  core.* depends on nothing  ·  no module reads
  another module's tables directly — module API only.
```

`[ANALYSIS]` That last line is the whole game. If `work.orders` selects directly from `core.assets` tables, you have a monolith with no boundaries and the future Warehouse module will require a rewrite. If it goes through a module interface, you can extract a service later on a Tuesday. Enforce it with a lint rule in CI, not with good intentions.

**Answer to §36 Q4 — which components are genuinely shared enterprise services:** identity, organisation structure, asset registry, documents, audit, notifications. That is six, and your §6 list is right. **Not** shared: workflow, KPI logic, reporting definitions — those are module-specific and pretending otherwise produces a generic abstraction that fits nothing.

---

## 3.2 The workflow engine: build a state table, not an engine

**`[ANALYSIS]` §9 proposes a configurable workflow/state engine. This is the most common over-engineering trap in this category of system, and it is a multi-month detour.**

What §9 actually needs is a *data-driven state machine*, which is a table:

| from_state | to_state | wo_type | required_role | required_fields | side_effects |
|---|---|---|---|---|---|
| `ASSIGNED` | `ACKNOWLEDGED` | any | assignee | — | stamp ack time |
| `IN_PROGRESS` | `ON_HOLD` | any | assignee, supervisor | `hold_reason_id` | open hold record, start hold clock |
| `ON_HOLD` | `IN_PROGRESS` | any | assignee, supervisor | — | close hold record |
| `WORK_COMPLETE` | `VERIFICATION` | corrective | supervisor | `completion_notes` | notify verifier |
| `WORK_COMPLETE` | `CLOSED` | preventive | supervisor | `pm_result` | — |
| `WORK_COMPLETE` | `CLOSED` | statutory | inspector | `certificate_doc_id` | compliance record |

That is a few hundred lines of code and a seed file. It gives you: per-work-order-type lifecycles, per-role transition permissions, mandatory-field enforcement at transition time, and a complete audit of allowed versus attempted transitions. `[ANALYSIS]` It delivers approximately 90% of the value of §9 for approximately 10% of the cost, and — importantly — it is *readable*, so an administrator can be shown the table and asked "is this right?"

What it does not give you is a drag-and-drop workflow designer UI. `[ANALYSIS]` You do not need one. Every organisation that has bought one has three workflows and a consultant.

**Answer to §36 Q11:** model transitions as data with required fields and required roles per transition, validated centrally, with every attempted transition (successful or rejected) written to the event log. The rejected ones are surprisingly valuable — they tell you where the process fights the users.

---

## 3.3 Events: an outbox table, not a message broker

`[ANALYSIS]` §23's event list is good and the concept is right. The implementation should be boring:

- Append-only `events` table in the same Postgres database, written in the **same transaction** as the state change. This is the critical property: an event that can be lost relative to the state change makes the audit trail a lie, and §12 depends on the audit trail being true.
- An `outbox` table for outbound delivery (notifications, future module hooks, future integrations), drained by a poller.
- No Kafka, no RabbitMQ, no service bus in Phase 1. `[ANALYSIS]` They add operational surface, a second thing to secure and back up, and an at-least-once delivery model you will have to write deduplication for. Postgres gives you transactional guarantees for free and will handle this volume without noticing.

Design the event **payload schema and versioning policy** now, because that is the part that is expensive to change and the part that future modules bind to. The transport is cheap to swap later; the contract is not.

**Answer to §36 Q18 — which APIs and events to define now:** define the *event catalogue* and its versioning rules now (your §23 list is a good start; add `PM_DUE`, `STATUTORY_DUE`, `DEFECT_DEFERRED`, `PERMIT_REQUESTED`, `PERMIT_ISSUED`, `PERMIT_RETURNED`, `OUTAGE_ASSIGNED`). Define the *read* API contracts now. Do not define Warehouse or Procurement APIs now — `[ANALYSIS]` you will guess wrong, and a wrong API contract you have committed to is worse than no contract.

---

## 3.4 The asset model, concretely

Per `01-verdict-and-critique.md` §1.3, this is the decision to get right.

```text
Site
 └── Unit
      └── System                        (KKS or site tagging standard)
           └── FunctionalLocation        ← permanent position, e.g. "U1 CW Pump A"
                 │                          criticality, spares policy, PM plan,
                 │                          failure history attaches HERE
                 └── InstallationRecord   ← dated: which Equipment was here, when
                          └── Equipment   ← serialised physical item
                                             manufacturer, model, serial,
                                             refurbishment history attaches HERE
```

Rules:

- Permanent, human-meaningful IDs for functional locations that **map to the station's existing plant tagging standard**. `[ANALYSIS]` Do not invent `AST-CWP-000123` as in §7 if the plant already calls it `1LAC10AP001`. Engineers trust the plant tag and distrust anything else; a parallel identifier scheme is a credibility problem, not a data problem. Carry your surrogate key internally and *display* the plant tag.
- Work orders reference the functional location **and** resolve the equipment installed at the reported time.
- Equipment class and failure mode from **ISO 14224** rather than a bespoke taxonomy.
- Criticality on the functional location, driving default priority and SLA — and later, in the Warehouse module, driving spares stocking policy. `[ANALYSIS]` That single field is the join between the MMS and the future Warehouse business case; it is the field that lets you say "we stock nothing for a critical position that failed four times."

**Answer to §36 Q10:** functional-location hierarchy aligned to the plant tagging standard, with serialised equipment linked by dated installation records, classes and failure modes per ISO 14224, criticality at the location.

---

## 3.5 Permissions

`[ANALYSIS]` §6.3's five named roles are a reasonable starting *configuration* but a poor *model*. Roles alone cannot express "supervisor, but only for Mechanical, only at Site B." Every real request in this domain has a scope attached.

Model: **`(role) × (scope)` grants**, where scope is a node in the organisation or site tree, plus fine-grained permissions attached to roles.

```text
Grant = { user, role, scope_type: site|department|unit, scope_id }

Permission check = does any grant held by this user
                   carry the required permission
                   AND cover the record's scope?
```

- Permissions are the atoms (`work_order.assign`, `work_order.close`, `kpi.view_department`, `kpi.view_all_departments`, `cost.view`, `audit.view`). Roles are named bundles. Grants bind a role to a scope.
- `[ANALYSIS]` The confidential-procurement carve-out in §6.3 is a *field-level* concern, not a role concern. Design field-level visibility rules from the start for cost fields specifically — they are the only ones that need it in Phase 1, and retrofitting field-level security later touches every endpoint.
- Every permission denial gets logged. Denials are how you discover the permission model is wrong.

**Answer to §36 Q15:** RBAC with organisational scoping and explicit field-level rules for cost data. Not ABAC — `[ANALYSIS]` a policy engine is over-engineering at this size and nobody will be able to answer "why can Dave see this?"

---

## 3.6 Reporting

`[ANALYSIS]` §18's instinct — do not run dashboards against production tables — is right, but a separate analytics stack in Phase 1 is not.

Phase 1: a **read replica** plus materialised views refreshed on a schedule, with all KPI logic in versioned SQL views under source control. `[ANALYSIS]` The critical discipline is that a KPI is defined **once**, in one place, and the dashboard, the export and the API all read the same definition. The moment MTTR is computed in two places, they diverge, someone notices in a management meeting, and the system's credibility never fully recovers. That is a real risk and it is a governance risk, not a technical one.

Phase 3+: if and when the data volume genuinely justifies it, a warehouse. Not before. Your §18 diagram is a good *year-three* target and a bad year-one build.

---

## 3.7 AI: what to actually build, and when

`[ANALYSIS]` §27 specifies ten agents. My assessment:

| Proposed agent | Verdict |
|---|---|
| Fault Triage | **Build — Phase 2.** Genuinely useful, low risk, needs ~6 months of real data first to be better than a dropdown. Suggestion only, never auto-apply. |
| Management summary / KPI explainer | **Build — Phase 2.** High perceived value to the exact people who fund Phase 3. Strictly narrating figures the SQL already computed. |
| Data Migration assistant | **Build — Phase 1, as a tool, not an agent.** Column mapping suggestion and duplicate candidate scoring during import. Human approves everything. |
| Maintenance Planner | Defer. Needs manuals, parts and history you will not have. |
| Warehouse / Procurement / Cost agents | Defer — the underlying modules do not exist. |
| Reliability agent | Defer to Phase 3. `[ANALYSIS]` Repeat-failure detection is a SQL query, not an agent. Build the query in Phase 1 and skip the agent. |
| Audit agent | Defer. Anomaly detection on a system with no behavioural baseline produces noise. |

**Answer to §36 Q20 — how to govern AI:**

1. AI **never** writes directly. It proposes; a human with the relevant permission commits. Every AI-proposed value is stored with provenance so you can measure acceptance rate and kill features nobody accepts.
2. AI reads through the same permission-scoped API as a user, running as a service principal with **explicitly narrower** rights than any human role. If the API would refuse a human, it refuses the model.
3. Every AI call and its inputs are audit-logged. In an NIS-regulated context you will be asked what data left the estate. "I don't know" ends the conversation badly.
4. **The data classification question is owned by security, not by the project.** Sending fault descriptions and asset tags to a third-party model API may be prohibited outright. Design so the model provider is swappable — including for a self-hosted model — and do not build any feature whose business case collapses if the answer is "on-premises only."
5. `[ANALYSIS]` Do not put AI in the Phase 1 pitch beyond the import assistant. It invites a security review you do not need yet, on a feature that is not yet valuable, at the exact moment you are trying to get approval for something else.

---

## 3.8 Technology choices

`[ANALYSIS]` Deliberately boring, because a bespoke system's real risk is the decade after go-live, not the quarter before it.

| Layer | Recommendation | Why |
|---|---|---|
| Database | PostgreSQL | Transactional event log, JSONB where the schema must flex, mature, runs anywhere including on-prem. The one non-negotiable good choice here. |
| Backend | One language, boring framework, strongly typed. .NET or Java if the client's IT will inherit it; Python/TypeScript if you retain it. | **Pick the one the client's IT department can hire for.** `[ANALYSIS]` This is a commercial decision disguised as a technical one — ask it in discovery. Getting it wrong makes handover impossible and locks you into support you may not want. |
| Frontend | Single PWA serving desktop and mobile | One codebase. Installable, offline-capable, no app store, no MDM negotiation. `[ANALYSIS]` Native apps in Phase 1 roughly double frontend cost for benefits you do not need yet. |
| Auth | Corporate SSO via OIDC (Entra ID most likely), MFA enforced, SCIM or scheduled sync for joiners/movers/leavers | Non-negotiable in this sector. Local password auth will fail the security review. |
| Hosting | Ask in discovery; design to run in either | `[ANALYSIS]` Many generators have cloud restrictions. If you assume cloud and they say on-prem, you rebuild deployment. Containers plus managed Postgres or plain Postgres keeps both doors open at near-zero cost. |
| Files | S3-compatible object storage, presigned URLs, virus scanning on upload | Photos will be the bulk of the data volume. |
| Observability | Structured logs, metrics, error tracking from day one | Cheap now, impossible to retrofit under pressure. |

---

## 3.9 What to remove from the original proposal

| Remove from Phase 1 | Replacement | `[ESTIMATE]` saving |
|---|---|---|
| Configurable workflow engine + designer UI (§9) | State transition table + seed data | 4–6 weeks |
| Message broker / event bus (§23) | Events + outbox tables in Postgres | 2–3 weeks |
| SMS, WhatsApp, push channels (§19) | Email + in-app + Teams webhook | 1–2 weeks |
| Separate analytics stack (§18) | Read replica + materialised views | 2–3 weeks |
| Microservice separation (§36 Q3) | Modular monolith, enforced boundaries | 3–4 weeks + ongoing |
| Eight of ten AI agents (§27) | Import assistant only | 4–6 weeks |
| Full document management (§20) | Attachments with tags and versioning | 1–2 weeks |
| Warehouse/Procurement API contracts (§5 hooks) | Event catalogue only; contracts when the module is real | 1 week |

`[DERIVED]` **Approximately 18–27 weeks of effort removed.** That is what pays for everything in `02-what-is-missing.md`, and it is why the net scope change is modest despite the long list of additions.

**Answer to §36 Q5 — what is over-engineered for the first release:** the table above, in that order.

**Answer to §36 Q27 — what must be added now so future modules do not require redesign:** functional-location/equipment split, criticality on locations, event catalogue with versioning, module boundary enforcement, permission scoping model, cost hooks as nullable fields on work orders, and the shift calendar. Everything else can wait.

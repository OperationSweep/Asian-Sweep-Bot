# Revised Build Plan
## Asian Session Liquidity Sweep Bot — Research-Safe Rebuild

## Why the current prototype is not deployable
The original single-file prototype is useful as a scaffold, but it is not safe to deploy because:

- strategy rules are too ambiguous in live-trading-critical areas
- BOS and swing logic are too crude
- state is only held in memory
- there is no durable signal/trade journal
- scheduling is fragile for unattended deployment
- execution assumptions are cleaner than reality

## Phase 0 — Freeze baseline
- preserve the original prototype as the baseline reference
- do not deploy it
- do not mistake a working script for a validated strategy

## Phase 1 — Formalise strategy
Deliver:
- `strategy_spec.md`

Define exact rules for:
- H4 bias
- Asian range
- sweep conditions
- invalid-day logic
- swing/BOS confirmation
- filters
- entry, SL, TP, BE, force close

## Phase 2 — Redesign architecture
Separate concerns into modest modules:
- data feed
- strategy
- execution
- state storage
- journaling
- entry point/config

## Phase 3 — Persistent state
Add daily persistent state so restart/recovery is possible.
Suggested first implementation:
- JSON state file per day or rolling JSON state file

## Phase 4 — Signal engine rebuild
Rebuild in this order:
1. bias engine
2. Asian range engine
3. sweep engine
4. invalidation engine
5. swing/BOS engine
6. qualification filters

## Phase 5 — Execution rebuild
Improve:
- fill price vs signal price separation
- spread checks
- stop distance checks
- force-close robustness
- TODO markers where broker-specific behaviour still needs validation

## Phase 6 — Journaling
Add:
- event log
- daily signal journal
- trade journal

The objective is to produce evidence, not just output.

## Phase 7 — Dry-run / paper mode
Before demo execution, support signal-only mode.
This allows:
- skipped-day analysis
- sweep/BOS review
- validation of session behaviour

## Phase 8 — Validation
Validation order:
1. historical / replay-style sanity testing
2. forward signal logging
3. demo account testing
4. tiny live pilot only if results justify it

## Phase 9 — Deployment
Only after validation:
- service/supervisor runtime
- restart handling
- log review
- kill switch
- daily health checks

## What to keep from the current repo
- basic MT5 connection direction
- logging scaffold concept
- one-trade-per-day discipline
- force-close session discipline
- break-even at 1R concept

## What to rewrite first
Priority order:
1. strategy formalisation
2. persistent state
3. BOS/swing precision
4. qualification filters
5. journaling
6. safer runtime structure

## Milestones
### Milestone 1
- strategy spec locked
- architecture documented

### Milestone 2
- research-safe scaffold built
- dry-run mode available
- persistent state and journals working

### Milestone 3
- demo execution path ready
- restart safety improved

### Milestone 4
- validation review completed
- go/no-go decision for live pilot

## Bottom line
The right path is:
- formalise
- scaffold
- validate
- then deploy

Not:
- code quickly
- hope YouTube equals edge
- deploy blind

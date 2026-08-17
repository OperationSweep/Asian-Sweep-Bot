# Asian-Sweep-Bot

Research-first rebuild foundation for an **Asian Session Liquidity Sweep + Break of Structure** trading bot on **EURUSD**.

## Current status

This repo started as a single-file MetaTrader5 prototype generated from a strategy prompt. After audit, it was **not considered safe to deploy** as-is because:

- the strategy rules were too ambiguous in key areas
- BOS and swing logic were too crude for live use
- runtime state was only in memory
- there was no durable signal/trade journal
- scheduling and restart safety were too weak for unattended trading

This repo is now being reshaped into a **research-safe scaffold**.

## What this repo is now

This is **not a production-ready live trading bot**.

It is a structured foundation for:

- formalising the mechanical rules of the strategy
- separating data, strategy, execution, state, and journaling concerns
- running dry-run / paper-mode signal research safely
- building a path toward demo validation before any live deployment

## Why not deploy yet

Do **not** deploy this inside a VPS/VPN for live money yet.

The strategy still needs:

- tighter rule validation
- forward testing
- broker-specific execution checks
- spread/slippage evaluation
- demo account verification
- restart/recovery testing

## Repo structure

- `bot.py` — main entry point and scheduler
- `config.py` — configuration and risk/execution settings
- `datafeed.py` — MT5 connectivity and market data helpers
- `strategy.py` — bias, Asian range, sweep, BOS, and qualification logic
- `execution.py` — execution and position management scaffolding
- `state_store.py` — persistent daily state handling
- `journal.py` — structured event/signal/trade journaling
- `strategy_spec.md` — exact mechanical strategy rules
- `build_plan.md` — revised build and validation plan

## Immediate next milestones

1. Lock strategy rules (`strategy_spec.md`)
2. Run in dry-run / paper mode only
3. Validate signals and skipped-day logic
4. Add demo execution validation
5. Only consider live pilot after evidence exists

## Notes

- The code aims to be runnable in principle, but it is intentionally conservative.
- Where live-trading-critical behaviour is still uncertain, the code uses TODO notes rather than pretending the logic is settled.
- Truth over hype.

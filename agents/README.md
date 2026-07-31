# Operator — the work agent

A single, maintained, continuously-learning agent for OperationSweep, replacing the
throwaway agents currently sitting in the Mistral Studio console.

---

## The one idea that matters

> **Git is the source of truth for the agent. Mistral Studio is a deploy target.**

Right now the agent definitions live only in the console. That is why there are eleven of
them called `enti`, `entit`, `hello` and `hell` — a console is a place to *try* things, and
nothing that is only tried ever gets maintained. Nothing is reviewable, nothing is
diffable, nothing can be rolled back, and "learning" can only mean *retyping the prompt*.

Everything here inverts that. The instructions, the memory, the tool policy and the
evaluation set are files in this repository. A script pushes them to Mistral. The console
becomes a *view* of what is in `main`, not the place where the agent secretly lives.

That single inversion is what makes the other two requirements — continuous learning and
work-system integration — actually buildable rather than aspirational.

---

## What "continuously learning" means here

An LLM does not learn from talking to you. Nothing is retained between conversations, and
no amount of prompting changes that. So continuous learning has to be *built*, and it is
built out of four moving parts:

| Part | Where it lives | What it does |
|---|---|---|
| **Retrieved memory** | Mistral Library (RAG) | Unbounded, cheap, recall-based. Facts, metrics, decisions, past failures. |
| **Resident memory** | `instructions.md` | Tiny, always-on, expensive per token. Identity, policy, protocol only. |
| **The loop** | n8n + GitHub PR | Capture → consolidate → human gate → deploy → evaluate. |
| **The ratchet** | `eval/` + agent versioning | Proves each version is better than the last, and rolls back when it isn't. |

The distinction between **retrieved** and **resident** memory is the part most agent
designs get wrong. They pour everything into the system prompt until it is four thousand
tokens of accumulated trivia, the model's attention is spread thin, and quality silently
degrades. Here, almost everything learned goes into the Library and is *retrieved on
demand*; promotion into the always-on instructions is rare and explicitly gated.

The other thing most designs get wrong is having no gate at all. An agent that writes
freely to its own memory will eventually learn something false, retrieve it, act on it,
and record the result as confirmation. **Every memory write in this design lands as a pull
request against this repo.** You approve it or you don't. That is deliberately a small
amount of friction, and it is the difference between a system that compounds and one that
rots.

Full mechanism: [`work-agent/learning-loop.md`](work-agent/learning-loop.md).

---

## Layout

```
agents/work-agent/
├── agent.yaml            # deployable config: model, tools, connectors, limits
├── instructions.md       # THE system prompt — the actual agent
├── learning-loop.md      # how learning works, end to end
├── integration.md        # per-connector policy + the n8n workflows
├── memory/
│   ├── SCHEMA.md         # the memory record format and write rules
│   ├── 00-charter.md     # durable truths — who, what, constraints
│   ├── 10-decisions.md   # append-only decision log
│   ├── 20-playbooks.md   # procedures that worked
│   ├── 30-metrics.md     # numbers that must stay current
│   └── 40-failures.md    # what went wrong and the rule it produced
├── eval/
│   ├── golden-set.yaml   # 18 graded cases
│   └── rubric.md         # how a response is scored
├── deploy.py             # repo → Mistral (agent + library), versioned
├── evaluate.py           # score a version, compare to baseline, roll back
└── requirements.txt
```

---

## Build order

Do these in sequence. Each step is useful on its own, so you can stop after any of them
and still have something better than what is in the console today.

**1 — Deploy it as it stands.** *(~15 minutes)*

```bash
cd agents/work-agent
pip install -r requirements.txt
export MISTRAL_API_KEY=...
python deploy.py --create          # creates the library + agent, writes .deploy-state.json
python evaluate.py --set-baseline  # records the starting score
```

You now have one real agent, defined in git, with a measured baseline. Commit
`.deploy-state.json`.

**2 — Fill the charter.** *(~30 minutes, and it is the highest-leverage half hour here)*

`memory/00-charter.md` ships with everything derivable from this repository, and gaps
marked `[NEEDS INPUT]`. Fill those in. The charter is what makes the agent *yours* rather
than a generic assistant, and no amount of clever prompting substitutes for it.

**3 — Wire the read-only connectors.** Gmail, Calendar, Drive, Shopify, GitHub — read
scopes only. See [`integration.md`](work-agent/integration.md). The agent becomes useful
here: it can see the work rather than being told about it.

**4 — Turn on the learning loop.** The three n8n workflows in `integration.md`: capture,
nightly consolidation, weekly promotion PR. This is the point at which it starts
compounding.

**5 — Grant write scopes, one at a time.** Drafts before sends. Draft PRs before pushes.
Each expansion gets a golden-set case *before* it gets the permission.

**6 — Delete the console agents.** Keep `CyberSecurity Vulnerability Analysis` if it is
doing real work; make it a second file here if so. Delete the rest. An agent list you
cannot read is an agent list you cannot trust.

---

## Deliberate non-goals

- **No fine-tuning.** At this data volume it would cost more, take longer, and learn less
  than retrieval does. Revisit at ~10k graded interactions, not before.
- **No autonomous spend, ever.** Not on ads, not on Stripe, not on inventory, not on
  Motion credits. The agent proposes; a human commits money.
- **No live trade execution, and no turning off dry-run.** The bot is a research scaffold
  (`DRY_RUN = True`) and not cleared for live money. The agent reads journals and proposes
  config diffs; it never places an order and never proposes flipping the flag that would
  make orders real. That boundary is in `agent.yaml` and in the instructions.
- **No multi-agent fan-out yet.** One good agent with real memory beats five agents with
  none. Mistral supports `handoffs` when a genuine specialist is warranted; the first
  candidate is a compliance reviewer, and it should wait until the ecommerce venture
  actually trades.

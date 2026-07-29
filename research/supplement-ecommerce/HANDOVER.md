# HANDOVER BRIEF — read this first

**You are picking up a piece of commercial research mid-project.** This file tells you what exists, what was decided, what is still open, and where the weak points are. Read this, then `README.md`, then whichever analysis file the task needs.

---

## 1. Context

The user is evaluating whether to build a **UK direct-to-consumer supplement brand**, acquiring customers through faceless short-form video (TikTok / Instagram Reels / Facebook), selling via a Shopify-style store.

They commissioned a 20-phase investigation and explicitly asked for it to be **stress-tested, not agreed with**. That instruction was followed, and it matters: the research concludes the model **as originally briefed does not work**, and recommends a modified version. Do not quietly revert to the original framing.

**Work was done in a cloud container (Claude Code, Opus 5) on 29 July 2026.** All research is complete and merged to GitHub. The user is now moving to their desktop to continue.

## 2. What exists

| File | What it is |
|---|---|
| `README.md` | Index, executive summary, verdict, scores, next actions |
| `01-market-analysis.md` | Market sizing (global/US/EU/UK), category growth, margin structure, demographics |
| `02-product-database.md` | 60-product database — 4 linked tables + excluded-products list |
| `03-ranking-and-shortlist.md` | Weighted scoring method; Top 20 → Top 10 → Top 5 |
| `04-marketing-and-compliance.md` | Faceless-social viability; Meta/TikTok/Google ad-policy map |
| `05-uk-regulation.md` | FSA, MHRA, ASA/CAP, labelling, VAT, GMP, recall, imports, insurance |
| `06-business-models-and-suppliers.md` | 5 business models scored /100; supplier comparison; RFQ template |
| `07-unit-economics.md` | Per-product unit economics (£GBP); 12 bundle concepts; formulation safety rules |
| `08-competitors-and-positioning.md` | Competitor financials; 11 positioning options scored |
| `09-financial-model.md` | Month 1/3/6/12 + Year 1/2/3 P&Ls, three cases; £1m reverse-engineering |
| `10-launch-and-content.md` | MVP → Phase 3 roadmap; content engine; 30 compliant video concepts |
| `11-risks-and-decision.md` | Risk register; hidden opportunities; final decision; budget tiers |
| `12-sources.md` | All sources grouped by claim, with quality tiering |
| `13-cac-pressure-test.md` | **Addendum. Revises the core CAC assumption and corrects three errors in 09.** |
| `CONVERSATION-TRANSCRIPT.md` | The full conversation that produced all of the above |

**⚠️ `13-cac-pressure-test.md` supersedes parts of `09-financial-model.md`.** If the two disagree, 13 is correct. It was written later, after the user asked for the CAC assumptions to be attacked. The base P&Ls in 09 were *not* retrospectively rebuilt — the deltas are stated in 13 instead. **If you are asked to rebuild the financial model, start by applying 13's corrections to 09.**

## 3. The conclusions, compressed

**Verdict: MODIFY → GO.** Opportunity 68 · Risk 72 · Scalability 74 · Profit potential 58 · Social suitability 81 (all /100).

1. **Single-product selling to cold paid traffic is arithmetically loss-making.** No single-unit order in the Top 10 covers even a best-case £38 CAC. Bundles and subscription are load-bearing, not optimisations.
2. **Launch 3 SKUs:** creatine monohydrate 500g, electrolytes 30-stick, magnesium glycinate 120ct. ~£9,400 opening inventory. Hero offer is the **Foundation Stack at £64.99** (£33.44 contribution vs £14.57 for a single tub).
3. **Creatine is the standout product** — 26.2% global CAGR, ~£3.20 COGS at £29.99, an authorised GB health claim, and an audience broadening to women and over-45s that no incumbent addresses.
4. **Positioning:** "Foundational performance nutrition, evidence-first, for adults who intend to be strong at 60." Deliberately targets the least-contested audience (40–65 on Facebook) rather than 18–34 men on TikTok.
5. **Business model:** UK private label (78/100) + subscription layer (88/100) → custom formulation in Year 2. **Dropshipping scored 22/100 and is arithmetically impossible** at a £70 CAC.
6. **Capital:** £25,000 recommended, on a self-funding ad ramp (spend capped at ≤130% of trailing 30-day contribution). Running at full speed needs ~£80,000 peak working capital.
7. **This is an asset play, not an income play.** £1m of revenue models to ~£58k EBITDA (~7% net). Huel makes 7.6% net at £254m. The return is in the exit multiple (Huel sold at ~3.9× revenue), not the cash flow.
8. **Compliance is the moat.** ~£5k/year. The key regulatory insight is counter-intuitive: **the ad copy, not the formula, is what can reclassify a supplement as an unlicensed medicine** under MHRA Guidance Note 8.

## 4. Where this research is weakest — attack these first

Stated plainly so you don't have to rediscover them:

1. **Every COGS figure is an estimate, not a quote.** The five-way manufacturer RFQ (template in `06`) has **not** been sent. This is the single most important outstanding action. All margin conclusions survive a ±20% COGS move, but they should still be replaced with real numbers.
2. **CAC has a plausible 14× range** (£13–£183 across scenarios, per `13`). No further desk research narrows it. Only real spend measures it. This is why the day-90 kill criteria matter more than any other part of the plan.
3. **`09`'s base P&Ls were not rebuilt after the CAC revision.** Deltas are in `13` §3. Year 1 EBITDA moves from −£12.0k to ~−£16.5k; payback from 12 to ~14 months.
4. **Market-size figures come from commercial research houses** whose numbers disagree by up to 2× and whose forward CAGRs are systematically optimistic. They are labelled and ranged, and **no financial projection is built on them** — the model is bottom-up from UK unit economics. Keep it that way.
5. **TikTok Shop was under-weighted in the original modelling.** `13` §5 finds it first-order profitable where paid social is not. The financial model in `09` still assumes a paid-social-led acquisition mix. **This is the largest unmodelled upside in the research.**
6. **No seasonality in the model.** UK CPMs swing ±45% between January and November (`13` §6). Recommended launch window is January.

## 5. Rules the user set, which you should keep

- **Do not fabricate product-level revenue or margin.** It does not exist as public data — companies report at group or segment level. Where it was unavailable it is marked `[NOT PUBLIC]`, deliberately. The one derivable brand-level figure (Optimum Nutrition) shows its arithmetic. **Maintain this discipline.**
- **Every material figure carries an evidence label:** `[FACT]` / `[DERIVED]` / `[ESTIMATE]` / `[ASSUMPTION]` / `[ANALYSIS]` / `[NOT PUBLIC]`. Keep labelling anything you add.
- **Do not recommend products that are illegal, prescription-only, or platform-banned merely because they sell well.** The exclusion list is in `02`. Notably: melatonin is **prescription-only in Great Britain**; weight-loss, fat-burner, detox and sexual-performance products are **prohibited on TikTok Shop**; shilajit is excluded for documented heavy-metal contamination.
- **Do not write marketing copy containing health claims outside the GB Nutrition and Health Claims Register**, and never reference a disease, condition or symptom by name. See `04` and `05` §7.1.
- **Do not agree reflexively.** The user explicitly asked for the idea to be stress-tested. They responded well to being told the arithmetic did not work.

## 6. Outstanding actions, in order

1. **Send the 5-way manufacturer RFQ** (template: `06` §"The RFQ"). Replace every estimated COGS with a quote. — *not started*
2. **Commission a UK food-law label and claims review** (~£800–£2,500 for 3 SKUs). — *not started*
3. **Set up duplicate ad infrastructure** (2 Business Managers, 2 ad accounts, 2 verified domains) *before* it is needed. — *not started*
4. **Produce 30 videos before spending anything on ads**; test hooks organically first. Concepts are in `10`. — *not started*
5. **Write down and sign the day-90 kill criteria** (`10`) before any emotional investment exists. — *not started*
6. **Rebuild `09`'s P&Ls** applying `13`'s corrections, and model a TikTok-Shop-led acquisition mix. — *not started*
7. Decide whether to split this research into its own repository — it currently sits inside an unrelated MetaTrader5 trading-bot repo.

## 7. Repository state

- **Repo:** `OperationSweep/Asian-Sweep-Bot` (a EUR/USD MetaTrader5 trading bot — the research is unrelated to the code and simply lives alongside it)
- **Branch:** `claude/asian-sweep-bot`
- **Path:** `research/supplement-ecommerce/`
- **PR #5 merged** 29 July 2026 (merge commit `77a3d8d`), 2 commits, 14 files, +2,420 lines
- **No CI** in this repository; no tests apply to this work

```bash
git clone https://github.com/OperationSweep/Asian-Sweep-Bot.git
cd Asian-Sweep-Bot && git checkout claude/asian-sweep-bot
```

## 8. Suggested opening move

If the user gives you no specific instruction, the highest-value thing you can do is **item 6** — rebuild the financial model applying the `13` corrections and adding a TikTok-Shop-led scenario. It is the largest known gap, it is entirely desk work, and it directly changes the capital recommendation.

Do not re-run the market research. It is done, sourced, and labelled.

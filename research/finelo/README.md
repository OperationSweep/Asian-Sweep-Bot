# Finelo — Company Research and Benefit Assessment

**Question investigated:** *What is Finelo, is it credible, and what concrete value does it have for us — as a learning resource, as a product blueprint for the Asian Sweep Bot, as a business model, or as a technical integration?*

**Date of research:** August 2026 · **Subject:** Finelo Limited (Limassol, Cyprus), part of Zimran Ltd. (Kazakhstan)

---

## ⚖️ VERDICT: **DO NOT BUY AS A LEARNER — STUDY IT AS A BLUEPRINT**

| Benefit vector | Score /100 | Verdict |
|---|---|---|
| **As a learning tool for you** | 12 | ❌ **NO** — beginner content, you are years past it |
| **As a product blueprint for Asian-Sweep-Bot** | 84 | ✅ **YES** — the highest-value finding here |
| **As a business-model comparable** | 71 | ✅ **YES** — better shape than the supplement plan |
| **As a technical integration (API/affiliate)** | 6 | ❌ **NO** — nothing exists to build against |
| **As a partner / commercial counterparty** | 15 | ❌ **NO** — no public partner route |

**Recommended commitment:** **$19.99, one month, one account** — bought as competitive reconnaissance, not as education. Cancel inside the first billing cycle. Total exposure ~$20. Do not buy the 12-week plan.

---

## Executive summary — the seven findings that matter

1. **Finelo is real, and it is not a scam.** `[FACT]` Finelo Limited is the App Store developer of record; the app holds **4.6★ from ~99,000 US App Store ratings** and **4.6★ from 17,000+ Trustpilot reviews**. The product exists, the courses deliver, the simulator works. The word "scam" attaches to it almost entirely through **billing friction, not fraud** — see finding 5.

2. **It is useless to you as education, and that is not a close call.** `[FACT]` The curriculum is 300+ bite-sized lessons (~3 min each) covering "what is a stock", "how to read a chart", investing vs trading. Reviewers converge on one criticism: *"advanced traders and experienced investors will find Finelo's content too introductory."* `[ANALYSIS]` You have already written a modular MT5 bot that marks an Asian session range across two timezones, detects fractal swing points, waits for a liquidity sweep, confirms a break of structure, qualifies the setup against spread and stop-distance limits, sizes to 1:2 RR, trails to break-even at 1R and journals every signal. Finelo teaches the first 2% of that. **There is no lesson in it for you.**

3. **The real find: Finelo has already productised the exact thing sitting in this repo.** `[FACT]` Finelo ships an **AI Bots store** — bots that scan markets continuously for matching setups, explain each setup in plain language, and let the user **approve or decline in one tap**, with a bell icon showing every setup found and whether it was approved, declined or expired. `[ANALYSIS]` That is `detect_sweep()` → `detect_bos()` → `qualify_trade()` → a human gate → `place_trade()`. Measured against the scaffold on `main`, **we are two features short, not four** — a backtest harness and a plain-language setup explainer. Simulated execution (`DRY_RUN`) and the setup journal are already built and already default-on.

4. **And they solved the regulatory problem, which is the part actually worth copying.** `[FACT]` The bots run **entirely in a simulator on virtual funds with real market data**; Finelo is **not a brokerage**, connects to **no** real account, and states plainly that it "does not provide personalized financial advice." `[ANALYSIS]` This is the identical structural insight to finding #7 of the supplement research — *compliance is the moat, not the overhead* — and the identical mechanism: **your marketing copy, not your code, is what determines whether you are carrying on a regulated activity.** Under FSMA s.19 and s.21 the FCA has asserted that teaching activity can amount to advising on or arranging deals in investments. Finelo's answer is the firewall: simulated execution, no personalisation, education framing, explicit disclaimer. `[ANALYSIS]` **`DRY_RUN = True` in `config.py` is the same firewall, and it is already the default** — which reframes it from a safety flag into the single most consequential line in the codebase.

5. **The part not to copy is the billing.** `[FACT]` The BBB profile shows **132 complaints in 12 months, 82 of them billing** — unauthorised recurring charges, cancellation difficulty, refund delays — against a **non-accredited** profile. `[ANALYSIS]` The entry price ($19.99 first month) is a customer-acquisition instrument; the business is made on the **$39.99/month renewal** and the tier upsells ($9.99 / $12.49 / $19.99 / $24.99 / $29.99 in-app). That is a legitimate model executed with enough friction to manufacture its own "is Finelo a scam" search results. Copying the funnel is fine. Copying the friction buys the reputation with it.

6. **The business shape beats the supplement plan on every economic axis, and loses on none except brand equity.** `[DERIVED]` Digital subscription: ~£0 marginal COGS, no inventory, no £80k peak working capital, no MHRA, no whey inflation, no recall exposure. Against it: refunds and chargebacks become the effective COGS line, and you trade FSA/MHRA risk for **FCA/ASA** risk, which is sharper. `[FACT]` Sister app **Coursiv did $1.8M in its first year** (~$250k/month by August 2025) — a real, recent, same-group benchmark for what this funnel does from a standing start. Finelo's own revenue is `[NOT PUBLIC]`.

7. **There is nothing to integrate with.** `[FACT]` No public API, no developer documentation, no documented affiliate or partner programme, no data feed. `[ANALYSIS]` Any plan that involves plugging our bot into Finelo, reselling their content, or earning commission on referrals is dead on arrival. The value here is **informational only** — which is why the recommended spend is $20 and not $200.

---

## ⚠️ If you do sign up, read this first

`[FACT]` Only **finelo.com** is the real product. Search results surface a cluster of lookalike domains — **finelo.ai**, **finelo-ai.com**, **fineloai.digital**, **finelopro.com** — advertising "AI-driven automated trading bots" and "premium AI trading automation." The genuine product is a **simulator that does not connect to a broker and does not trade real money**. Anything promising automated real-money trading under the Finelo name is not Finelo. `[FACT]` Trust-scoring services rate finelo.com highly (88.6) and flag finelo.ai as young and not recommended.

**Practical guardrails:** buy through the App Store or Play Store rather than direct checkout, so cancellation sits in your store subscription list rather than in a support queue. Set a calendar reminder for **day 25** of the 28-day cycle. The refund guarantee is real but conditional, and requests are commonly declined after a renewal has processed.

---

## Documents

| # | File | Contents |
|---|---|---|
| 01 | [`01-company-and-product.md`](01-company-and-product.md) | Corporate structure, founders, the Zimran group, what the app actually contains, the AI feature set, and the contradiction between the marketing site and the product page |
| 02 | [`02-business-model-and-economics.md`](02-business-model-and-economics.md) | Pricing ladder, the quiz→web-to-app funnel, subscriber-count reconciliation, revenue evidence, and the head-to-head against the supplement plan |
| 03 | [`03-reputation-and-risks.md`](03-reputation-and-risks.md) | Trustpilot vs BBB reconciled, the complaint taxonomy, the clone-domain problem, and the UK regulatory position (FSMA s.19/s.21, ASA/CAP, consumer subscription law) |
| 04 | [`04-benefit-to-us.md`](04-benefit-to-us.md) | **The direct answer.** Four benefit vectors scored, and a code-grounded roadmap mapping Finelo's shipped features onto the modules already on `main` |
| 05 | [`05-sources.md`](05-sources.md) | All sources grouped by claim, with source-quality tiering |

---

## Evidence labelling

Same scheme as the supplement research.

| Label | Meaning |
|---|---|
| `[FACT]` | Company statement, store listing, regulator, BBB record, or a named source's published figure |
| `[DERIVED]` | Calculated from `[FACT]` inputs — arithmetic shown |
| `[ESTIMATE]` | A defensible estimate with stated reasoning |
| `[ASSUMPTION]` | A planning input chosen by me; change it and the conclusion may change |
| `[ANALYSIS]` | My commercial judgement |
| `[NOT PUBLIC]` | No adequate evidence exists — deliberately left unfilled |

**On the critical data rule:** Finelo is a private subsidiary of a private group. **Revenue, subscriber count and CAC are not public.** Company-claimed learner numbers are marketing figures and are labelled as such, with their internal inconsistencies shown rather than smoothed over. Third-party review sites citing "1.15 million paid subscribers" are repeating the company's own claim, not verifying it.

---

## Immediate next actions

1. **Do not buy the 12-week plan.** If you want a look inside, buy one month through the App Store, screenshot the AI Bots store and the setup-history screen, and cancel on day 25.
2. **Read [`04-benefit-to-us.md`](04-benefit-to-us.md) first** — it is the only document with an action in it. The other four are the evidence for it.
3. **Build the backtest harness next.** It is now the top item on the roadmap — `DRY_RUN` is accumulating signals into `signals.csv` with nothing to measure them against.
4. **Decide the fork before writing more bot code:** private tool (build whatever you like) vs. product (in which case `DRY_RUN = True` and "no personalisation" become architectural commitments, not defaults).
5. **Do not sign up on any domain other than finelo.com** or the official App Store / Play Store listing.

> **Not legal, financial or investment advice.** This is commercial research. Any productisation of a trading tool in the UK must be checked against current FCA, ASA/CAP and consumer-protection guidance with professional advice before you trade or sell.

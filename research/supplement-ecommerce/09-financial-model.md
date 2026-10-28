# Phases 14 & 15 — Financial Model and the £1M Question

**All figures `[ESTIMATE]` / `[ASSUMPTION]`, £GBP.** "Revenue" is stated **net of VAT** in the P&Ls (the standard for a UK VAT-registered business) and **inc VAT** in the £1M reverse-engineering section (because that is what a store dashboard shows). Both are labelled at every point.

**These are not forecasts. They are a model.** Change three inputs — conversion rate, CAC, repeat rate — and every number changes. The inputs are stated explicitly so you can stress them yourself.

---

## 14.1 Core model inputs

| Input | Conservative | **Base** | Strong | Note |
|---|---|---|---|---|
| Cold-traffic conversion rate | 1.1% | **1.6%** | 2.4% | Not the 6.8% category benchmark — that reflects established brands with returning traffic `[ANALYSIS]` |
| Starting AOV (inc VAT) | £34 | **£46** | £58 | Bundle-driven |
| AOV at month 12 | £38 | **£52** | £66 | |
| CAC month 1 | £95 | **£80** | £62 | New accounts are always inefficient |
| CAC month 12 | £78 | **£52** | £36 | Improves with creative volume + retargeting + affiliate mix |
| Contribution margin (% net rev, before ads) | 47% | **51%** | 55% | |
| Repeat orders as % of total, month 12 | 18% | **34%** | 46% | **The single most important variable** |
| Subscription attach | 12% | **22%** | 32% | |

---

## 14.2 Base case — monthly milestones, Year 1

| | **Month 1** | **Month 3** | **Month 6** | **Month 12** |
|---|---|---|---|---|
| Ad spend | £1,500 | £2,800 | £5,500 | £13,000 |
| CAC | £80 | £70 | £62 | £52 |
| New customers | 19 | 40 | 89 | 250 |
| Repeat orders | 0 | 5 | 30 | 129 |
| **Total orders** | **19** | **45** | **119** | **379** |
| Sessions (@1.6% CVR) | 1,190 | 2,800 | 7,400 | 23,700 |
| AOV (inc VAT) | £46 | £47 | £49 | £52 |
| **Gross revenue (inc VAT)** | **£874** | **£2,115** | **£5,831** | **£19,708** |
| **Net revenue (ex VAT)** | **£728** | **£1,763** | **£4,859** | **£16,423** |
| COGS (27% of net) | £197 | £476 | £1,312 | £4,434 |
| **Gross profit** | **£531 (73%)** | **£1,287** | **£3,547** | **£11,989** |
| Fulfilment + shipping | £156 | £369 | £976 | £3,108 |
| Payment processing | £17 | £42 | £117 | £394 |
| Returns/refunds | £18 | £44 | £121 | £411 |
| **Contribution** | **£340** | **£832** | **£2,333** | **£8,076** |
| Advertising | £1,500 | £2,800 | £5,500 | £13,000 |
| Software (Shopify, email, reviews, apps) | £180 | £220 | £320 | £520 |
| Staff / contractors | £0 | £0 | £400 | £1,600 |
| Other operating (insurance, compliance, accounting) | £280 | £280 | £340 | £480 |
| **EBITDA / operating profit** | **(£1,620)** | **(£2,468)** | **(£4,227)** | **(£7,524)** |
| **Cumulative cash burn** | (£1,620) | (£6,100) | (£19,400) | (£58,000) |

**`[ANALYSIS]` The most important row is the last one.** In the base case, **month 12 loses more money than month 1**, and cumulative burn reaches **~£58,000**. This is not a modelling error — it is the correct and inevitable consequence of a 12-month payback period combined with growth. **Growth consumes cash in this business. The faster you grow, the more you burn.**

This is why the budget-tier analysis in `11-decision.md` matters so much: **a £5,000 or £10,000 budget cannot fund the base-case ramp.** It can only fund a deliberately slower, self-funding version of it.

## 14.3 Three-year P&L, all three cases

### Conservative

| | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Orders | 720 | 2,400 | 4,900 |
| AOV (inc VAT) | £36 | £39 | £42 |
| Gross revenue (inc VAT) | £25,920 | £93,600 | £205,800 |
| **Net revenue** | **£21,600** | **£78,000** | **£171,500** |
| COGS | £6,264 | £22,230 | £47,320 |
| **Gross profit** | £15,336 (71%) | £55,770 (72%) | £124,180 (72%) |
| Fulfilment, shipping, payments, returns | £6,190 | £20,160 | £40,180 |
| **Contribution** | **£9,146** | **£35,610** | **£84,000** |
| Advertising | £22,000 | £48,000 | £86,000 |
| Software + staff + other opex | £7,800 | £18,000 | £34,000 |
| **EBITDA** | **(£20,654)** | **(£30,390)** | **(£36,000)** |
| **Net profit after tax** | **(£20,654)** | **(£30,390)** | **(£36,000)** |

**Verdict: a business that never works.** Losses widen with scale. This is the outcome if repeat rate stalls below ~20% — and it is a genuinely likely outcome, not a strawman.

### Base / realistic

| | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Orders | 1,800 | 6,500 | 15,000 |
| AOV (inc VAT) | £48 | £52 | £56 |
| Gross revenue (inc VAT) | £86,400 | £338,000 | £840,000 |
| **Net revenue** | **£72,000** | **£281,667** | **£700,000** |
| COGS (27% / 26% / 25%) | £19,440 | £73,233 | £175,000 |
| **Gross profit** | £52,560 (73%) | £208,434 (74%) | £525,000 (75%) |
| Fulfilment + shipping | £14,220 | £50,050 | £112,500 |
| Payment processing | £1,730 | £6,760 | £16,800 |
| Returns / refunds | £1,800 | £7,040 | £17,500 |
| **Contribution** | **£34,810** | **£144,584** | **£378,200** |
| Advertising | £34,000 | £96,000 | £212,000 |
| Software | £3,400 | £8,400 | £16,000 |
| Staff / contractors | £4,800 | £22,000 | £68,000 |
| Other opex (insurance, compliance, accounting, testing) | £4,600 | £9,500 | £16,500 |
| **EBITDA** | **(£11,990)** | **£8,684** | **£65,700** |
| EBITDA margin (% net revenue) | −16.7% | 3.1% | **9.4%** |
| **Est. net profit after 25% CT** | **(£11,990)** | **£6,513** | **£49,275** |

**Verdict: a real but modest business.** ~£840k of store revenue in year three, ~£49k of net profit. For comparison: **Huel makes 7.6% net margin at £254m of revenue** `[FACT]`, and Applied Nutrition makes 19.3% operating margin *with its own factory* `[FACT]`. A 9.4% EBITDA margin at £700k net revenue is a credible, unglamorous outcome that is fully consistent with how this industry actually performs.

### Strong

| | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Orders | 3,000 | 13,500 | 36,000 |
| AOV (inc VAT) | £56 | £62 | £68 |
| Gross revenue (inc VAT) | £168,000 | £837,000 | £2,448,000 |
| **Net revenue** | **£140,000** | **£697,500** | **£2,040,000** |
| COGS (26% / 25% / 24%) | £36,400 | £174,375 | £489,600 |
| **Gross profit** | £103,600 (74%) | £523,125 (75%) | £1,550,400 (76%) |
| Fulfilment, shipping, payments, returns | £28,200 | £121,500 | £313,200 |
| **Contribution** | **£75,400** | **£401,625** | **£1,237,200** |
| Advertising | £62,000 | £252,000 | £695,000 |
| Software | £4,200 | £14,000 | £34,000 |
| Staff | £9,600 | £68,000 | £245,000 |
| Other opex | £6,200 | £18,000 | £48,000 |
| **EBITDA** | **(£6,600)** | **£49,625** | **£215,200** |
| EBITDA margin | −4.7% | 7.1% | **10.5%** |

**Verdict: this is what "it worked" looks like.** ~£2.4m of store revenue and ~£215k EBITDA in year three. Note that **even in the strong case, year one loses money.** There is no version of this business that is profitable in year one while growing.

## 14.4 Peak cash requirement — the number that actually decides whether you can do this

`[DERIVED]` from the base-case model:

| | Conservative | **Base** | Strong |
|---|---|---|---|
| Cumulative loss to breakeven | £51,000+ (never breaks even) | **~£58,000** | ~£40,000 |
| Plus inventory investment at peak | £12,000 | **£22,000** | £45,000 |
| **Peak working capital requirement** | **£70,000+** | **~£80,000** | **~£85,000** |
| Month of peak burn | — | **Month 14–16** | Month 10–12 |

**`[ANALYSIS]` This is the most commercially important number in the entire research and it is rarely stated honestly anywhere:** running the base-case plan at full speed requires access to roughly **£80,000** of cash before the business self-funds. Not £10,000. The gap between "what it costs to start" and "what it costs to reach breakeven" is the single largest cause of failure in DTC supplements.

**The mitigation is not more capital — it is a slower, self-funding ramp.** Cap ad spend at a fixed % of trailing 30-day contribution (start at 100%, never exceed 130%), and let growth be limited by cash rather than ambition. This turns a £80k requirement into a £10k–£25k requirement at the cost of 12–18 months of speed. **For a self-funded founder, this is the correct trade and it is the plan recommended in `11-decision.md`.**

---

# PHASE 15 — The £1M Question

## Method

All figures **inc VAT** (store revenue as displayed in Shopify). Ad spend = new customers × CAC. New customers = orders × (1 − repeat share). Contribution = net revenue × contribution margin.

**Two parameter sets are shown, because the answer differs completely between them:**
- **Base parameters:** AOV £48, CAC £55, contribution 51% of net
- **Target parameters:** AOV £55, CAC £40, contribution 55% of net — the operating state you must reach

## Under BASE parameters

| Monthly revenue target | Orders/mo | Repeat share | New customers | Ad spend | Net revenue | Contribution | **Contribution − ads** |
|---|---|---|---|---|---|---|---|
| £10,000 | 208 | 30% | 146 | £8,030 | £8,333 | £4,250 | **(£3,780)** |
| £25,000 | 521 | 40% | 313 | £17,215 | £20,833 | £10,625 | **(£6,590)** |
| £50,000 | 1,042 | 48% | 542 | £29,810 | £41,667 | £21,250 | **(£8,560)** |
| £100,000 | 2,083 | 55% | 937 | £51,535 | £83,333 | £42,500 | **(£9,035)** |
| £250,000 | 5,208 | 62% | 1,979 | £108,845 | £208,333 | £106,250 | **(£2,595)** |

**`[ANALYSIS]` Every single tier is loss-making under base parameters.** The losses narrow as repeat share climbs, but they never turn positive before fixed costs are even considered. **This is the central finding of Phase 15: at a £55 CAC and a £48 AOV, this business does not work at any scale.** Scale is not the solution. It amplifies whatever the unit economics already are.

## Under TARGET parameters — what you must reach

| Monthly revenue target | Orders/mo | Repeat share | New customers | Ad spend | Net revenue | Contribution | Contribution − ads | Fixed costs | **Operating profit** | **Margin** |
|---|---|---|---|---|---|---|---|---|---|---|
| **£10,000** | 182 | 40% | 109 | £4,360 | £8,333 | £4,583 | £223 | £1,100 | **(£877)** | −10.5% |
| **£25,000** | 455 | 50% | 227 | £9,080 | £20,833 | £11,458 | £2,378 | £2,200 | **£178** | 0.9% |
| **£50,000** | 909 | 55% | 409 | £16,360 | £41,667 | £22,917 | £6,557 | £3,800 | **£2,757** | 6.6% |
| **£100,000** | 1,818 | 60% | 727 | £29,080 | £83,333 | £45,833 | £16,753 | £7,500 | **£9,253** | 11.1% |
| **£250,000** | 4,545 | 65% | 1,591 | £63,640 | £208,333 | £114,583 | £50,943 | £17,000 | **£33,943** | 16.3% |

### £1,000,000 annual revenue — the full requirement

`[DERIVED]` £1,000,000 inc VAT = **£833,333 net revenue**

| Requirement | Value |
|---|---|
| **Orders required (year)** | **18,182** (AOV £55) |
| Orders/month at steady state | 1,515 |
| **Repeat share needed** | **58%** |
| **New customers required (year)** | **7,636** |
| **Repeat orders (year)** | 10,546 |
| **Orders per customer per year** | **2.38** |
| Total sessions required @ 2.0% CVR | **909,000/year** (~75,750/month) |
| **CAC** | **£40** |
| **Annual ad spend** | **£305,440** (36.7% of net revenue) |
| Gross margin | 74% |
| **Contribution** | **£458,333 (55% of net)** |
| Contribution after ads | £152,893 |
| Fixed costs (staff, software, insurance, compliance, accounting, testing) | ~£95,000 |
| **EBITDA** | **~£57,900** |
| **Net margin (% of net revenue)** | **~7.0%** |
| **Net margin (% of inc-VAT store revenue)** | **~5.8%** |

### What "£1m revenue" actually means in practice

`[ANALYSIS]` Stripped of romance, hitting £1m/year requires:

- **7,636 new customers acquired in a year** — roughly **21 new customers every single day**, 365 days
- **£305,000 of advertising spend** — meaning you must be comfortable spending **£25,000/month on ads**
- **A 58% repeat-order rate** — which is *above* the 37.7% category benchmark `[FACT]` and requires genuinely excellent retention, not average retention
- **~909,000 website sessions** — about 2,500 a day
- **A creative engine producing enough volume to keep CAC at £40** while spending £25k/month
- **~£58,000 of EBITDA at the end of it** — a **7% net margin** on a business turning over a million pounds

**And that is the *good* outcome.** For calibration: **Huel turns over £254m and makes 7.6% net** `[FACT]`. A 7% net margin at £1m is exactly in line with how this industry actually behaves. It is not a failure of the model; it is the industry.

**The honest conclusion of Phase 15:** £1m of revenue in supplements is achievable and is worth roughly £58k of profit. **The prize is not the profit — it is the asset.** Huel sold for ~€1bn on ~£254m of revenue (~3.9× revenue) `[FACT]`; Applied Nutrition listed on the LSE at £107m of revenue `[FACT]`. **A £1m-revenue, high-retention, subscription-heavy supplement brand is worth substantially more as an asset than as a cash generator.** If you are building this for monthly income, the maths are unattractive. If you are building an asset with a 2–4× revenue exit multiple, the maths are compelling.

**That distinction should drive the go/no-go decision more than any other single consideration.**

---

**Next:** `10-launch-and-content.md` (Phases 16 & 17).

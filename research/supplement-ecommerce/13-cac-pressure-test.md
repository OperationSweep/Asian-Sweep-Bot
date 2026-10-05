# Addendum — CAC Pressure Test

**Purpose:** the entire investment case rests on customer acquisition cost. Every conclusion in `07-unit-economics.md`, `09-financial-model.md` and `11-risks-and-decision.md` survives a ±20% move in COGS and none survives a CAC that stays above ~£100. This document attacks the CAC assumptions directly, using bottom-up channel-cost data rather than the DTC benchmark aggregators the original analysis leaned on.

**Outcome: the base-case CAC assumption survives, but two things I got wrong are corrected below, and one of them changes the recommended launch plan.**

---

## 1. What the original research assumed, and where it came from

| Assumption | Value | Original source | Source quality |
|---|---|---|---|
| Category CAC benchmark | **~$89 (≈£70)** | CommerceCatalyst / Foundry CRO 2026 DTC benchmarks | **Tier 3** — benchmark aggregator |
| Conservative CAC | £75 | Derived from above + new-brand penalty | `[ESTIMATE]` |
| **Base CAC** | **£55** | `[ESTIMATE]` | — |
| Strong CAC | £38 | `[ESTIMATE]` | — |
| CAC trajectory | £80 (M1) → **£52 (M12)** | `[ASSUMPTION]` | — |

**`[ANALYSIS]` The honest criticism of my own work:** the single most load-bearing number in a 30,000-word analysis came from a Tier 3 source — a benchmark aggregator selling a CRO service — and was then adjusted by judgement. That is not good enough for a number this consequential. The rest of this document rebuilds it from channel primitives.

---

## 2. Bottom-up reconstruction from channel costs

CAC is not a benchmark to look up. It is an output:

```
Cost per purchase = (CPM ÷ 1000) ÷ CTR ÷ landing-page CVR
New-customer CAC  = Cost per purchase ÷ (share of purchases that are new customers)
```

### Input data (2026)

| Input | Value | Source | Label |
|---|---|---|---|
| **UK Meta CPM, feed** | **£7.50 – £14.00** | UK ecommerce Meta benchmarks 2026 | `[FACT]` (as published) |
| UK Meta CPC | £0.45 – £1.10 | Same | `[FACT]` (as published) |
| UK Meta CPM (point) | £10.85 | Lebesgue UK 2026 | `[FACT]` (as published) |
| Reels vs feed CPC | **20–35% cheaper** | Same | `[FACT]` (as published) |
| **TikTok CPM** | **$4.80 – $13.26** (Lebesgue broad / Triple Whale ecommerce cohort) | TikTok 2026 benchmarks | `[FACT]` (as published) |
| TikTok CTR platform benchmark | **1.77%** (FY2025 data) | Same | `[FACT]` (as published) |
| TikTok CVR platform benchmark | **2.01%** | Same | `[FACT]` (as published) |
| **Meta cost per purchase, supplements** | **$45.62** vs $30–35 for fashion/pet | Triple Whale ecommerce data | `[FACT]` (as published) |
| **Health & Wellness CPA change YoY** | **+12.6% — the sharpest increase of any vertical** | Same | `[FACT]` (as published) |
| Subscription-model acceptable CPA | $30–$70 | Supplement Meta-ads practitioner sources | `[ESTIMATE]` |
| **UK Meta CPM seasonality** | **+35–60% Sept→Dec**, peaking Black Friday week; **−25–40% in January** vs November peak | UK 2026 benchmarks | `[FACT]` (as published) |

### Reconciling the two conflicting figures

The $45.62 Meta cost-per-purchase and the $89 category CAC look contradictory. **They are not — they measure different things.**

| | Meta cost per purchase ($45.62 ≈ £36) | Blended new-customer CAC ($89 ≈ £70) |
|---|---|---|
| Denominator | All purchases Meta attributes to itself | **New customers only** |
| Includes returning customers | **Yes** | No |
| Attribution | Meta's own 7-day click / 1-day view — systematically over-attributes | Total marketing spend ÷ new customers |
| Includes non-Meta spend | No | Yes (agency, tools, creator seeding, other channels) |

`[DERIVED]` The ratio is **1.95×**, which sits squarely inside the 1.5–2.5× gap normally observed between platform-reported CPA and blended new-customer CAC. **The two sources corroborate each other rather than conflicting.** This materially strengthens the £55–£70 range rather than undermining it.

### Bottom-up CAC by channel

`[DERIVED]` Assuming ~85% of early purchases are new customers (÷0.85 uplift):

| Channel & scenario | CPM | CTR | CVR | Cost/purchase | **New-customer CAC** |
|---|---|---|---|---|---|
| **Meta — bear** | £14.00 | 0.90% | 1.0% | £155.56 | **£183** |
| **Meta — base** | £10.85 | 1.20% | 1.6% | £56.51 | **£66** |
| **Meta — bull** (Reels-weighted) | £7.50 | 1.60% | 2.4% | £19.53 | **£23** |
| **TikTok paid — bear** | £10.00 | 1.00% | 0.9% | £111.11 | **£131** |
| **TikTok paid — base** | £6.24 | 1.50% | 1.2% | £34.67 | **£41** |
| **TikTok paid — bull** | £4.00 | 1.77% | 2.0% | £11.30 | **£13** |

**`[ANALYSIS]` Three observations:**

1. **The base-case blended figure lands at £50–£60**, which validates the original £55 assumption. The bottom-up build and the (corroborating) top-down benchmarks agree.
2. **The spread is enormous — roughly £13 to £183, a 14× range.** The business is excellent at the bull end and dead at the bear end. **CAC is not a number you can assume; it is the thing the first 90 days exists to measure.** This vindicates the pre-committed day-90 kill criteria more than any other single finding.
3. **The dominant term is conversion rate, not media cost.** Moving CVR from 1.0% to 2.4% cuts CAC by 58%; moving CPM from £14 to £7.50 cuts it by 46%. **Landing page and offer work is worth more than media buying skill** — and it is cheaper to fix.

---

## 3. ⚠️ Correction 1 — the CAC trajectory assumption was wrong-signed

**What I assumed:** CAC falls from £80 (M1) to £52 (M12), a 35% improvement.

**What the evidence says:** `[FACT]` **Health & Wellness had the sharpest CPA increase of any vertical at +12.6% year on year**, attributed to supplement and wellness brands flooding the platform.

Two forces act in opposite directions:

| Force | Direction | Magnitude `[ESTIMATE]` |
|---|---|---|
| Learning effects — better creative, better LP, retargeting pools, email capture | **↓ CAC** | −25% to −40% over 12 months |
| Category CPA inflation — more supplement advertisers competing | **↑ CAC** | +10% to +15% per year |
| Meta's removal of lookalike/custom audiences for restricted health ads | **↑ CAC** | +20% to +40% early (see Correction 2) |

**`[DERIVED]` Net expectation: roughly flat to −15% over 12 months, not −35%.**

**Revised trajectory:** £80 (M1) → **£68 (M12)**, not £52.

**Consequence for the model:** the base case in `09-financial-model.md` is optimistic. Rerunning Year 1 at £68 rather than £52 CAC for the second half reduces new customers by ~18% and pushes base-case Year 1 EBITDA from **−£11,990 to roughly −£16,500**, and moves 12-month payback out to **~14 months**. The direction of the conclusion (MODIFY → GO) does not change; the capital requirement and the patience requirement both increase.

---

## 4. 🚨 Correction 2 — the plan cannot exit Meta's learning phase (the most serious finding)

This is a concrete, arithmetic contradiction inside the original model that I did not catch.

`[FACT]` Meta ad sets require approximately **50 optimisation events per ad set per 7 days** to exit the learning phase and deliver stably. Below that threshold, delivery is volatile and CPA is materially higher.

`[DERIVED]` At a £55 CAC optimising for purchases:

```
50 purchases/week × £55 = £2,750/week = £11,930/month — per ad set
```

Now compare against the ad-spend ramp in `09-financial-model.md`:

| | Month 1 | Month 3 | Month 6 | Month 12 |
|---|---|---|---|---|
| Planned ad spend (base case) | £1,500 | £2,800 | £5,500 | £13,000 |
| Weekly equivalent | £346 | £646 | £1,269 | £3,000 |
| Weekly purchases at £55 CAC | 6 | 12 | 23 | 55 |
| **Exits learning phase (≥50/wk)?** | ❌ | ❌ | ❌ | ✅ *(one ad set only)* |

**The plan spends eleven months permanently inside the learning phase — and I simultaneously assumed CAC would fall 35% during exactly that period. Those two assumptions are mutually contradictory.**

This compounds with a restriction already identified in `04-marketing-and-compliance.md`: `[FACT]` Meta's tiered health-ad system **removes custom and lookalike audiences** for restricted health ads, forcing broad targeting — which *increases* the conversion volume the algorithm needs to find the right audience, at exactly the point where we have the least.

### Mitigations, in order of effectiveness

1. **Optimise for a mid-funnel event early.** `[ESTIMATE]` Add-to-cart costs roughly 1/6th of a purchase (~£9). 50 ATC/week ≈ **£450/week ≈ £1,950/month** — achievable from month 2. Switch to purchase optimisation only once spend supports ~£12k/month. **This is the single most important operational change arising from this pressure test.**
2. **One campaign, one ad set, broad.** Ad-set fragmentation is fatal at low budget — each ad set needs its own 50 events. Consolidate ruthlessly.
3. **Lead with TikTok Shop, not Meta, in months 1–6** (see section 5). Creator-driven sales do not depend on Meta's learning phase at all.
4. **Raise AOV to raise conversion value per event** — helps ROAS but *not* the learning phase, which counts events, not value. Do not rely on this.

### Consequence for the budget tiers

This forces a revision to the budget analysis in `11-risks-and-decision.md`:

| Budget | Original verdict | **Revised verdict** |
|---|---|---|
| £2,500 | Too little | Unchanged — too little |
| £5,000 | Organic-first experiment only | **Now explicitly: TikTok Shop + organic only. Meta purchase campaigns are structurally unavailable at this budget** |
| £10,000 | Minimum viable test | **Viable only if Meta runs on mid-funnel optimisation, or is skipped in favour of TikTok Shop** |
| £25,000 | Recommended | **Still recommended — but ad spend should be TikTok-Shop-weighted for months 1–6, with Meta purchase campaigns starting around month 7–9** |
| £50,000 | Best risk-adjusted | Unchanged — this is the only tier that can run Meta purchase optimisation properly from early on |

---

## 5. 💡 Finding — TikTok Shop affiliate is a structurally different (and better) CAC, and the original research under-weighted it

`[FACT]` TikTok Shop UK fee structure: **platform commission 9%** (inclusive of VAT), plus a **seller-set affiliate commission**, typically 5–20% generally and **20–30% for beauty and supplements** to attract high-performing creators.

This is not a cost you can overspend. **Affiliate commission is a variable cost of sale — it cannot produce a CAC you cannot afford, because it is only ever paid on a completed sale.** That is a categorically different risk profile from paid social, where you can spend £10,000 and acquire nobody.

### First-order economics, Foundation Stack £64.99

| Line | Paid social (Meta) | **TikTok Shop affiliate** |
|---|---|---|
| Gross revenue | £64.99 | £64.99 |
| Net revenue (÷1.2) | £54.16 | £54.16 |
| Platform commission (9%) | — | (£5.85) |
| Affiliate commission (20%) | — | (£13.00) |
| CAC / acquisition cost | (£55.00) | — |
| COGS | (£10.50) | (£10.50) |
| Fulfilment + shipping + packaging | (£7.10) | (£7.10) |
| Payment processing | (£1.17) | *(in platform fee)* |
| Returns | (£1.35) | (£1.35) |
| **First-order contribution** | **(£21.56)** | **+£16.36** |

### Same test on a single hero SKU (creatine £29.99), where creator-driven AOV usually sits

| | Affiliate @ 20% | Affiliate @ 30% |
|---|---|---|
| Net revenue | £24.99 | £24.99 |
| Platform commission 9% | (£2.70) | (£2.70) |
| Affiliate commission | (£6.00) | (£9.00) |
| COGS | (£3.20) | (£3.20) |
| Fulfilment + shipping + pack | (£5.95) | (£5.95) |
| Returns | (£0.62) | (£0.62) |
| **First-order contribution** | **+£6.52** | **+£3.52** |

**`[ANALYSIS]` This reframes the whole acquisition strategy:**

- **TikTok Shop is first-order profitable; Meta is not.** Even at a 30% creator commission on a bare single SKU, contribution stays positive. Every Meta first order loses £21–£40.
- **But absolute contribution is small** (£3.52–£16.36). TikTok Shop is a **volume and awareness machine that does not lose money**, not a profit engine.
- **Meta is the profit engine that requires funding upfront**, and only pays back over 12–24 months.
- **The correct structure is therefore sequential, not parallel:** use TikTok Shop to reach first-order breakeven, build reviews, build creator relationships and generate cash; then deploy that cash into Meta once spend can support proper optimisation.

### The honest caveats on TikTok Shop

| Caveat | Consequence |
|---|---|
| Affiliate volume is **not commandable** — you cannot buy it, you must earn creator pick-up | Revenue is unpredictable month to month |
| Sample seeding costs are real (`[ESTIMATE]` £500–£2,000 to seed 50–150 creators) | An upfront cost my model did not include |
| **The customer is semi-owned by TikTok** — limited email capture, weaker subscription conversion | Directly attacks the LTV thesis the whole business depends on |
| AOV is typically lower — creators sell hero SKUs, not £65 bundles | Lower absolute contribution per order |
| Concentration risk on one platform's policy | Already the #2 risk in the register |

**`[ANALYSIS]` This is a genuine weakness in the original research.** I identified TikTok Shop as a mitigation in the risk register and as a channel in the launch sequence, but I built the entire financial model on paid-social CAC. Given that TikTok Shop is **the UK's 4th-largest beauty and wellness retailer** `[FACT]` and produces positive first-order contribution, it should have been modelled as a primary channel, not a supporting one.

---

## 6. ⚠️ Correction 3 — the model has no seasonality, and UK seasonality is large

`[FACT]` UK Meta CPMs rise **35–60% between September and December**, peaking in Black Friday week, and fall **25–40% below the November peak in January**.

`[DERIVED]` A £55 base CAC therefore ranges roughly **£40 in January to £80 in late November** on media cost alone, before any change in creative or competition. That is a ±45% swing my flat-CAC model does not capture.

**Consequences:**
- **Launch timing matters more than the original research implied.** A January–March launch tests the business in the cheapest media window of the year; a Q4 launch tests it in the most expensive and risks producing a false negative on the day-90 kill criteria.
- **The day-90 kill criteria must be seasonally adjusted.** A £70 CAC in November is a materially better result than a £70 CAC in February. Judging a Q4 launch against a flat £65 threshold would kill a viable business.
- **Recommended launch window: January.** `[ANALYSIS]` Cheapest CPMs, strongest health-and-fitness intent of the year, and it puts the day-90 decision point in April with clean data.

---

## 7. What CAC actually kills the business

Using base-case contribution from `07-unit-economics.md` (£54.98 at 12 months, £102.30 at 24 months):

| Blended CAC | 12-mo LTV:CAC | 24-mo LTV:CAC | Verdict |
|---|---|---|---|
| **£25** | 2.20 | **4.09** | Excellent — scale aggressively |
| **£34** | 1.62 | **3.01** | **The target. Healthy 3:1 at 24 months** |
| **£45** | 1.22 | 2.27 | Good. Fundable, scalable |
| **£55** *(base)* | 1.00 | 1.86 | **Viable but thin.** Breakeven at 12 months, real return only in year 2 |
| **£68** *(revised base)* | 0.81 | 1.50 | Marginal. Survives only with tight cost control and strong retention |
| **£85** | 0.65 | 1.20 | Barely covers capital. Not worth the risk or the time |
| **£102** | 0.54 | **1.00** | **Zero return on two years of work.** Hard stop |
| **£130+** | 0.42 | 0.79 | Dead. Every customer destroys capital |

**`[ANALYSIS]` Three conclusions:**

1. **The kill threshold is ~£100 blended CAC at 24-month retention** — not the ~£85 implied by the day-90 criteria. But the day-90 criteria should stay *tighter* than the kill threshold, because month-3 CAC on a new account is measured before retargeting pools, email flows and review social-proof exist. **£85 at day 90 remains the right trip-wire.**
2. **The target is £34, not £55.** A 3:1 LTV:CAC at 24 months is the standard for a fundable, scalable DTC brand. £55 keeps you alive; £34 makes it a business worth building.
3. **CAC alone is not the constraint — CAC ÷ retention is.** At 24-month retention the business tolerates a £100 CAC; at 12-month retention it tolerates £55. **Doubling retention is worth exactly as much as halving CAC, and retention is cheaper to improve.** The original research under-emphasised this: it treated CAC as the villain when the ratio is the real variable.

---

## 8. Revised CAC assumptions

| | Original | **Revised** | Change |
|---|---|---|---|
| Conservative | £75 | **£85** | Worse — reflects learning-phase penalty at low budget |
| **Base** | **£55** | **£62** | Worse — flat-to-rising category CPA, no lookalikes |
| Strong | £38 | **£40** | Broadly unchanged — achievable via TikTok Shop mix |
| Trajectory M1→M12 | £80 → £52 | **£80 → £68** | Materially worse |
| Target for a fundable business | *(not stated)* | **£34 at 24-month retention** | New |
| Kill threshold | ~£85 (implied) | **£85 at day 90; £100 sustained** | Clarified |
| Seasonality | *(none modelled)* | **±45% Jan vs Nov** | New |
| TikTok Shop effective CAC | *(not modelled)* | **29–39% of order value, first-order profitable** | New |

---

## 9. Verdict of the pressure test

**The CAC assumptions broadly survive. The £55 base was defensible and is corroborated by an independent bottom-up build; it should be revised to £62.**

**But three things were wrong, and one of them matters a great deal:**

1. **The learning-phase contradiction is a real flaw.** The plan cannot exit Meta's learning phase until month 12 while simultaneously assuming CAC falls 35% in that window. **Fix: optimise for add-to-cart early, consolidate to one ad set, and lead with TikTok Shop.**
2. **TikTok Shop affiliate was under-weighted.** It is first-order profitable where Meta is not, and it should be the primary channel for months 1–6 — with the caveat that it partially cedes customer ownership, which is a real cost against the LTV thesis.
3. **Seasonality was ignored.** ±45% CAC swing. **Launch in January, and seasonally adjust the day-90 criteria.**

**Does the overall verdict change? No.** MODIFY → GO stands. The revisions make the base case slightly worse, the capital requirement slightly higher, and the timeline slightly longer — but they also surface a channel (TikTok Shop) with structurally better first-order economics than anything in the original plan.

**The most important thing this exercise proved is not a number. It is that CAC has a plausible 14× range across scenarios, and no amount of desk research narrows it further.** The first 90 days of real spend is the only instrument that measures it. That is precisely why the pre-committed kill criteria are the most valuable part of this entire research.

---

## Sources added by this pressure test

- Lebesgue — Facebook Ads CPM by Country, 2026 ecommerce benchmarks: https://lebesgue.io/facebook-ads/facebook-cpm-by-country
- AdLibrary — Meta Ads Average CPC/CPM UK Ecommerce 2026: https://adlibrary.com/posts/meta-ads-average-cpc-cpm-uk-ecommerce
- Adamigo — Meta Ads CPM & CPC Benchmarks by Country 2026: https://www.adamigo.ai/blog/meta-ads-cpm-cpc-benchmarks-by-country-2026
- Lebesgue — TikTok Ads Benchmarks for CTR, CR and CPM (2026 update): https://lebesgue.io/tiktok-ads/tiktok-ads-benchmarks-for-ctr-cr-and-cpm
- Influee — TikTok Ads Benchmarks 2026 (CPA, CPM, CTR, ROAS, CVR by industry): https://influee.co/gb/blog/tiktok-ads-benchmarks
- Triple Whale — Facebook Ad Benchmarks by Industry: https://www.triplewhale.com/blog/facebook-ads-benchmarks
- 27five — Meta Ads Benchmarks for eCommerce 2026: https://www.27five.com/blog/meta-ads-benchmarks-ecommerce-2026/
- Landing Partners — Meta Ads for Supplement Brands: Policy, Claims & ROAS 2026: https://www.landing.partners/blog/meta-ads-supplement-brands-vitamins-advertising-policy
- Flighted — How to Run Meta Ads for Supplement Brands in 2026: https://www.flighted.co/blog/meta-ads-strategy-for-supplement-brands-2026
- **TikTok Shop UK — Platform Commission Fee (9%, incl VAT):** https://seller-uk.tiktok.com/university/essay?knowledge_id=7753824408913665&lang=en-GB
- Hamster Garage — TikTok Shop Affiliate Commission: 2026 Rates, Fees & Payouts: https://www.hamstergarage.com/article/tiktok-shop-affiliate-commission-rates-fees-payouts
- Z Media — TikTok Shop UK Fees Explained: 2026 Seller Cost Breakdown: https://www.z.media/insights/tiktok-shop-fees-uk-2026

**`[ANALYSIS]` Source-quality note:** the channel benchmarks above are Tier 3 aggregators, with one exception — the TikTok Shop 9% commission rate is Tier 1, published by TikTok itself. The Triple Whale figures are better than most because they derive from an actual ad-data platform's aggregated customer accounts rather than from survey or estimate. **Crucially, the bottom-up CAC build and the top-down benchmark agree to within ~15%, from independent methods.** That convergence is what gives the £55–£68 range its credibility — not the authority of any single source.

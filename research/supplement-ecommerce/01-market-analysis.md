# Phase 1 — Global, US, European and UK Supplement Market Analysis

**Evidence labelling used throughout this repository**

| Label | Meaning |
|---|---|
| `[FACT]` | Reported by a company filing, regulator, government source, or a named research house's published figure |
| `[DERIVED]` | Calculated by me from `[FACT]` inputs; the arithmetic is shown |
| `[ESTIMATE]` | A defensible market estimate with stated reasoning, not a published number |
| `[ASSUMPTION]` | A planning input chosen by me; change it and the model changes |
| `[ANALYSIS]` | My commercial judgement/opinion |
| `[NOT PUBLIC]` | No adequate evidence exists; I have deliberately not filled the gap |

**Critical caveat on all market-size numbers below.** Commercial market-research houses (Grand View, Precedence, Fortune Business Insights, Mordor, Future Market Insights, Towards FnB, market.us) publish materially different numbers for the *same* market in the *same* year because they define "supplements" differently (some include functional food and beverage, some include sports nutrition, some include probiotic drinks). Their headline figures are marketing assets for report sales, and their forward CAGRs are systematically optimistic. **Where two sources disagree by more than ~20% I quote the range, not a point estimate, and I do not build the financial model on any of them.** The financial model in `09-financial-model.md` is built bottom-up from UK unit economics, not top-down from market size.

---

## 1.1 Global market size

| Metric | Value | Source | Label |
|---|---|---|---|
| Global dietary supplements market 2025 | **USD 192.6bn – 209.5bn** | Grand View Research, Precedence Research, Zion Market Research (range across houses) | `[FACT]` (as published) |
| Global forecast 2030 | **USD 275bn – 319bn** | Same houses | `[FACT]` (as published) |
| Implied CAGR 2025–2030 | **7.6% – 10.1%** | Same houses | `[FACT]` (as published) |
| Consensus mid-point I will use | **~USD 200bn in 2025, ~7–8% CAGR** | — | `[ESTIMATE]` |

**`[ANALYSIS]`** The honest reading: the global category is very large, growing roughly 2–3× GDP, and is *not* a fad. But "supplements is a $200bn market" is commercially useless to a UK startup. The addressable market for a UK DTC brand is a rounding error against these numbers, and market size has essentially zero explanatory power for whether *your* store succeeds. What matters is UK online-channel size, category-level growth, and paid-social CAC — covered below.

## 1.2 UK market

| Metric | Value | Source | Label |
|---|---|---|---|
| **UK online vitamin & supplement retailing industry revenue 2025-26** | **£1.5bn**, 5-yr CAGR 3.9%, +1.0% growth in 2025-26 | IBISWorld (UK, industry 14644) | `[FACT]` |
| UK adults using supplements | **76%** | IBISWorld, citing UK consumption data | `[FACT]` |
| Total UK VMS + sports nutrition retail (all channels) | **~£2.5bn – £3.5bn** | `[ESTIMATE]` triangulated: H&B UK ~£981m group revenue, THG Nutrition £609m, Bulk ~£123m+, Vitabiotics ~£101m manufacturing, plus grocery/Boots/Amazon/Superdrug own-label | `[ESTIMATE]` |
| UK functional mushroom market 2024 | US$1.85bn → US$4.42bn by 2032 (11.5% CAGR) | Balance Journal citing market research | `[ESTIMATE]` — treat sceptically, this looks inflated relative to observable UK retail |
| UK collagen market 2025 | **USD 583.6m**, 6.78% CAGR to 2035 | Expert Market Research | `[FACT]` (as published) |
| UK marine hydrolysed collagen CAGR 2025–30 | **9.2%** | Grand View Research | `[FACT]` (as published) |
| UK probiotic supplements 2025 | **USD ~596m**, ~7.5% CAGR to 2035 | Future Market Insights | `[FACT]` (as published) |

**The single most important UK number in this document is £1.5bn growing at 1% a year.**

**`[ANALYSIS]`** The UK *online* supplement channel is growing at roughly the rate of inflation, not at the 8–10% the global reports imply. IBISWorld explicitly flags that "growth in online retail has settled" and that customers now comparison-shop across multiple sites before buying. This is a **mature, price-transparent, competitive channel**, not a land grab. Any business plan that assumes a rising tide will carry it is wrong. Growth has to be taken from someone else, or created in a sub-category that is genuinely growing (see 1.4).

## 1.3 US and Europe (relevant only as expansion optionality)

| Market | 2025 size | Growth | Source | Label |
|---|---|---|---|---|
| US dietary supplements | **USD 68.7bn – 78.2bn** | to ~USD 131bn (2033) / ~USD 190bn (2035) | Grand View / Precedence | `[FACT]` (as published) |
| US adult supplement usage | **75%** of Americans; median spend **$50/month** | CRN 2024 Consumer Survey | `[FACT]` |
| US brand loyalty | **71%** of users loyal to their chosen brand | CRN | `[FACT]` |
| Europe dietary supplements | **USD 21.5bn – 28.9bn** (definition-dependent) | ~6–7% CAGR | Expert Market Research / Fortune / Towards FnB | `[FACT]` (as published) |
| Germany | ~USD 10.4bn — largest single European market | — | Towards FnB | `[FACT]` (as published) |
| European category mix | Vitamins & minerals = **51.3%** of European value | Towards FnB | `[FACT]` (as published) |

**`[ANALYSIS]`** The **CRN 71% brand-loyalty and $50/month median spend figures are the two most commercially important data points in this entire section**, and they are from a credible industry association survey rather than a report-selling market research house. They say: (a) supplements are a genuinely habitual, repeat-purchase category — the LTV thesis is real; (b) but incumbents own that loyalty, so the acquisition fight is for switchers and new entrants to the category. Post-Brexit, EU expansion means separate notification regimes, EU-based responsible person, EU VAT/IOSS and duty — it is a **Year 3 question, not a launch question**.

## 1.4 Category-by-category: where growth actually is

| Category | Global size (2025) | Growth | UK relevance | My read |
|---|---|---|---|---|
| **Sports nutrition** | USD 71.6bn `[FACT, Grand View]` → USD 138.5bn by 2033, 8.7% CAGR | High | Very high — UK is a top-3 European sports nutrition market | Large but **brutally commoditised**, and margins are currently being destroyed by whey inflation (see 1.5) |
| **Protein supplements** | USD 29.8bn `[FACT]`, 10.3% CAGR | High | Very high | Avoid as a *launch* product. Input-cost exposure is the problem, not demand |
| **Creatine** | USD 1.4bn `[FACT, Grand View]` → USD 8.7bn by 2033, **26.2% CAGR**; US CAGR 28.3% `[FACT, market.us]` | **Highest of any category researched** | Very high, and broadening beyond gym users | **The standout growth category.** Cheap input, tiny dose, mass-broadening audience |
| **Functional mushrooms** | USD 12.1bn `[FACT, Mordor]`, 9.45% CAGR; Lion's Mane USD 418m, 13.5% CAGR `[FACT, GMI]` | High | Moderate — smaller in UK than the headline reports imply | Good margin, good content, but **claims-restricted** and the "brain fog" angle is where ASA rulings land |
| **Collagen / beauty-from-within** | UK USD 584m `[FACT]`, marine 9.2% CAGR | High | High — marine collagen has overtaken bovine at ~40–45% of value | Strong repeat, strong social, **crowded** |
| **Gut health / probiotics** | UK USD ~596m `[FACT]`, 7.5% CAGR | Medium-high | High | Strong repeat, but **cold-chain/stability and strain-specificity raise the bar** |
| **Sleep / stress** | Part of the ~USD 5bn+ global "mood & sleep" segment `[ESTIMATE]` | High | High | **Melatonin is illegal to sell OTC in GB** — this constrains the category to magnesium/L-theanine/glycine/ashwagandha |
| **Weight management** | Large, but | Being cannibalised by GLP-1 drugs | — | **Avoid.** Banned or heavily restricted on every ad platform. See `04-marketing-and-compliance.md` |
| **GLP-1 companion** | New, emerging | Fastest *new* segment per Vitafoods Europe 2026 coverage | Emerging in UK | **The clearest 2–5 year emerging opportunity.** ~12% of the US population on GLP-1s is already reshaping whey demand `[FACT, Vesper/newhope]` |
| **Healthy ageing** | Growing | Creatine + protein repositioned for over-45s | Emerging | Underserved and **very** underserved in advertising |
| **Women's health (perimenopause, hormonal)** | Growing fast | "Outperforming general wellness" per 2026 trend coverage | High | Underserved; high trust barrier; high LTV |
| **Joint/bone** | Mature | Low single digit | High (ageing population) | Low social suitability |
| **Everyday vitamins/minerals** | 51% of European value `[FACT]` | Low | Very high | **Where the money is, and where the margin isn't.** Boots/Tesco/Amazon own-label crush price |

## 1.5 The margin story — and the warning inside it

| Data point | Value | Source | Label |
|---|---|---|---|
| Applied Nutrition plc FY2025 gross margin | **46.7%** | Applied Nutrition FY25 results | `[FACT]` |
| Applied Nutrition FY2025 revenue / operating profit | **£107.1m / £20.7m** (19.3% operating margin) | Same | `[FACT]` |
| Holland & Barrett FY2025 gross margin | £579.9m / £981m = **59.1%** | H&B FY25 announcement | `[DERIVED]` |
| Glanbia Performance Nutrition FY2025 EBITDA margin | **13.0%**, down 380bps | Glanbia FY25 | `[FACT]` |
| WPC cost increase over 2 years | **+108%**; WPI **+139%** | Vesper Tool / industry | `[FACT]` |
| Huel FY2025 (YE 31 Jul 2025) | Revenue **£254m** (+19%), PBT **£19.4m** (7.6% net) | Companies House filing via The Grocer | `[FACT]` |

**`[ANALYSIS]` — read these five rows together, they tell the whole story:**

1. A **vertically integrated, factory-owning UK manufacturer** (Applied Nutrition) runs 46.7% gross and 19.3% operating margin. That is the realistic ceiling for a *product* business at scale.
2. A **retailer with 809 stores and huge own-label** (H&B) runs 59% gross — but it took £124m of owner investment in one year to get 11% growth.
3. A **branded protein giant** (Glanbia) had its EBITDA margin collapse 380bps *purely on whey input inflation*, despite growing volume double digits.
4. **Huel, the best-run UK DTC nutrition business of the last decade, makes 7.6% net margin at £254m of revenue** — and sold to Danone for ~€1bn rather than keep grinding.

The conclusion is uncomfortable and important: **supplements are a high-gross-margin, low-net-margin business.** The 70–80% gross margins quoted in every "start a supplement brand" YouTube video are real at the COGS line and evaporate at the CAC line. Everything in this research turns on whether we can acquire a customer for less than their first-year gross profit.

## 1.6 Ecommerce penetration, subscription and repeat behaviour

| Metric | Value | Source | Label |
|---|---|---|---|
| Supplements DTC repurchase rate | **37.7%** (up from 33.1%) | CommerceCatalyst / Foundry CRO 2026 benchmarks | `[FACT]` (as published, third-party benchmark) |
| Supplement DTC CAC | **~$89 per new customer — highest of any DTC category measured** | Same | `[FACT]` (as published) |
| Vitamin/multivitamin sub-category CAC | **$45–$80** | Same | `[FACT]` (as published) |
| Subscription LTV, vitamins | **$300–$600** | Same | `[FACT]` (as published) |
| Subscription LTV, premium greens (AG1 class) | **$600–$1,200** | Same | `[FACT]` (as published) |
| Personal care & supplements site conversion rate | **~6.8%** (well above the 1.4–1.8% Shopify average) | Champion Bio 2025 via DTC benchmark aggregators | `[FACT]` (as published) — **I treat this as optimistic; see below** |
| H&B digital sales FY2025 | **£249.4m, +20% YoY** | H&B FY25 | `[FACT]` |
| TikTok Shop UK position | **4th-largest UK beauty & wellness retailer**; 55% of users purchase after seeing a product in video | TikTok Newsroom / BeautyMatter | `[FACT]` (platform-published, treat as promotional) |
| TikTok Shop Health & Wellness share of global GMV | **~9% (~$3.0bn)**, 4.5–5.8% conversion rate | TikTok Shop statistics aggregators | `[ESTIMATE]` |

**`[ANALYSIS]` on the 6.8% conversion figure:** that number reflects established brands with returning-customer traffic and branded search. **A cold-traffic paid-social landing page for an unknown UK supplement brand will convert at 1.0–2.5%, not 6.8%.** I use 1.6% (base case) in the financial model. If you build the model on 6.8% you will build a fantasy. This is the single most common way supplement business plans lie to their authors.

**`[ANALYSIS]` on the $89 CAC:** converted at ~£0.78/$ that is roughly **£70 CAC** for a UK supplement customer. Against a typical £30 AOV at 65% gross margin, first-order gross profit is £19.50. **The first order loses ~£50.** This is the central economic fact of the entire business: *supplements are not a first-order-profitable category on paid social; they are a subscription/repeat business or they are nothing.* Every strategic recommendation downstream flows from this.

## 1.7 Consumer demographics

`[FACT]` (CRN 2024, IBISWorld): 75–76% of UK/US adults use supplements. Usage rises with age; spend concentrates in 35–64. `[ANALYSIS]` For paid social specifically the commercially interesting cohorts are:

- **Men 18–34, gym-adjacent** — cheapest CPMs, highest content velocity, lowest loyalty, most price-sensitive, highest competition. Good for volume, bad for margin.
- **Women 25–45, wellness/beauty** — higher AOV, much higher subscription take-up, strong Instagram/TikTok fit, higher CAC, better LTV.
- **Adults 45–65, healthy ageing** — **the best LTV/CAC ratio available and the least contested on TikTok/Reels.** Under-targeted because agencies default to the young gym audience. Meta remains the right platform here, not TikTok.

## 1.8 Where the strongest opportunities appear to exist — Phase 1 verdict

**`[ANALYSIS]`** Ranked by *opportunity for a new UK entrant*, not by market size:

1. **Creatine and the creatine-adjacent stack** — 26%+ category CAGR, £2–£4 COGS, audience broadening from gym-bro to women/over-45s/cognitive. The only category where both growth and margin are strong simultaneously.
2. **Healthy-ageing / GLP-1 companion (protein-sparing, electrolytes, fibre, creatine)** — genuine emerging demand, almost no UK DTC brand owns this positioning yet.
3. **Women's performance & perimenopause** — high LTV, high trust premium, underserved, strong subscription mechanics.
4. **Sleep & stress (magnesium/L-theanine/glycine/ashwagandha — NOT melatonin)** — universal problem, cheap COGS, excellent content, but claims are the tightest of any category.
5. **Functional mushrooms** — good margin and content, but decelerating novelty and elevated ASA risk on cognition claims.

**Avoid:** weight management (ad-banned), whey protein as a launch SKU (input-cost exposure), generic multivitamins (own-label price floor), anything requiring a Novel Foods authorisation.

---

**Sources:** see `12-sources.md`.

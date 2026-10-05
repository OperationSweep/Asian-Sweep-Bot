# Phases 2 & 3 — The 60-Product Commercial Database

## How to read this file

The Phase 3 brief asked for 28 fields per product. A single 28-column table is unreadable, so the database is split into **four linked tables** covering the same 60 products in the same order:

- **Table A — Demand:** what it is, what people buy it for, market size, growth, competition, search/social interest
- **Table B — Economics:** UK retail price, unit size, estimated COGS, ecommerce gross margin, repeat/replenishment
- **Table C — Channel & risk:** TikTok/Instagram/Facebook potential, subscription fit, regulatory complexity, private label, dropship, **opportunity score /100**
- **Table D — Companies & the revenue-attribution problem:** leading brands and manufacturers, with company revenue where verified

### The critical data rule, applied honestly

**`[NOT PUBLIC]` — Product-level revenue and product-level margin do not exist as public data for essentially any supplement ingredient.**

Public companies report at group or segment level. Glanbia reports "Performance Nutrition"; it does **not** report "revenue from creatine". THG reports "THG Nutrition"; it does not report "revenue from Vitamin D3". Applied Nutrition reports a group gross margin of 46.7%; it does not report gross margin by SKU. Holland & Barrett is private and reports group revenue only.

Therefore, in Table D:
- **Company revenue is `[FACT]`** where it comes from a filing or results announcement.
- **Category attribution is `[NOT PUBLIC]` or `[ESTIMATE]` with the derivation shown** — never presented as if it were the company's own disclosure.
- The one meaningful exception found in this research: **Glanbia disclosed that Optimum Nutrition represented 75% of Performance Nutrition revenue in FY2025 `[FACT]`**, which permits a genuine `[DERIVED]` brand-level figure. That is the standard; nothing else in this document dresses company revenue up as product revenue.

### Basis of the COGS estimates

All COGS figures are **`[ESTIMATE]`** for **UK private-label, landed, finished-goods cost including bottle/pouch, label, and inbound freight, at a 1,000–5,000 unit first order**, based on published UK contract-manufacturer indicative pricing and standard ingredient economics. They are planning inputs. **You must replace every one of them with a real quote before committing capital** — see `06-business-models-and-suppliers.md` for the RFQ process.

All retail prices are **UK, VAT-inclusive** (supplements are standard-rated at 20% — see `05-uk-regulation.md`), and reflect the mid-market DTC price point, not the Amazon price floor and not the premium-brand ceiling.

**Ecommerce gross margin** in Table B = (net-of-VAT selling price − COGS) ÷ net-of-VAT selling price. It **excludes** fulfilment, shipping, payment fees and CAC. It is not profit.

---

## Table A — Demand

| # | Product | Category | Bought for | Category size & growth | Search / social interest | Competition |
|---|---|---|---|---|---|---|
| 1 | Multivitamin (adult) | Everyday | "Insurance policy" nutrition | Largest single VMS line; V&M = 51.3% of European value `[FACT]` | Very high, flat | **Very High** |
| 2 | Vitamin D3 (+K2) | Everyday | Immunity, bones, winter deficiency | Core UK line; NDNS shows persistent UK deficiency `[FACT]` | High, seasonal (Oct–Feb spike) | **Very High** |
| 3 | Vitamin C | Everyday | Immunity | Mature, low growth | High, seasonal | **Very High** |
| 4 | Vitamin B12 | Everyday | Energy, vegan diets | Growing with plant-based diets | Medium-high | High |
| 5 | B-Complex | Everyday | Energy, stress | Stable | Medium | High |
| 6 | Magnesium (glycinate/citrate) | Everyday / Sleep | Sleep, cramps, stress, fatigue | **Fast-growing** — the breakout mineral of 2023–26 | **Very high, still rising** | High |
| 7 | Zinc | Everyday | Immunity, skin, "male health" | Stable | Medium | High |
| 8 | Iron (bisglycinate) | Everyday | Fatigue, women's health, vegan | Stable-growing | Medium | Medium-high |
| 9 | Calcium | Everyday | Bone health | Mature, declining in DTC | Low | Medium |
| 10 | Omega-3 fish oil | Everyday | Heart, brain, joints | Very large, mature | High | **Very High** |
| 11 | Algal Omega-3 (vegan) | Everyday | As above, plant-based | Small but growing fast | Medium | Medium |
| 12 | Ashwagandha (KSM-66/Sensoril) | Herbal | Stress, sleep, "cortisol" | **One of the "Big Four of 2026"** `[FACT, trade press]` | **Very high** | High |
| 13 | Lion's Mane | Mushroom | Focus, "brain fog", memory | USD 418m (2024), 13.5% CAGR `[FACT, GMI]` | Very high, plateauing | High |
| 14 | Reishi | Mushroom | Sleep, calm, immunity | Part of USD 12.1bn functional mushroom mkt `[FACT]` | Medium | Medium |
| 15 | Cordyceps | Mushroom | Energy, endurance | Growing | Medium | Medium |
| 16 | Turkey Tail | Mushroom | Gut/immune | Small | Low-medium | Low |
| 17 | Maca | Herbal | Energy, libido, hormonal | Stable | Medium | Medium |
| 18 | Turmeric / curcumin | Herbal | Joints, inflammation | Very large, mature | High | **Very High** |
| 19 | Panax ginseng | Herbal | Energy, cognition | Stable | Medium | Medium |
| 20 | Rhodiola rosea | Herbal | Stress, fatigue, endurance | Growing | Medium | Medium |
| 21 | Milk thistle | Herbal | Liver, "after a night out" | Stable | Medium | Medium |
| 22 | Saffron extract | Herbal | Mood, appetite | Small, growing | Low-medium | Low |
| 23 | **Creatine monohydrate (powder)** | Sports | Strength, muscle, **now cognition & healthy ageing** | **USD 1.4bn 2025 → 8.7bn 2033, 26.2% CAGR `[FACT, Grand View]`; US 28.3% CAGR `[FACT, market.us]`** | **Extremely high and rising — best in class** | High but **demand is outrunning it** |
| 24 | Creatine gummies | Sports | Same, convenience format | Explosive on TikTok Shop (1m+ units on single listings) `[FACT, TikTok Shop]` | **Very high** | Medium-high, rising fast |
| 25 | Whey protein (concentrate/blend) | Sports | Muscle, protein target | USD 29.8bn protein mkt, 10.3% CAGR `[FACT]` | Very high | **Extreme** |
| 26 | Plant/vegan protein | Sports | As above, plant-based | Growing above category | High | High |
| 27 | Clear whey isolate | Sports | Light/refreshing protein format | Fast-growing niche | High | Medium-high |
| 28 | Collagen peptides (bovine) | Beauty/Joint | Skin, hair, joints | UK collagen USD 584m, 6.8% CAGR `[FACT]` | Very high | **Very High** |
| 29 | Pre-workout | Sports | Energy, focus, pump | Large, mature | Very high | **Very High** |
| 30 | **Electrolytes** | Sports/Wellness | Hydration, energy, hangover, **GLP-1 side effects** | Fast-growing; LMNT/Liquid IV created the category | **Very high** | Medium-high |
| 31 | BCAA | Sports | Recovery (largely superseded by EAA) | **Declining** | Declining | High |
| 32 | EAA | Sports | Recovery, MPS | Growing | Medium | Medium |
| 33 | L-Citrulline | Sports | Pump, blood flow | Niche, stable | Medium | Low-medium |
| 34 | Beta-alanine | Sports | Endurance, "the tingle" | Niche, stable | Medium | Low-medium |
| 35 | Glutamine | Sports | Recovery, gut | Declining (weak evidence) | Low | Medium |
| 36 | Probiotics (multi-strain) | Gut | Digestion, bloating, immunity | UK USD ~596m, 7.5% CAGR `[FACT]`; multi-strain +67% 2020–23 `[FACT]` | Very high | **Very High** |
| 37 | Prebiotics (inulin/GOS) | Gut | Feed gut bacteria | Growing | Medium | Medium |
| 38 | Psyllium husk / fibre | Gut | Regularity, satiety, **GLP-1 companion** | Growing sharply | **Rising fast** | Low-medium |
| 39 | CoQ10 / ubiquinol | Wellness | Heart, energy, statin users | Stable, ageing-driven | Medium | Medium-high |
| 40 | NAC | Wellness | Liver, antioxidant, respiratory | Growing | Medium | Medium |
| 41 | L-Theanine | Sleep/Focus | Calm focus, pairs with caffeine | Growing | Medium-high | Low-medium |
| 42 | Glycine | Sleep | Sleep quality | Growing from small base | Medium | **Low** |
| 43 | Glucosamine | Joint | Joint comfort | Mature, ageing-driven | Medium | Medium-high |
| 44 | Chondroitin | Joint | Joint comfort (usually with glucosamine) | Mature | Low | Medium |
| 45 | Vitamin K2 (MK-7) | Everyday | Bone/heart, pairs with D3 | Growing | Medium | Medium |
| 46 | Hair, Skin & Nails formula | Beauty | Appearance | Large, mature | High | **Very High** |
| 47 | Biotin | Beauty | Hair/nails | Mature, commoditised | Medium | High |
| 48 | Marine collagen | Beauty | Skin, premium positioning | **Marine now 40–45% of collagen value, up from 30% in 2020 `[FACT]`; UK 9.2% CAGR `[FACT]`** | Very high | High |
| 49 | Hyaluronic acid (oral) | Beauty | Skin hydration | Growing | Medium-high | Medium |
| 50 | Greens powder | Wellness | "Nutritional insurance", convenience | AG1 built ~USD 600m/yr on one SKU `[FACT, Forbes]` | Very high | **Very High** |
| 51 | Sea moss | Wellness | "Minerals", social-media driven | Volatile, trend-led | High but faddish | Medium |
| 52 | **Colostrum (bovine)** | Emerging | Gut, immunity, recovery | **"Big Four of 2026"** `[FACT, trade press]` | **Very high, rising** | Medium — **still open in UK** |
| 53 | Shilajit | Emerging | Energy, "male vitality" | **819% trend momentum on TikTok Shop `[FACT, TikTok trend data]`** | Very high | Medium — **but see risk note** |
| 54 | Tart cherry | Sleep/Recovery | Sleep, muscle soreness | Growing | Medium | Low-medium |
| 55 | Beetroot nitrate | Sports | Endurance, blood flow | Growing | Medium | Low-medium |
| 56 | Apigenin | Sleep | Sleep (Huberman-driven) | Small, growing | Medium (podcast-driven) | **Low** |
| 57 | Berberine | Metabolic | Blood sugar, metabolic health | Growing — **but claim-toxic** | High | Medium |
| 58 | Taurine | Wellness | Energy, ageing (2023 Science paper) | Growing | Medium | **Low** |
| 59 | Myo-inositol | Women's | PCOS, cycle, mood | Growing fast | Medium-high | **Low-medium** |
| 60 | Lutein / zeaxanthin | Eye | Screen fatigue, eye health | Growing, ageing + screens | Medium | Low-medium |

---

## Table B — Economics (UK, GBP, VAT-inclusive retail)

`[ESTIMATE]` throughout unless marked. GM% = (net-of-VAT price − COGS) ÷ net-of-VAT price.

| # | Product | Typical UK retail (inc VAT) | Typical unit | Est. private-label COGS | Ecom gross margin | Repeat potential | Replenishment |
|---|---|---|---|---|---|---|---|
| 1 | Multivitamin | £12–£20 | 60–90 caps | £1.40–£2.60 | 72–80% | High | 60–90 days |
| 2 | Vitamin D3+K2 | £10–£18 | 90–120 caps | £0.90–£1.80 | 78–86% | High | 90–120 days |
| 3 | Vitamin C | £8–£14 | 60–120 caps | £0.80–£1.60 | 76–84% | Medium | 60–90 days |
| 4 | Vitamin B12 | £9–£16 | 60–90 caps | £0.90–£1.70 | 76–85% | High | 60–90 days |
| 5 | B-Complex | £10–£18 | 60–90 caps | £1.20–£2.20 | 74–82% | Medium-high | 60–90 days |
| 6 | **Magnesium glycinate** | £15–£26 | 90–120 caps | £2.20–£3.80 | 70–78% | **High** | 45–60 days |
| 7 | Zinc | £8–£13 | 90–120 caps | £0.70–£1.40 | 78–86% | Medium | 90–120 days |
| 8 | Iron bisglycinate | £10–£16 | 60–90 caps | £1.00–£2.00 | 76–84% | High | 60–90 days |
| 9 | Calcium | £8–£13 | 60–90 tabs | £0.90–£1.70 | 74–82% | Medium | 60–90 days |
| 10 | Omega-3 | £14–£25 | 60–120 softgels | £2.20–£4.50 | 66–76% | High | 60–90 days |
| 11 | Algal Omega-3 | £22–£35 | 60 softgels | £5.00–£8.50 | 58–70% | High | 60 days |
| 12 | **Ashwagandha KSM-66** | £16–£28 | 60–90 caps | £2.20–£4.20 | 70–80% | High | 45–60 days |
| 13 | Lion's Mane | £18–£32 | 60–90 caps | £2.80–£5.50 | 66–78% | Medium-high | 45–60 days |
| 14 | Reishi | £16–£28 | 60 caps | £2.50–£4.80 | 66–78% | Medium | 60 days |
| 15 | Cordyceps | £16–£28 | 60 caps | £2.50–£4.80 | 66–78% | Medium | 60 days |
| 16 | Turkey Tail | £16–£28 | 60 caps | £2.50–£4.80 | 66–78% | Low-medium | 60 days |
| 17 | Maca | £12–£20 | 100g–200g | £1.60–£3.00 | 72–80% | Medium | 45–60 days |
| 18 | Turmeric/curcumin | £12–£22 | 60–90 caps | £1.60–£3.20 | 72–80% | Medium-high | 60 days |
| 19 | Ginseng | £14–£24 | 60 caps | £2.00–£3.80 | 70–80% | Medium | 60 days |
| 20 | Rhodiola | £14–£24 | 60 caps | £2.00–£3.80 | 70–80% | Medium | 60 days |
| 21 | Milk thistle | £10–£18 | 60–90 caps | £1.20–£2.40 | 74–82% | Medium | 60–90 days |
| 22 | Saffron extract | £18–£30 | 30–60 caps | £3.50–£6.50 | 60–72% | Medium | 30–60 days |
| 23 | **Creatine monohydrate** | £16–£30 | **250g–500g (50–100 servings)** | **£2.20–£4.50** | **72–82%** | **High** | **50–90 days** |
| 24 | Creatine gummies | £20–£32 | 60–90 gummies | £4.00–£7.00 | 60–72% | High | 30–45 days |
| 25 | Whey protein | £22–£40 | 1kg | **£9.00–£15.00 and rising `[FACT: WPC +108% in 2 yrs]`** | **40–58% and falling** | High | 30 days |
| 26 | Plant protein | £22–£38 | 1kg | £7.00–£11.00 | 50–64% | High | 30 days |
| 27 | Clear whey | £26–£40 | 500g–1kg | £9.00–£14.00 | 44–58% | High | 30 days |
| 28 | Collagen peptides | £20–£35 | 300g | £4.50–£8.00 | 60–72% | High | 30–45 days |
| 29 | Pre-workout | £22–£38 | 300–400g | £4.00–£7.50 | 62–74% | High | 30–45 days |
| 30 | **Electrolytes** | £18–£30 (sticks) | **30 sticks** | **£3.00–£6.00** | **66–78%** | **Very High** | **30 days** |
| 31 | BCAA | £16–£28 | 250–500g | £3.50–£6.50 | 60–72% | Medium | 45 days |
| 32 | EAA | £20–£32 | 250–400g | £4.50–£8.00 | 58–70% | Medium-high | 45 days |
| 33 | L-Citrulline | £14–£24 | 250g | £2.20–£4.00 | 70–80% | Medium | 45–60 days |
| 34 | Beta-alanine | £12–£20 | 250g | £1.80–£3.20 | 72–82% | Medium | 45–60 days |
| 35 | Glutamine | £12–£20 | 250–500g | £2.20–£4.00 | 70–78% | Low-medium | 45–60 days |
| 36 | Probiotics | £20–£35 | 30–60 caps | £3.50–£7.00 | 62–74% | **High** | 30–60 days |
| 37 | Prebiotics | £14–£24 | 200–300g | £2.00–£3.80 | 72–80% | High | 30–45 days |
| 38 | **Psyllium/fibre** | £12–£20 | 300–500g | £1.60–£3.00 | 74–82% | **High** | 30–45 days |
| 39 | CoQ10 | £16–£30 | 60 caps | £3.00–£6.00 | 62–74% | High | 60 days |
| 40 | NAC | £12–£22 | 60–90 caps | £1.60–£3.20 | 72–82% | Medium | 60 days |
| 41 | L-Theanine | £12–£20 | 60–90 caps | £1.50–£2.80 | 74–82% | Medium-high | 45–60 days |
| 42 | Glycine | £10–£18 | 250–500g | £1.40–£2.60 | 74–84% | Medium-high | 45–60 days |
| 43 | Glucosamine | £12–£22 | 90–120 tabs | £1.80–£3.50 | 72–80% | High | 60–90 days |
| 44 | Chondroitin | £14–£24 | 90 tabs | £2.40–£4.50 | 68–78% | High | 60–90 days |
| 45 | Vitamin K2 MK-7 | £14–£24 | 60–90 caps | £2.00–£4.00 | 68–80% | High | 60–90 days |
| 46 | Hair/Skin/Nails | £16–£28 | 60 caps | £2.20–£4.20 | 70–80% | High | 30–60 days |
| 47 | Biotin | £8–£14 | 90–120 caps | £0.70–£1.50 | 78–86% | Medium | 90 days |
| 48 | **Marine collagen** | £25–£45 | 300g | £6.50–£11.00 | 56–68% | High | 30–45 days |
| 49 | Hyaluronic acid | £16–£28 | 60 caps | £2.50–£5.00 | 66–78% | High | 60 days |
| 50 | Greens powder | £30–£60 (AG1 £79+) | 30 servings | £6.00–£12.00 | 62–76% | **Very High** | **30 days** |
| 51 | Sea moss | £14–£28 | 60 caps / gel | £2.20–£5.00 | 66–80% | Medium | 45 days |
| 52 | **Colostrum** | £30–£50 | 200–300g | £8.00–£14.00 | 56–68% | High | 30–45 days |
| 53 | Shilajit | £20–£40 | 30–60g resin | £3.50–£8.00 | 62–78% | Medium-high | 45–60 days |
| 54 | Tart cherry | £16–£26 | 60 caps | £2.50–£4.50 | 68–78% | Medium-high | 45–60 days |
| 55 | Beetroot nitrate | £16–£26 | 300g | £2.80–£5.00 | 66–78% | Medium | 45 days |
| 56 | Apigenin | £16–£26 | 60 caps | £2.50–£4.80 | 66–78% | Medium-high | 60 days |
| 57 | Berberine | £18–£30 | 60 caps | £3.00–£5.50 | 64–76% | High | 30–60 days |
| 58 | Taurine | £10–£18 | 250–500g | £1.20–£2.40 | 76–84% | Medium | 60 days |
| 59 | **Myo-inositol** | £18–£30 | 200–400g | £2.80–£5.00 | 66–78% | **High** | 30–45 days |
| 60 | Lutein/zeaxanthin | £14–£24 | 60–90 caps | £2.20–£4.20 | 68–78% | High | 60–90 days |

**`[ANALYSIS]` The single most important pattern in Table B:** capsule-format micronutrients have the *highest* gross margin percentage but the *lowest* absolute gross profit per order (£10–£16). Powder-format actives (creatine, electrolytes, collagen, greens) have *lower* percentage margin but *higher* absolute gross profit per order (£16–£35) and shorter replenishment cycles. **At a £50–£70 CAC, absolute gross profit per order is what matters, not percentage margin.** This is why a £12 vitamin C bottle can never be a paid-social hero product and a £35 stack can.

---

## Table C — Channel, risk and opportunity score

Score /100 is my weighted composite `[ANALYSIS]` using the Phase 4 factor set (weights in `03-ranking-and-shortlist.md`). Regulatory complexity is GB-specific.

| # | Product | TikTok | Instagram | Facebook | Subscription | Reg. complexity | Private label | Dropship practical | **Score /100** |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Multivitamin | Low | Low | Medium | High | Low | Universal | Yes | 44 |
| 2 | Vitamin D3+K2 | Medium | Low | **High** | High | Low | Universal | Yes | 58 |
| 3 | Vitamin C | Low | Low | Medium | Medium | Low | Universal | Yes | 34 |
| 4 | Vitamin B12 | Medium | Medium | Medium | High | Low | Universal | Yes | 47 |
| 5 | B-Complex | Low | Low | Medium | Medium | Low | Universal | Yes | 38 |
| 6 | **Magnesium glycinate** | **High** | **High** | **High** | High | Low | Universal | Yes | **82** |
| 7 | Zinc | Low | Low | Medium | Medium | Low | Universal | Yes | 36 |
| 8 | Iron bisglycinate | Medium | Medium | Medium | High | Low-med | Universal | Yes | 50 |
| 9 | Calcium | Low | Low | Low | Medium | Low | Universal | Yes | 26 |
| 10 | Omega-3 | Low | Medium | **High** | High | Low | Universal | Yes | 52 |
| 11 | Algal Omega-3 | Medium | Medium | Medium | High | Low | Wide | Yes | 49 |
| 12 | **Ashwagandha** | **High** | **High** | Medium | High | **Medium** ⚠ | Universal | Yes | **74** |
| 13 | Lion's Mane | **High** | High | Medium | Medium-high | **Medium-High** ⚠ | Wide | Yes | 68 |
| 14 | Reishi | Medium | Medium | Low | Medium | Medium | Wide | Yes | 51 |
| 15 | Cordyceps | Medium-high | Medium | Low | Medium | Medium | Wide | Yes | 54 |
| 16 | Turkey Tail | Low | Low | Low | Low-med | Medium | Wide | Yes | 38 |
| 17 | Maca | Medium | Medium | Low | Medium | **Medium-High** ⚠ (libido claims) | Wide | Yes | 46 |
| 18 | Turmeric | Medium | Medium | High | Medium-high | **Medium** ⚠ | Universal | Yes | 55 |
| 19 | Ginseng | Low | Low | Medium | Medium | Medium | Wide | Yes | 42 |
| 20 | Rhodiola | Medium | Medium | Medium | Medium | Medium | Wide | Yes | 50 |
| 21 | Milk thistle | Medium | Low | Medium | Medium | **Medium** ⚠ (liver claims) | Wide | Yes | 44 |
| 22 | Saffron | Medium | Medium | Low | Medium | **High** ⚠ (mood claims) | Narrow | Limited | 40 |
| 23 | **Creatine monohydrate** | **Very High** | **High** | **High** | **High** | **Low** ✅ | Universal | Yes | **91** |
| 24 | **Creatine gummies** | **Very High** | **High** | Medium | High | Low | Growing | Yes | **80** |
| 25 | Whey protein | High | High | High | Very High | Low | Universal | Yes | 55 (margin-capped) |
| 26 | Plant protein | Medium-high | High | Medium | Very High | Low | Universal | Yes | 58 |
| 27 | Clear whey | High | High | Medium | High | Low | Wide | Yes | 57 |
| 28 | Collagen peptides | High | **Very High** | High | High | Medium | Universal | Yes | 69 |
| 29 | Pre-workout | **Very High** | High | Medium | High | **Medium** ⚠ (stimulants) | Universal | Yes | 63 |
| 30 | **Electrolytes** | **Very High** | **High** | Medium-high | **Very High** | **Low** ✅ | Wide | Yes | **86** |
| 31 | BCAA | Low | Medium | Medium | Medium | Low | Universal | Yes | 36 |
| 32 | EAA | Medium | Medium | Medium | High | Low | Wide | Yes | 48 |
| 33 | L-Citrulline | Medium | Medium | Low | Medium | Low | Wide | Yes | 46 |
| 34 | Beta-alanine | Medium-high | Medium | Low | Medium | Low | Wide | Yes | 48 |
| 35 | Glutamine | Low | Low | Low | Low-med | Low | Wide | Yes | 30 |
| 36 | Probiotics | High | High | High | **Very High** | **Medium** ⚠ ("probiotic" is itself a restricted claim) | Wide | Care needed (stability) | 65 |
| 37 | Prebiotics | Medium-high | Medium | Medium | High | Medium | Wide | Yes | 56 |
| 38 | **Psyllium/fibre** | **High** | Medium | Medium | **High** | Low | Universal | Yes | **70** |
| 39 | CoQ10 | Low | Low | **High** | High | Medium | Wide | Yes | 51 |
| 40 | NAC | Medium | Low | Medium | Medium | **Medium** ⚠ | Wide | Yes | 45 |
| 41 | **L-Theanine** | High | High | Medium | Medium-high | Low | Wide | Yes | **66** |
| 42 | Glycine | Medium-high | Medium | Low | Medium | Low | Wide | Yes | 55 |
| 43 | Glucosamine | Low | Low | **High** | High | Medium | Universal | Yes | 49 |
| 44 | Chondroitin | Low | Low | Medium | High | Medium | Wide | Yes | 43 |
| 45 | Vitamin K2 | Medium | Low | Medium | High | Low | Wide | Yes | 52 |
| 46 | Hair/Skin/Nails | High | **Very High** | High | High | Medium | Universal | Yes | 62 |
| 47 | Biotin | Medium | Medium | Medium | Medium | Low | Universal | Yes | 40 |
| 48 | **Marine collagen** | High | **Very High** | High | High | Medium | Wide | Yes | **72** |
| 49 | Hyaluronic acid | Medium-high | High | Medium | High | Medium | Wide | Yes | 58 |
| 50 | Greens powder | **Very High** | **Very High** | High | **Very High** | Medium | Wide | Yes | **75** |
| 51 | Sea moss | High | Medium | Low | Medium | **Medium-High** ⚠ (iodine limits) | Wide | Yes | 47 |
| 52 | **Colostrum** | **Very High** | **High** | Medium | **High** | **Medium** ⚠ | Narrowing (few UK suppliers) | Limited | **76** |
| 53 | Shilajit | **Very High** | Medium | Low | Medium | **HIGH** ⚠⚠ (heavy-metal contamination is a documented, recurring problem) | Risky | **No** | 44 |
| 54 | Tart cherry | Medium-high | Medium | Medium | Medium-high | Low | Wide | Yes | 56 |
| 55 | Beetroot | Medium-high | Medium | Medium | Medium | Low | Wide | Yes | 52 |
| 56 | **Apigenin** | High | Medium | Low | Medium-high | Low-med | Narrow | Yes | 58 |
| 57 | Berberine | High | Medium | Low | High | **HIGH** ⚠⚠ (blood-sugar = medicinal claim territory; ad-platform toxic) | Wide | Yes | 38 |
| 58 | Taurine | Medium | Low | Low | Medium | Low | Wide | Yes | 44 |
| 59 | **Myo-inositol** | High | High | Medium | **High** | **Medium-High** ⚠ (PCOS = condition claim) | Wide | Yes | **64** |
| 60 | Lutein/zeaxanthin | Medium | Low | **High** | High | Medium | Wide | Yes | 55 |

### Products flagged for exclusion, and why

Per the Phase 2 instruction not to include dangerous/illegal/POM/banned/poorly-regulated products merely because they sell:

| Excluded | Reason | Label |
|---|---|---|
| **Melatonin** | **Prescription-only medicine in Great Britain.** Only Circadin 2mg holds a UK product licence. Selling it OTC in any format — pill, gummy, spray, drink — is unlawful | `[FACT]` |
| **DHEA** | POM in UK; explicitly disallowed by Google Ads policy | `[FACT]` |
| **CBD** | Novel Food regime + ASA has run an active 2025 enforcement line on CBD health claims and influencer ads | `[FACT]` |
| **NMN** | Contested/unresolved Novel Foods status in GB; not worth the regulatory exposure at launch | `[FACT/ANALYSIS]` |
| **SARMs, DMAA/DMHA, ephedra, phenibut, tianeptine, kratom** | Unlicensed medicines / banned substances | `[FACT]` |
| **Yohimbine** | Restricted; cardiovascular risk | `[FACT]` |
| **"Fat burners", appetite suppressants, detox teas, colon cleanse** | **Explicitly prohibited by TikTok Shop policy and Meta health-and-wellness ad standards** | `[FACT]` |
| **Red yeast rice (monacolin K)** | Regulated at medicinal thresholds; statin-like action | `[FACT]` |
| **"Testosterone boosters" as positioned** | The *ingredients* may be legal; the *positioning* triggers Meta/TikTok restricted-claims enforcement and MHRA borderline risk | `[ANALYSIS]` |
| **Shilajit** *(scored but not recommended)* | Recurring documented heavy-metal contamination in the supply chain. Included in the database because it is commercially significant on TikTok; **excluded from every launch recommendation.** If you ever sell it, per-batch ICP-MS heavy metals testing is mandatory, not optional | `[ANALYSIS]` |

---

## Table D — Companies, revenue, and honest attribution

| Company | Revenue | Period | Label | What it does **not** tell us |
|---|---|---|---|---|
| **Glanbia plc — Performance Nutrition** | **USD 1,801.1m**; EBITDA USD 233.8m, **13.0% margin (−380bps)** | FY2025 | `[FACT]` — Glanbia FY25 Preliminary Statement | Segment level only |
| **Optimum Nutrition (brand)** | **~USD 1,351m** | FY2025 | `[DERIVED]` — Glanbia disclosed ON = **75% of PN revenue** `[FACT]`; 0.75 × 1,801.1 | Still not product level. ON's creatine revenue is `[NOT PUBLIC]` |
| **THG plc — THG Nutrition (Myprotein)** | **£609.1m** (2024: £580.3m), +5.0% | FY2025 | `[FACT]` — THG FY25 prelims | Division level. Myprotein's per-SKU split is `[NOT PUBLIC]` |
| **THG Nutrition Q4 2025** | £157.2m, +8.1% | Q4 2025 | `[FACT]` | — |
| **Holland & Barrett (group)** | **£981m** revenue, **£579.9m gross profit (59.1%)**; digital **£249.4m (+20%)**; 809 UK stores, store sales £731.3m | FY2025 (YE 30 Sep 2025) | `[FACT]` — H&B corporate announcement | Private company; no category P&L. Note: £124m owner investment in the year |
| **Applied Nutrition plc** | **£107.1m** revenue (+24.3%); GP £34.8m, **46.7% GM**; operating profit **£20.7m**; PBT £20.9m (+77.1%); FY26 guidance £140m | FY2025 | `[FACT]` — APN FY25 results & Annual Report | Brand-level, not SKU-level |
| **Huel** | **£254m** (+19%); **PBT £19.4m (7.6% net)**; UK £139.3m (+26.5%), US £75.5m, EU £31.6m; wholesale £5.7m→£12.4m | FY2025 (YE 31 Jul 2025) | `[FACT]` — Companies House filing, reported by The Grocer | Acquired by Danone for ~€1bn, March 2026 `[FACT]` |
| **Bulk** | £123.1m (+30%), adj. EBITDA £9.3m, PBT £6.0m | FY2023 (most recent detailed public figures found) | `[FACT]` | 2024/25 accounts not located in this research — `[NOT PUBLIC]` |
| **Vitabiotics Ltd** | **£101.2m** — 2nd-largest UK vitamin & supplement *manufacturer* after THG | 2025 | `[FACT]` — IBISWorld | Third-party aggregators quoting "$232m" for Vitabiotics are unreliable and **should not be used**. UK's No.1 vitamin brand family; 8 of the UK's top 18 VMS brands (Pregnacare, Wellman, Wellwoman) `[FACT]` |
| **AG1 (Athletic Greens)** | **~USD 600m** annual revenue, profitable | 2024, held ~flat into 2025 | `[FACT]` — Forbes, Fortune | **Effectively one SKU.** The cleanest existence proof that a single supplement can build a $600m DTC business |
| **Danone** | Acquired Huel for **~€1bn** | March 2026 | `[FACT]` | Sets a credible exit comparable: ~3.9× revenue |

### Estimated revenue attributable to specific supplements

**`[NOT PUBLIC]` for every company above, with one partial exception (Optimum Nutrition, `[DERIVED]` above).**

I will not manufacture these numbers. Anyone who tells you "the global creatine market is $1.4bn and Optimum Nutrition has 12% of it" is inventing the 12%. What *is* usable:

- **`[FACT]`** Creatine category: USD 1.4bn (2025) → USD 8.7bn (2033), 26.2% CAGR (Grand View); powdered = 80.4% of revenue share.
- **`[FACT]`** Functional mushrooms: USD 12.06bn (2025), 9.45% CAGR (Mordor); Lion's Mane USD 418.4m (2024), 13.5% CAGR (GMI).
- **`[FACT]`** UK collagen: USD 583.6m (2025), 6.78% CAGR; marine collagen 40–45% of value.
- **`[FACT]`** UK probiotic supplements: ~USD 596m (2025), 7.5% CAGR.
- **`[DERIVED]`** UK creatine market: `[ESTIMATE]` UK ≈ 3–4% of the global supplement market by value → **UK creatine ≈ £35–£45m in 2025, growing >20%/yr.** Shown as a derivation, not a fact: 1.4bn × 3.5% × 0.78 GBP/USD ≈ £38m. **Treat as an order-of-magnitude sanity check only.**

**`[ANALYSIS]` — what Table D actually proves for us:** the UK market contains one £981m retailer, one £609m division, one £254m DTC brand, one £107m listed manufacturer and one £101m manufacturer. That is a market with **big, well-capitalised incumbents and no dominant DTC challenger under £100m**. There is a real gap between "£100m incumbents" and "£0 startups" — and Applied Nutrition's rise from nowhere to a £107m LSE-listed business, and AG1's $600m on one SKU, prove the gap is crossable. It just isn't crossable cheaply.

---

**Next:** `03-ranking-and-shortlist.md` — Top 20 → Top 10 → Top 5.

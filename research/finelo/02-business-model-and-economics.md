# 02 — Business Model and Economics

## 2.1 The pricing ladder

| Tier | Price | Label |
|---|---|---|
| Entry offer | **$19.99** — stated as "a first-month discount price for our 4-week plan" | `[FACT]` |
| Marketing framing | "Begin a 28-day path today, with as little as $20" | `[FACT]` |
| 1-week plan | Lowest absolute cost, short-term access | `[FACT]` |
| 12-week plan | Full course, best per-week rate | `[FACT]` |
| **Steady-state renewal** | **$39.99 / month** | `[FACT]` |
| In-app purchase points (US App Store) | $9.99 · $12.49 · $19.99 · $24.99 · $29.99 | `[FACT]` |
| Refund guarantee | 28-day, **conditional** | `[FACT]` |

`[ANALYSIS]` The structure is a classic **discounted-entry / full-price-renewal** ladder. Three things follow from it:

1. **The $19.99 is not the price; it is the CAC offset.** The business is made on renewals at $39.99 and on the five in-app upsell points stacked on top.
2. `[DERIVED]` **The step from entry to renewal is +100%** ($19.99 → $39.99). A user who does not register that step is a complaint waiting to happen — and §03 shows 82 of them in twelve months.
3. `[ANALYSIS]` The 12-week plan being sold on "best per-week rate" is the margin product: it front-loads cash, removes three renewal decision points, and pushes the user past the 28-day refund window before the first natural cancellation moment.

`[DERIVED]` **Annualised value of a retained subscriber**, entry month + 11 renewals: $19.99 + (11 × $39.99) = **$459.88**, before upsells and before refunds. `[ASSUMPTION]` Real retention on a 28-day-challenge product is far below 12 months — challenge-format apps have a structural churn cliff at completion. `[ESTIMATE]` A realistic blended LTV is more plausibly in the **$60–$120** band. `[NOT PUBLIC]` — actual retention curves are not disclosed.

---

## 2.2 The acquisition machine

`[FACT]` Zimran describes itself as a major Meta / Google / TikTok partner in Central Asia. `[FACT]` The Zimran playbook — visible in both Finelo and Coursiv — is the **quiz funnel → web-to-app** model: paid social drives cold traffic to a web quiz, the quiz personalises an offer and takes payment on the web, and the app install happens after the sale.

`[ANALYSIS]` Why this matters commercially — and why it is the most transferable thing in this document:

- **Payment happens on web, not in-app.** That avoids Apple/Google's 15–30% commission on the initial sale. `[DERIVED]` On a $19.99 entry, keeping ~30% is **$6.00 per sale** that would otherwise be platform fee — on a business doing hundreds of thousands of sales, that is the difference between a viable and a non-viable CAC.
- **The quiz is a qualification and price-discrimination instrument**, not a content feature. It collects intent signals before showing a price.
- **The install is a retention mechanism, not an acquisition one** — which inverts the usual mobile playbook.

`[ANALYSIS]` This is the *same funnel logic* as the TikTok Shop affiliate finding in `13-cac-pressure-test.md` of the supplement research: the channel that is first-order profitable is the one where the platform tax and the CAC are structurally lower, not the one with the best creative.

---

## 2.3 Revenue evidence

| Metric | Value | Label |
|---|---|---|
| **Finelo revenue** | — | `[NOT PUBLIC]` |
| **Coursiv, first year** | **$1.8M** | `[FACT]` |
| Coursiv monthly run-rate, Aug 2025 | **>$250,000/month**, best month June 2025 | `[FACT]` |
| Coursiv Android, Nov 2025 | ~50k monthly downloads, ~$70k monthly revenue, **$1.40 per download** | `[ESTIMATE]` (third-party panel data) |
| Coursiv launch | April 2025 | `[FACT]` |

`[ANALYSIS]` Coursiv is the single most useful number in this research, because it is a **same-group, same-playbook, recent, from-zero benchmark**. It tells us what the Zimran funnel produces on a new brand: roughly **$250k/month within 16 months of launch**, from a standing start, in a category with no incumbent moat.

`[ANALYSIS]` The **$1.40 revenue per Android download** figure is the honest counterweight. It is low, and it is exactly what you would expect from a funnel that buys enormous cold volume and monetises a thin slice of it. This is a **volume business with a thin per-user margin and a heavy ad-spend dependency** — not a high-margin SaaS. Anyone modelling this shape should assume the ad account *is* the business, and that a Meta or TikTok policy change is an existential event, not an operational one.

`[DERIVED]` Finelo is the older and larger of the two brands. `[ESTIMATE]` If Finelo's US install base is 2–5M lifetime (§01.5) and it monetises on the same funnel, its revenue is very likely **multiples of Coursiv's**, plausibly in the **$5M–$40M/year** range. **This is a wide band derived from a chain of estimates and should not be relied on for any decision.** The honest answer remains `[NOT PUBLIC]`.

---

## 2.4 Market context

| Metric | Value | Label |
|---|---|---|
| Trading education market, 2026 | **$1.29bn**, → $2.3bn by 2034, **7.8% CAGR** | `[FACT]` |
| Regional leader | Asia Pacific, **38.5%** of 2025 global revenue | `[FACT]` |
| Stock trading / investing apps market | $63.62bn (2025) → $76.59bn (2026), 20.4% CAGR | `[FACT]` |
| Global EdTech | $199.74bn (2025) → $236.25bn (2026), 18.3% CAGR | `[FACT]` |

`[ANALYSIS]` Read these in the right order. **The relevant number is $1.29bn, not $236bn.** Trading education is a small, moderately-growing niche sitting inside two much larger markets that it is easy to mistake itself for. 7.8% CAGR is respectable but it is not a wave — and it is the same analytical trap flagged in the supplement research (finding #4: *"the UK online supplement channel is growing at 1% a year, not 10%… global '$200bn market' figures are commercially useless here"*).

`[ANALYSIS]` The growth driver cited — *"integration of AI and ML into trading education platforms, enabling personalised learning paths and real-time performance analytics"* — is precisely what Finelo has built and precisely what our repo has the raw material for. That is a real tailwind, but it is a tailwind everyone can see.

---

## 2.5 Head-to-head: Finelo's shape vs. the supplement plan

This is the comparison worth having, because both are live options on the table.

| Dimension | UK supplement DTC (per `research/supplement-ecommerce/`) | Trading-education app (Finelo shape) |
|---|---|---|
| **Peak working capital** | **~£80,000** `[FACT, prior research]` | **~£0 inventory** — spend is ad budget, which is throttleable `[ANALYSIS]` |
| **Marginal COGS** | £2.80–£10.50 per order `[FACT, prior research]` | **~£0** — plus payment fees and AI inference `[ANALYSIS]` |
| **Net margin** | **7.6% at £254m** (Huel); ~5.8% EBITDA modelled `[FACT, prior research]` | Higher gross, but ad-spend-dominated; `[NOT PUBLIC]` for Finelo |
| **CAC** | **£62** revised base `[FACT, prior research]` | `[NOT PUBLIC]`; $1.40 rev/download implies a very low per-user CAC on huge volume |
| **Effective "COGS" risk line** | Inventory obsolescence, whey inflation, recall | **Refunds and chargebacks** `[ANALYSIS]` |
| **Regulator** | FSA, MHRA, Trading Standards, ASA | **FCA (FSMA s.19/s.21), ASA/CAP, consumer subscription law** |
| **Regulatory sharpness** | High — but the firewall is formula + copy | **Higher** — the firewall is where the order goes + copy |
| **Scalability** | Constrained by cash conversion cycle | **Near-unconstrained** — constrained only by ad budget |
| **Kill risk** | Supplier failure, MHRA reclassification | **Ad account ban** — single point of failure |
| **Exit comparable** | Huel → Danone ~€1bn at ~3.9× revenue `[FACT, prior research]` | `[NOT PUBLIC]` — Zimran unexited |
| **Time to first revenue** | Months (RFQ → manufacture → launch) | **Weeks** — the product is content and code |

`[ANALYSIS]` **The digital shape is economically superior on every axis except brand durability and exit comparability.** It removes the single biggest objection in the supplement research — the £80k peak working capital that "is 3–8× what most founders budget" — and replaces it with an ad budget you can switch off on any given Tuesday.

`[ANALYSIS]` What it does **not** remove is the hard part. In supplements the hard part was the arithmetic; here the arithmetic is friendlier and **the hard part is the regulator and the platform.** A £70 CAC is a maths problem you can solve with bundles. An FCA perimeter breach or a permanent Meta ban is not a maths problem. See §03.

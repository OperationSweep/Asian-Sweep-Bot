# 03 — Reputation and Risks

## 3.1 The two contradictory reputations, reconciled

Finelo simultaneously holds an excellent consumer rating and a visible "is this a scam" search footprint. Both are accurate, and the reconciliation is the useful part.

| Source | Signal | Label |
|---|---|---|
| Apple App Store (US) | **4.6★ from ~99,000 ratings** | `[FACT]` |
| Trustpilot | **4.6★ from 17,000+ reviews; 94% are 4–5★** | `[FACT]` |
| Newsweek / Statista | Listed, "America's Best Online Platform 2025", Education & Learning | `[FACT]` |
| **BBB** | **NOT accredited**; **132 complaints in 12 months** | `[FACT]` |
| Trust-scoring services | finelo.com scored 88.6 / authentic | `[FACT]` |
| Independent review consensus | *"Not a scam — the company exists, the courses deliver, the simulator works"* | `[FACT]` |

### The BBB complaint taxonomy

`[FACT]` 132 complaints closed in the last 12 months (and 132 over three years — i.e. **essentially all of them are recent**):

| Category | Count | Share |
|---|---|---|
| **Billing** | **82** | **62%** |
| Service / repair | 26 | 20% |
| Sales & advertising | 14 | 11% |
| Product | 8 | 6% |
| Other | 2 | 2% |

`[FACT]` 99 answered, 33 resolved. `[DERIVED]` **A 25% resolution rate against complaints raised** — answering is not the same as resolving, and the gap is where the reputational damage accumulates.

`[FACT]` The named grievances: unauthorised recurring charges, difficulty cancelling, refund delays, and confusion about terms disclosed before purchase.

### The reconciliation

`[ANALYSIS]` These two pictures are not in conflict; they measure different populations at different moments.

- **Trustpilot and the App Store capture the learning experience**, rated by users at the point of engagement — often prompted in-app during a streak. The product genuinely is good at what it does, and 94% 4–5★ is not manufacturable at 17,000 reviews.
- **BBB captures the billing experience**, rated by users at the point of an unexpected charge. Nobody files a BBB complaint about a lesson.

`[ANALYSIS]` So: **the product is good and the billing is adversarial.** The "scam" label is earned by the second, not the first, and it is the reason a genuinely well-rated education app has an "is Finelo legit" content industry around it. `[FACT]` One reviewer's summary is exactly right: *"the 'scam' reputation is almost entirely about billing friction, not fraud."*

`[ANALYSIS]` A secondary theme is worth recording separately because it is a different offence: `[FACT]` reviewers report *"misleading marketing videos that use fictional stories, in some instances imply profits, and lean on emotions like fear of missing out."* **Implied profits in trading-adjacent marketing is a materially more serious problem than a confusing renewal date** — see §3.3.

---

## 3.2 The clone-domain problem

`[FACT]` The genuine product is **finelo.com** plus the official App Store / Play Store listings. Search results surface a cluster of lookalikes:

| Domain | What it advertises | Assessment |
|---|---|---|
| **finelo.com** | Education + simulator | ✅ **Genuine** — trust score 88.6 |
| finelo.ai | — | ⚠️ Low trust score, "very young, might be a scam" `[FACT]` |
| fineloai.digital | *"Premium AI-powered trading automation for professional operations"* | 🚩 Not the real product `[ANALYSIS]` |
| finelo-ai.com | *"Official Website 2025 — Secure Trading Platform"* | 🚩 Not the real product `[ANALYSIS]` |
| finelopro.com | *"AI-Driven Automated Trading Bots Overview"* | 🚩 Not the real product `[ANALYSIS]` |

`[ANALYSIS]` The tell is unambiguous and easy to teach: **the real Finelo does not trade real money and does not connect to a broker.** Every lookalike positions itself around *automated real-money trading* — which is the one thing the genuine product explicitly is not. Anything under the Finelo name promising automated trading, a "secure trading platform," or deposits is impersonating an education app to sell something else entirely.

`[ANALYSIS]` **Relevance to us beyond safety:** this is what happens to a brand that markets an "AI trading bot" into a retail audience. The brand becomes bait. If we ever ship anything called a bot to the public, the clone/impersonation problem is not a tail risk — it is a scheduled event, and trademark plus domain defence is a launch-week cost, not a year-three one. `[FACT]` Note that Zimran did register FINELO and FINELO APP as trademarks.

---

## 3.3 The UK regulatory position

This is the section that matters if the Asian Sweep Bot ever becomes a product rather than a personal tool.

### The perimeter

`[FACT]` **FSMA 2000 s.19** — the General Prohibition: no person may carry on a **regulated activity** in the UK unless authorised or exempt.

`[FACT]` **FSMA 2000 s.21** — no person may, in the course of business, **communicate an invitation or inducement to engage in investment activity** unless they are authorised, or the communication is approved by an authorised person.

`[FACT]` **Only FCA-authorised firms can issue or approve a financial promotion.** All financial promotions must be **clear, fair and not misleading**, in any medium.

`[FACT]` **The critical point, and it is not intuitive:** the FCA has asserted that **teaching activities can themselves amount to regulated activities** — specifically *advising on investments* or *arranging deals in investments* — under the Regulated Activities Order. Calling something "education" does not, by itself, put it outside the perimeter.

### How Finelo sits outside it

`[ANALYSIS]` Finelo's design reads as a deliberate, coherent answer to exactly this problem. Four load-bearing choices:

1. **The order never reaches a market.** Simulator, virtual funds, no broker connection, no client money. This alone removes *arranging deals* and *dealing as agent*.
2. **Nothing is personalised.** The AI Mentor "does not give personalized investment recommendations"; bots are *presets* framed as making "strategy logic visible." **Advice on investments is personal recommendation** — generic strategy explanation is much harder to characterise as advice.
3. **The disclaimer is explicit, repeated, and on the product itself** — not buried in a footer.
4. **The framing is consistently pedagogical.** Not "our bot makes money" but "here is what this strategy does and why."

`[ANALYSIS]` **The transferable rule: the perimeter is crossed by three things — where the order goes, whether the output is personalised, and how you describe it.** The code that finds a liquidity sweep is regulatorily inert. The sentence you put next to it is not.

`[ANALYSIS]` This is structurally identical to the finding in the supplement research: *"your ad copy, not your formula, is what can reclassify your product as an unlicensed medicine."* Same lesson, different regulator. **The compliance boundary in both businesses runs through the marketing department, not the product team.**

### Where the risk actually concentrates

`[ANALYSIS]` Ranked by probability × severity for a UK operator building in this space:

| # | Risk | Why it bites | Severity |
|---|---|---|---|
| 1 | **Implied or illustrated profits in ads** | Trading-adjacent promotion implying returns is the fastest route to both an ASA ruling and FCA attention. This is the exact criticism already levelled at Finelo's marketing videos. | 🔴 Critical |
| 2 | **Ad account ban** | The business *is* the ad account (§02.2). Financial-services ad policies at Meta/TikTok/Google are stricter than supplements and enforced by classifier, not human. | 🔴 Critical |
| 3 | **Personalisation creep** | The moment output is tailored to a user's holdings, capital or risk profile, "education" starts to look like a personal recommendation. This creep is a natural product-improvement direction, which is what makes it dangerous. | 🟠 High |
| 4 | **Connecting to a real broker** | Instantly changes the classification. A tempting "power user" feature that would reclassify the whole product. | 🟠 High |
| 5 | **Subscription / auto-renewal practice** | UK consumer-protection rules on subscription contracts and auto-renewal are tightening; the Finelo complaint pattern (82 billing complaints/yr) is precisely the pattern being legislated against. **Verify the current position under the DMCC Act 2024 subscription regime before designing any billing flow.** | 🟠 High |
| 6 | **Chargebacks** | Aggressive renewal + trading-adjacent product = elevated dispute rate. Above threshold, acquirers terminate. | 🟡 Medium |
| 7 | **Brand impersonation** | See §3.2. Scheduled, not tail. | 🟡 Medium |

`[ANALYSIS]` Note that risks 1, 3, 4 and 5 are all **self-inflicted and free to avoid at design time**, and all four become expensive to unwind later. That is the argument for deciding the fork before writing more code, not after.

> **Not legal advice.** The FSMA/RAO perimeter is fact-specific and the consequences of getting it wrong are criminal, not merely commercial. Take FCA-competent legal advice before offering any trading tool, signal or course to third parties in the UK.

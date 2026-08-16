# 01 — Company and Product

## 1.1 Corporate structure

| Item | Detail | Label |
|---|---|---|
| Consumer brand | Finelo — "Master Trading" | `[FACT]` |
| Operating entity | **Finelo Limited**, Limassol, Cyprus | `[FACT]` |
| App Store developer of record | Finelo Limited | `[FACT]` |
| Android package ID | `io.zimran.finelo` | `[FACT]` |
| Parent group | **Zimran Ltd.**, Kazakhstan | `[FACT]` |
| Group founded | 2021 | `[FACT]` |
| Founders | Zhanibek Sydykov (CEO), Eduard Tupikov (CMO), Arman Nurgaziyev (CTO) | `[FACT]` |
| Brand trading since | Late 2022; mobile launch 2024 | `[FACT]` |
| Sister product | **Coursiv** (`io.zimran.coursiv`) — AI-tools education | `[FACT]` |
| Group self-description | "Well-funded and already profitable"; "Lifestyle EdTech" | `[FACT]` (company claim) |
| Group financials | — | `[NOT PUBLIC]` |

`[ANALYSIS]` The Cyprus-operating-entity / Kazakhstan-parent split is unremarkable for a consumer subscription app selling into the US and EU — Cyprus gives an EU billing entity and Apple/Google payout relationship. It is not, on its own, a red flag. What it does mean is that **no filed financials will ever be available**, so every revenue figure in this research is either a third-party estimate or absent.

`[FACT]` The group states that Finelo and Coursiv have both entered the top-10 EdTech applications in the USA and that they are major Meta / Google / TikTok partners in Central Asia. `[ANALYSIS]` "Major partner" in this context means large ad spend, not a product integration. It is a signal about the size of the paid-acquisition machine, which matters for §02.

---

## 1.2 What the product actually is

`[FACT]` Finelo is an **education and simulation platform**. It is explicitly:

- **not a brokerage**
- **not an investment adviser**
- **not connected to any real trading account**

`[FACT]` Its own disclaimer: *"Finelo is an educational platform only, we do not provide financial or investment advice. Investing involves financial risks, including the loss of your investment."* The App Store listing repeats it: *"designed for educational purposes and does not provide personalized financial advice."*

### Content

| Component | Detail | Label |
|---|---|---|
| Lessons | 300+ bite-sized, ~3 min average, 10 languages | `[FACT]` |
| Total content | 270+ hours claimed across four learning paths | `[FACT]` (company claim) |
| Structure | 28-day challenge, ~15 min/day, quizzes, streaks, XP, badges | `[FACT]` |
| Challenge variants | Classic trading, Classic investing, AI-assisted trading, AI-assisted investing | `[FACT]` |
| Paths | Investor (stocks/ETFs/portfolio), Trader (short-term analysis, chart reading), Crypto (blockchain, digital assets) | `[FACT]` |
| Simulator | Virtual funds, **real market data**, no broker connection | `[FACT]` |
| Community | Facebook group | `[FACT]` |

### Depth

`[FACT]` Independent reviews converge on a single criticism, stated three different ways:

- *"Advanced traders and experienced investors will find Finelo's content too introductory."*
- *"The platform is not trying to make you a day trader. It's trying to take someone who's intimidated by finance and give them enough knowledge to feel confident opening a brokerage account."*
- *"An experienced trader will find the depth shallow, and that is a recurring complaint in the App Store reviews."*

`[ANALYSIS]` This is not a defect — it is a deliberate and correct positioning choice. The addressable market for "what is a stock" is 100× the market for "how do I model a Tokyo-session liquidity sweep." **It is simply not our market as a buyer.**

---

## 1.3 The AI feature set

`[FACT]` Named AI features:

| Feature | What it does |
|---|---|
| **AI Chart Analyzer** | Upload or select an asset + timeframe; returns a structured snapshot: technical behaviour, volatility, trend state, analyst sentiment, key price levels, recent news. Covers stocks, forex and crypto. |
| **Smart Pattern Finder** | Identifies historical chart patterns and reports **historical probability** — *"in the past, similar structures resolved this way X% of the time."* |
| **AI Mentor** | Plain-language Q&A on market concepts and movements. Does **not** give personalised recommendations. |
| **AI Bots store** | Browse and set up bots "in a few taps," with smart signal alerts. |
| **Strategy presets** | Cautious (capital protection), Momentum (trend-following), Contrarian (mean reversion) — framed as *"not there to copy blindly… there to make strategy logic visible."* |

### The bot workflow — the part that matters to us

`[FACT]` Three stages, as advertised:

1. **Bot scans** — watches markets continuously for matching setups
2. **User reviews** — each setup is explained in plain language
3. **User decides** — **approve or decline in one tap**

`[FACT]` A bell icon on the bot screen shows **every trade setup the bot has found**, and whether it was **approved, declined, or expired**. `[FACT]` Version 1.48.2 shipped "trade setup history tracking, bot activity displays, and asset selection improvements."

---

## 1.4 A contradiction worth recording

`[FACT]` The marketing homepage describes AI Bots with "smart signal alerts so you never miss a market move" and one-tap trade approval. `[FACT]` The dedicated AI product page states the platform "operates entirely in simulation… the simulator uses virtual funds and real market data and is not a brokerage," describes the bots as *presets* whose purpose is to make strategy logic visible, and contains **no** alert or approval flow.

`[ANALYSIS]` Two readings, and they are not mutually exclusive:

1. **Charitable and probably correct:** the bots are real features that execute into the simulator. The approve/decline tap books a *virtual* trade. The marketing page sells the experience; the product page states the legal reality. Both are true.
2. **Critical:** the homepage copy is written to read like a real-money automated trading tool to a reader who does not scroll to the disclaimer. That is precisely the ambiguity that generates the "Sales & Advertising" complaint category in §03.

`[ANALYSIS]` **For our purposes the distinction is the whole lesson.** The same feature — a bot that finds setups and asks a human to approve them — is an education product when it books to a simulator and a regulated activity when it books to a broker. The code is nearly identical. The classification is decided by where the order goes and how you describe it.

---

## 1.5 Recognition and scale claims

| Claim | Source | Label |
|---|---|---|
| 4.6★, ~99,000 US App Store ratings | Apple App Store listing | `[FACT]` |
| 4.6★, 17,000+ Trustpilot reviews, 94% 4–5★ | Trustpilot via review aggregators | `[FACT]` |
| "1,500,000+ Learners Worldwide" | finelo.com homepage | `[FACT]` (company claim) |
| "Surpassed 100k learners globally" post-2024 launch | finelo.com/about-us | `[FACT]` (company claim) |
| "1.15 million paid subscribers" | third-party reviews | `[ESTIMATE]` — repeating a company claim |
| "2 million+ premium users, 180+ countries" | Zimran group, **Finelo + Coursiv combined** | `[FACT]` (company claim) |
| Newsweek / Statista "America's Best Online Platform 2025", Education & Learning | Newsweek/Statista | `[FACT]` — note this is a **nomination/listing**, not a win |

`[ANALYSIS]` These numbers do not reconcile cleanly, and the inconsistency is itself informative. "100k learners" (about page), "1.5M learners" (homepage), "1.15M paid subscribers" (third parties) and "2M+ premium users" (group, two apps) are four different metrics presented interchangeably. **Treat all of them as marketing.** The only figure with independent grounding is the App Store rating count — ~99,000 US ratings implies a genuinely large install base, since typical rating-prompt conversion is low single-digit percent. `[DERIVED]` At a 2–5% rating rate `[ASSUMPTION]`, ~99k US ratings implies roughly **2–5 million US installs** lifetime. That is consistent with a real top-10 category app and inconsistent with a shell.

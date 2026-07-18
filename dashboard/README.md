# AMPS Quarterly Kitting Dashboard

Single-file, offline HTML dashboard (`amps-kitting-dashboard.html`) showing
**planned (ASP) vs kitted (COOIS) AMPs per contract per week**, with
UNDER / ON TRACK / AHEAD verdicts, repeater-equivalents, and a serial-number
audit layer. Open the file in any browser; no install, no macros, no network.
All pasted data stays in the browser (localStorage).

## Environment constraints (important)

- SAP is accessed through the **NetWeaver web viewer with a restricted
  transaction set**. Available transactions: **COOIS**, **IQ09**, **ZPRO**
  (custom goods-issue). Classic codes like MB51/SE16N/SQVI are NOT available —
  never design a workflow around them.
- Inputs are therefore paste-based exports, not live connections.

## Inputs

1. **COOIS** — List = *Documented Goods Movements* over the AMP work orders:
   movement types 261/262 **and 101/102**, all component materials, wide date
   range. One export covers all contracts.
2. **ASP plan** — open in Excel, select-all, copy, paste. Parsed: PROJECT_ID/
   PROJECT_DESC, ITEM_ID (fibre pairs), PROD_ID (contract digits), Total
   system, and the weekly matrix (year row + week-number header row after
   "Planned Qty"; cells = repeaters planned that week).
3. **IQ09 serial list** (optional) — audit layer for serial lookups.

## Business rules (validated against real exports, July 2026)

- **1 work order = 1 AMP. A repeater needs FP-count AMPs** (24FP repeater =
  24 AMP orders). Planned AMPs per week = ASP weekly repeaters × FP.
- Fibre pairs parse from ITEM_ID: `R512.24REPOPT` → 24FP, `R512/9.19REP` →
  19FP (verified: Aurora 104×24=2,496; Medusa 5×19=95).
- **Contract identity = last 3 digits of the 5-digit group** in assembly
  codes (92YAF00**588**AAA → 588 = FIG) and ASP PROD_IDs (92ERP24**429**A++ →
  429 = Aurora).
- AMP order BOM (from real orders): 2× GFF (91CFL…), 2× 92RRA…, 4× CCG,
  1× PCL; output = 92YAF… assembly received via movement **101** ("built").
- **GFF variants are contract-unique**; the variant→contract mapping is
  learned automatically from orders where a GFF and an RRA/YAF code co-occur
  (validated 100% unambiguous on 10 variants). Known fixed mapping:
  91CFL00302AFT → 429 Aurora (confirmed by operations; Aurora orders carry no
  RRA/YAF rows in the export window). AFM → 335 Medusa ("KOHOKU" in GFF
  descriptions is Medusa's codename).
- An order counts as **kitted** on its first net-positive GFF issue
  (261 − 262) — the ZPRO posting date. Movement 262 reverses; a serial keeps
  only its last change date.
- Serial statuses (IQ09): `ESTO` in stock · `AVLB` consumed (ZPRO'd) ·
  `ECUS` at customer; consumed serial's "Changed on" = ZPRO posting date
  (validated: daily counts reconcile exactly with COOIS net 261s).
- Verdict = cumulative kitted vs cumulative planned up to the current week,
  ±5% tolerance. The plan matrix only covers the weeks present in the ASP
  export, so contracts kitted before the matrix window read as AHEAD.

## Contract mapping

Contract digits found in the data get names automatically from ASP PROD_IDs;
the "Contract names & fibre pairs" editor fills the gaps (names for 438, 517,
521, 527, 627, 746; FP overrides for mixed-FP contracts). Entries persist in
the browser.

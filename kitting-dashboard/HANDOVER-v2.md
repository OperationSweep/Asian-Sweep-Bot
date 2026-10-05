# R5B AMP Kitting Control v2 — handover

**Files**
- `R5B-AMP-Kitting-Control-v2.xlsx`: the operational workbook (Microsoft 365, no macros, no links).
- `R5B-AMP-Release-Log-Archive.xlsx`: static history (182 release-log lines) plus the migration reconciliation. Nothing links to it.

## Everyday use (production controller)
1. **Assemblies & Totals:** overwrite *Cumulative supplied to date* with the new **total**. If the total was 26 and 4 more were supplied, enter 30. Then fill *Updated on*, *Updated by* and *Source reference* (the SAP export filename).
2. **Corrections:** enter the correct total, even if it's lower, and explain it in *Correction note*.
3. **Dashboard:** pick a contract and read the tiles. *Next action* tells you what to do.

## Plan maintenance (planner)
- **Weekly Plan:** one row per **final build / housing week (Monday)**.
- **Move:** change the date. **Split:** reduce the qty and add a row. **Cancel:** delete the row.
- **Replace a contract's plan:** filter on that contract, delete all of its rows, then paste the new rows.
- Record the change in *Plan revision*, *Plan updated on* and *Plan updated by* on **Contracts**.

## Contract setup (once per contract)
1. **Contracts:** add a row.
2. **Assemblies & Totals:** add one row per assembly code (from ZMRP).
3. **Weekly Plan:** add the contract's weeks.

No formulas, ranges or formatting need changing. New rows appear in the Dashboard and Gantt automatically.

## Design notes
- Kit release = final build − kit lead (2 weeks). AMPS build = final build − AMPS lead (1 week). Both are set per contract.
- A complete repeater kit = the lowest complete-set count across the contract's assemblies. It does not mean production is complete.
- The Dashboard and Gantt are protected without a password. The input sheets are unprotected so Excel Tables can grow.
- Supplied totals older than **Contracts!C4** days (default 7) are flagged as out of date.
- If a grey (calculated) column is overwritten, copy a cell from the row above. The formulas are listed on Start Here.

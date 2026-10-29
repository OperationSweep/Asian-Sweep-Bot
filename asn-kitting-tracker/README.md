# ASN Kitting Progress Tracker

This folder holds a simple kitting progress tracker for repeater assembly kitting at ASN, in two versions:

- **Excel workbook** (Microsoft 365, no macros).
- **Standalone HTML page** (works offline in any modern browser).

Both versions apply the same rules to the same inputs and give the same numbers.

| File | What it is |
|---|---|
| `ASN Kitting Progress Tracker (blank).xlsx` | Excel workbook with the assembly requirements loaded. No ASN plan or order data. Paste the ASP and COOIS exports to start. |
| `ASN Kitting Progress Tracker (blank).html` | HTML version with the assembly requirements loaded. Use **Load ASP** / **Load COOIS** to start. |
| `build/` | Builders, the shared calculation engine (`engine.js`) and the tests. |

Copies already loaded with the August ASP and the current COOIS export are handed over separately. They are not stored in this repository because they contain SAP order and user data.

## Daily routine (both versions)

1. Load the ASP.
2. Load the COOIS export.
3. Choose the contract variant you actually kitted, the stage, and the repeaters' worth kitted.
4. Review the quantities and the proposed orders.
5. Confirm.

The tracker:

- works out the units needed from the per-repeater requirements in Settings;
- proposes unallocated, non-CLSD COOIS orders (oldest release first);
- shows any shortage;
- records the confirmed entry and the order allocation in the Kitting Log.

Corrections are made by voiding an entry with a reason. Nothing is deleted.

| | Excel | HTML |
|---|---|---|
| Loading the ASP and COOIS | Paste each export at A1 of its sheet. | **Load ASP** / **Load COOIS** buttons. |
| Confirming an entry | Copy the green block, then Paste Special > Values at the bottom of the Kitting Log. Excel without macros cannot append rows itself. | **Confirm and record** button. |
| Duplicate protection | The Check column flags an order pasted twice ("Duplicate allocation - fix"). | Allocated orders are never offered again. |
| Where data is saved | In the .xlsx file. | In the browser on that PC. Use **Save backup** (.json) to keep it on the shared drive. |
| Sharing with the other version | The Kitting Log columns are identical. Rows copied from the HTML paste straight in. | **Import Excel tracker** reads the workbook's Settings, Kitting Log, ASP and COOIS. **Copy new rows for Excel** gives tab-separated rows to paste into the workbook. |

## Rules implemented

- **Variant ID.** This is the ASP `Friendly_name` (e.g. `E2A-R12P-T5-C`). Kitting history is keyed on it, so a new ASP never erases progress.
- **Variants that leave the ASP.** A set-up or recorded variant that disappears from the ASP is flagged for review.
- **Kit target week.** This is the ASP week minus the kit lead (Settings, default 3). It uses ISO weeks, so year ends (including 53-week years such as 2026) are handled.
- **Complete assembly kits.** These are repeaters' worth where every set-up assembly line is recorded **and** covered by allocated COOIS orders. The lowest line decides. A complete kit is not a finished repeater.
- **CNF.** CNF is never treated as kitted.
  - PCNF, CNF, DLV, CLSD and TECO are matched as whole status words.
  - CLSD is flagged for review; its cause is not confirmed by the status alone.
- **Contract allocation.** This comes from the controller's confirmed entry. The COOIS export does not prove which contract an order belongs to.
- **Shared codes.** Codes shared by several variants (e.g. PSB `91YAF03404AAA`: 1 per REP on E2A 4FP, 3 on E2A 12FP, 6 on WKE 24FP) are never assigned automatically.
- **Repeater View.**
  - **Kitted** means recorded against a REP number.
  - **Kitted\*** means covered by a contract-level quantity and shown against the earliest open REP positions. It is not a physical traceability link.
- **Missing requirements.** A variant with no requirement rows shows "Assembly setup required".

The assembly requirements for E2A-R4P-T1-C, E2A-R12P-T5-C and WKE-R24P-T1-C are loaded. The 12FP and WKE lists were reconstructed from tables pasted in chat. Every requirement row carries a note asking for it to be checked against the original kitting sheet.

## Rebuilding and testing

```
KIT_SRC=<folder with asp.xlsx and coois.xlsx> python3 build/build_xlsx.py out.xlsx [--blank]
python3 build/build_html.py out.html xlsx.full.min.js [seed-scenario.json]
python3 build/run_tests.py          # every scenario through Excel (LibreOffice recalculation) and the JS engine
node build/ui_test.js tracker.html asp.xlsx coois.xlsx tracker-with-log.xlsx outdir   # browser test of the HTML
```

`run_tests.py` covers the following, as multi-step scenarios:

- the shared PSB code;
- no double allocation;
- a repeated or new COOIS export;
- missing or changed orders;
- unallocated shared orders;
- CNF before picking;
- CLSD orders;
- partial entries and shortages;
- an ASP adding or removing a variant;
- year-end target weeks;
- missing requirements;
- a management order change;
- REP-level recording and corrections.

Each step is recalculated in Excel through LibreOffice and run through the JS engine. The step fails if any number, flag or proposed order differs, or if any formula error cell appears.

**Not verified in Microsoft Excel.** The tests use LibreOffice 26.2. The following have not been opened in Excel:

- spill behaviour;
- table auto-expansion on paste;
- dropdowns fed by spill ranges;
- conditional formatting;
- sheet protection.

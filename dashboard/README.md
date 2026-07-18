# AMPS Quarterly Kitting Dashboard

Single-file, offline HTML dashboard (`amps-kitting-dashboard.html`) for tracking
AMP kitting — planned (ASP) vs kitted (COOIS) — with GFF serial-number
attribution. Open the file in any browser; no install, no macros, no network.
All pasted data stays in the browser (localStorage).

## Environment constraints (important)

- SAP is accessed through the **NetWeaver web viewer with a restricted
  transaction set**. Available transactions: **COOIS**, **IQ09**, **ZPRO**
  (custom goods-issue). Classic codes like MB51/SE16N/SQVI are NOT available —
  never design a workflow around them.
- Inputs are therefore paste-based exports, not live connections.

## Inputs

1. **COOIS** — List = *Documented Goods Movements*, filtered to the GFF
   material code(s), wide date range. Export as .XLS (tab-separated text) and
   paste. Columns used: Order, Material, Mat. Doc., Mvmt Type (261/262),
   Pstng Date.
2. **IQ09** — serial list for the same GFF material(s). Open in Excel,
   select-all, copy, paste. Columns used: Material, Description, Serial number,
   System status, Equipment, Changed on.

## Business rules (validated against real exports, July 2026)

- **AMPS = repeaters × fibre pairs** (e.g. 104 repeaters × 24FP = 2,496 AMPS).
- Serial status: `ESTO` = in stock · `AVLB` = consumed (ZPRO'd) · `ECUS` = at
  customer.
- For consumed serials, IQ09 **"Changed on" = the ZPRO posting date**.
  Validation: on every COOIS posting date, net 261 issues = serials changed
  that day (92=92, 94=94, 48=48, 48=48, 96=96 across the test window).
- **One kitting = one material document = exactly 2 GFF serials per work
  order** ("always ×2").
- Movement 262 is a reversal; a serial only keeps its *last* change date, so a
  reversal shows as −n on the original day and +n on the re-issue day
  (observed on order 100851041).
- **GFF material codes are contract-unique** (contract name is the first word
  of the GFF description, e.g. "KOHOKU GFF 37.7nm/…"). GFF codes are NOT
  unique per fibre pair.
- Serial → contract is exact. Serial → specific work order is narrowed to the
  posting day's order set; exact pairing requires the serial↔material-document
  link (SER03/OBJK — needs an IT-built query, not available in the web viewer).

## Attribution model (hybrid)

- **Historical orders**: back-fill by tracing where each work order's output
  was consumed upward (top-code trace via old transactions), or import an
  attribution CSV.
- **New kitting**: entered manually at kitting time — the operator knows the
  contract/fibre pair from the ASP plan. Entries persist in the browser and
  export/import as `amps_attribution.csv` (columns: order, contract,
  fibre_pair) so they survive browser changes and can be shared.

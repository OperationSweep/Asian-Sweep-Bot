# SAP ZPRO + CO04 kitting automation

Reads the fibre-pair scan workbook, posts each work order's serial numbers
through **ZPRO**, reprints the range through **CO04**, and saves one PDF per
work order.

Mistral supervises. It does not press Post. [Why](#stage-2--architecture).

---

## Stage 1 — What the workbook actually contains

The uploaded `ZPRO.xlsx` was inspected before any design work. It is
**column-oriented**, which drives everything downstream:

```
        A                 B            C            ...      Y
 1   GFF Allocation     M1/M2        M3/M4          ...   M47/M48     <- fibre pairs
 2   Work Order s/n   1008752nn    1008752nn        ...  1008752nn    <- work orders
 3   Amp Tray s/n     YAF03nnnnnn  YAF03nnnnnn      ...      0        <- component rows
 4   <material code>  TP2603Annnn  TP2603Annnn      ...
 ...                                                                     col A = material
37   <material code>  AAE2055nnn   AAE2055nnn       ...
38                        1            2            ...     24        <- index row
```

One column = one fibre pair = one work order. One row = one component material.
A serial lives at the intersection.

**Measured** (second revision of the sheet, a normal full 24-pair
transaction): 24 work orders, 35 component rows, **504 serial numbers, zero
duplicates**.

Six findings that changed the design:

**1. `Serial Number missing for …` names a *material*, not a serial.**
The material you quoted has the shape `92RRA…`, and column A holds a
`92RRA…` code at rows 12–13 — the same shape. No serial in the sheet looks
like that; the serial families are `TP2603A…`, `AAA21…`, `1D25…`, `2B26…`,
`YAF03…`. Ten materials carry no serial anywhere, which is exactly why SAP
asks for them.

That distinction is the safety mechanism. The same sentence is benign or
critical depending on which material it names:

| SAP says the serial is missing for… | Verdict | Why |
|---|---|---|
| a material the sheet never serialises | `EXPECTED_WARNING`, continue | bulk part, expected every run |
| a material the sheet **does** serialise | `CRITICAL_ERROR`, stop | your serials did not land |
| a material not in the sheet at all | `UNKNOWN_MESSAGE`, stop | operator confirms |

An automation that pattern-matched the text alone would confirm past a real
posting failure. It looks identical on screen.

**2. Rows 1–3 are formulas; the work orders are an external link.**
Rows 4–37 (the scanned serials) are typed values, but the fibre-pair labels,
the work order numbers and the amp tray serials are computed — the latter two
linked to another workbook on SharePoint. Any reader gets **whatever Excel
cached last**. A stale cache posts serials against the wrong orders.

Pre-flight raises `COMPUTED_WORK_ORDERS` every run. If the cache is empty the
run stops with instructions rather than a confusing "no order numbers".

**3. The work orders are not one unbroken run — and CO04 selects by range.**
This batch is two orders from one series and twenty-two from another, with a
gap of hundreds between them. A single `From`/`To` across that gap would select
**344 orders** where only 24 belong to the run, reprinting hundreds of
unrelated production documents.

So the reprint runs **once per contiguous block**, and pre-flight shows the
split before anything starts:

```
CO04 print ranges:
  <first> - <second>       (2 orders)
  <third> - <last>         (22 orders)
  These orders are not one unbroken run. Printed as a single range, CO04
  would select 344 orders instead of 24, so each block is selected separately.
```

Blocks are derived from *posted* orders only, so this also handles the other
case for free: an order that fails mid-batch splits the block around itself and
is excluded from the reprint.

**4. An earlier revision had `0` where the amp tray serial goes.**
Eight orders, a literal zero rather than a blank. The current sheet has a tray
serial on every order, but the handling stays: a `0` is never sent to SAP as
`"0"`, it is reported, and those orders simply carry one serial fewer.

**5. One stray cell.** `N45` holds a lone `TQ2603A…` serial, seven rows below the
block, under the 13th order. Not a duplicate of anything in the grid. It is reported,
never silently swept into a posting — someone should say what it was meant to be.

**6. The fibre-pair count does not need asking.** Row 1 labels M1/M2…M47/M48
and row 38 numbers 1–24. The sheet says 24. So the prompt is replaced by
detect-and-confirm, with `--limit N` when you are running a partial batch. One
less thing to mistype at 6am.

---

## Stage 2 — Architecture

```
Excel ─► reader ─► validator ─► [confirm] ─► ZPRO ─► state ─► CO04 ─► PDF split ─► verify
           │           │                       │       │                              │
           └───────────┴──────── audit log ────┴───────┴──────────────────────────────┘
                                      │
                            Mistral (advisory only)
```

You asked me to compare three options and recommend one.

| | Who decides to post | Verdict |
|---|---|---|
| **A** Python app, Mistral for reasoning | Python | workable |
| **B** Mistral Agent owns the tools | the model | **rejected** |
| **C** Deterministic Python, Mistral advises | Python | **recommended** |

**Why B is rejected specifically.** Under B the model chooses when to call
`post_goods_issue()`. A goods issue is irreversible and moves real stock. One
mis-sequenced call — a retry after a posting that actually succeeded, a tool
result misread — costs a stock correction, not a re-run. And there is nothing
here the model needs that freedom for: the sequence is five fixed steps, and
the workbook already states exactly what should happen.

**What Mistral does:**
- interprets an SAP message no rule matched, returning retry/skip/stop with a reason
- writes the plain-language run summary for the operator and the log

**What Mistral cannot do:** press a key, post, retry, choose a work order,
invent a serial, or resolve anything on its own. `interpret_message` returns a
recommendation; `orchestrator._decide` makes the call. A `continue` below 0.8
confidence is treated as `stop` — the model saying it is unsure *is* the signal.
If the API is down the run stops, as the rules already said.

With `mistral.enabled: false` (the default) the system is fully deterministic
and makes zero API calls. **Start there.** Turn Mistral on once you have seen
what real messages look like.

---

## Stage 3 — SAP automation strategy

**SAP GUI Scripting via `win32com.client`**, per your preference order. It
addresses controls by ID, so no mouse coordinates anywhere.

BAPI/RFC was considered and set aside: ZPRO is a custom transaction, so there
is no guarantee of a matching BAPI, and finding out costs ABAP-side
investigation you would have to commission. If your team confirms one exists
(`BAPI_GOODSMVT_CREATE` with serial numbers, say), that is a strictly better
back end — `sap/zpro.py` is the only module that would change.

pywinauto is used for exactly one thing: the Windows save dialog, which is
outside SAP's object model. Screen/image automation is not used at all.

---

## Stage 4 — Data model

```python
Workbook
├── jobs: [Job]
│   ├── work_order: "1008752nn"
│   ├── fibre_pair: "M1/M2"
│   ├── column_letter: "B"
│   ├── serials: [ComponentSerial(material, serial, sheet_row, sequence)]
│   └── anomalies: [Anomaly]
├── serialised_materials:     [...]   # drives message classification
├── non_serialised_materials: [...]   # drives message classification
└── anomalies: [Anomaly]
```

`job.to_dict()` gives the flat shape you specified:

```python
{"work_order": "1008752nn", "fibre_pair": "M1/M2", "serial_numbers": [...]}
```

Layout is **discovered, not assumed**: the reader finds the work-order row by
its column-A label, the data columns by what holds an order number, and the
component rows by where column A stops. A sheet with an extra header row or a
different pair count still parses.

---

## Stage 5 — State machine

```
LOAD_EXCEL → VALIDATE → CONNECT_SAP → AWAIT_CONFIRMATION
   → ZPRO ⟳ per order → VALIDATE_COMPLETION
   → CO04 → PRINT → VERIFY_FILES → COMPLETE
                                 ↘ HALTED
```

Per order: `PENDING → IN_PROGRESS → POSTED | FAILED | UNCERTAIN | SKIPPED`.

`UNCERTAIN` is the one that matters. Post was pressed and SAP did not clearly
confirm — a timeout, a terminated update, an unreadable reply. Whether stock
moved is unknowable from outside, so it is **never retried automatically**. A
lock or a busy object is different: SAP refused before posting, so that is
`FAILED` and safe to retry.

State is written to disk after every transition (temp-file-then-replace, so a
crash cannot corrupt the record of what posted). `resume` continues from the
last verified order, and refuses if the workbook changed since the run started.

---

## Stage 6 — Modules

```
app.py                        CLI: inspect | validate | zpro | print | full | resume
tools/discover_controls.py    reads SAP control IDs off a live screen
config.example.yaml           settings
controls.example.yaml         every SAP control ID, all null until you fill them
sap_agent/
  models.py                   Job / ComponentSerial / Anomaly, normalising
  excel/reader.py             layout discovery → jobs
  excel/validator.py          pre-flight + operator preview
  sap/connection.py           GUI Scripting wrapper; dry-run intercepts here
  sap/controls.py             controls.yaml, with failures that say what to do
  sap/messages.py             the classifier
  sap/zpro.py                 the ZPRO flow
  sap/co04.py                 the CO04 reprint
  sap/mock.py                 scriptable fake SAP for tests
  printing/pdf_writer.py      dialog handling, splitting, naming
  printing/pdf_validator.py   existence, size, page count, right-order check
  workflow/state.py           run state + the idempotency guard
  workflow/orchestrator.py    the state machine
  audit/log.py                CSV + JSONL, drops anything secret-shaped
```

### PDF naming — the part worth reading

You said: *never rely blindly on window order if a more reliable identifier is
available*. There is one — the work order is printed **on the document**. So
pages are matched by extracting the order number from the page text, not by
save-dialog sequence. If SAP emits them shuffled, the names are still right.

Both output shapes are handled: `combined_split` (one PDF, split by page
content — the default) and `per_document` (one dialog each, then identified by
content). A page that names no order is reported, never attributed to whatever
came before it. `pdf_validator` then re-opens every file and fails any whose
content does not mention the order it is named for — the exact mix-up that
attaches the wrong paperwork to a shipment.

---

## Stage 7 — Mistral integration

```yaml
mistral:
  enabled: true
  model: "mistral-medium-3505"
```
```
setx MISTRAL_API_KEY "..."
```

Structured output is forced through tool calling, so the reply is a typed
verdict rather than prose to parse:

```python
response = client.chat.complete(
    model=self.model,
    messages=[{"role": "system", ...}, {"role": "user", "content": prompt}],
    tools=[{"type": "function", "function": {"name": "answer",
                                             "parameters": RECOMMENDATION_SCHEMA}}],
    tool_choice="any",
    parallel_tool_calls=False,
)
verdict = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
```

The prompt carries both material lists, so the model reasons against your
actual build rather than general SAP knowledge. Cost is a handful of calls per
batch — only on messages the rules could not place.

**Driving it from Le Chat** is possible but not recommended yet: Le Chat runs
in Mistral's cloud and would need an inbound route to a machine logged into
production SAP. That is an IT decision, not a config flag. The CLI needs no
inbound network at all.

---

## Stage 8 — Testing

**157 tests, no SAP required.** `python -m pytest tests/ -q`

`sap/mock.py` is a scriptable fake session, so tests assert on the exact
keystroke sequence that would reach production:

- serials are all written **before** the checkbox is ticked, Post comes last
- a wrong order on screen aborts before anything is keyed
- a table too small to hold the serials aborts rather than truncating
- the three `Serial Number missing` verdicts
- resume does not repost; an `UNCERTAIN` order is never auto-retried
- PDFs shuffled in the print job still get the right names
- a PDF named for one order but containing another fails verification
- a two-series batch splits into the right print blocks, and a failed order
  splits the block around it
- the audit log drops a password even when handed one

**The real workbook is not in this repo.** It holds live serial numbers, ASN
part numbers and an internal SharePoint link, and this repository is public.
`tests/fixture.py` generates a synthetic workbook with the identical structure
— same layout, same formula-driven rows, same zero-instead-of-serial cells,
same stray cell, same two-block order numbering — so the tests exercise the
same paths. `tests/*.xlsx` is
gitignored.

---

## Stage 9 — Deployment on your Windows machine

**Once, with Basis:** profile parameter `sapgui/user_scripting = TRUE`. It is
off by default on many production systems and usually needs a change request.
Worth confirming before investing more time — nothing here works without it.

**Once, on your machine:**
1. SAP GUI → Options → Accessibility & Scripting → Scripting → **Enable
   scripting**, and untick both "notify when a script…" boxes, or every run
   stalls on a modal the script cannot dismiss.
2. `pip install -r requirements.txt`
3. `copy config.example.yaml config.yaml` and `copy controls.example.yaml controls.yaml`

**Then, in order:**

```bat
python app.py inspect  --sheet ZPRO.xlsx      :: what the workbook says
python app.py validate --sheet ZPRO.xlsx      :: pre-flight + unset controls
```

Discover the control IDs — this is the step nobody can do for you:

```bat
:: open the ZPRO selection screen, then:
python tools\discover_controls.py

:: open an order with Components View expanded, then:
python tools\discover_controls.py
python tools\discover_controls.py --window "wnd[1]"    :: for popups
```

Look for the field you type the order into:

```
GuiCTextField     wnd[0]/usr/ctxtP_AUFNR   tooltip='Order'
```

Paste it into `controls.yaml`. For the components table the tool prints its
type and columns: `GuiTableControl` → `serial_column` is the column **index**
(`"7"`); `GuiShell`/ALV → it is the column **name** (`"SERNR"`). Repeat on the
CO04 screens.

Then walk it up:

```bat
python app.py zpro --sheet ZPRO.xlsx --limit 1              :: dry run, prints every keystroke
python app.py zpro --sheet ZPRO.xlsx --limit 1 --execute    :: one order, for real
python app.py full --sheet ZPRO.xlsx --execute              :: the batch
python app.py resume --sheet ZPRO.xlsx --execute            :: after a halt
```

Dry run is the default everywhere; `--execute` is the only thing that lets a
keystroke reach SAP. A dry run works before any control is discovered, so you
can rehearse the shape of a batch on day one.

### Interface

CLI first, deliberately. It is the only interface that works over RDP, logs
everything by construction, and has no UI state to desync from run state. A
Streamlit wrapper is easy to add later once the flow is proven — the
orchestrator already takes a `confirmer` callback and reports progress, so a UI
is a front end over the same calls, not a rewrite.

---

## Safety

Every safeguard you listed, and where it lives:

| | |
|---|---|
| Dry run by default | `app.py`, `connection.py` |
| Pre-flight blocks before SAP | `excel/validator.py` |
| Duplicate-post protection | `state.may_post()` — POSTED/UNCERTAIN/IN_PROGRESS all refuse |
| Never post an unknown order | orders must be registered from the sheet |
| Never invent a serial | serials only ever come from cells; `0` and blanks are dropped |
| Never modify the input | the workbook is opened read-only |
| Stop on unknown SAP error | `UNKNOWN_MESSAGE` halts; the model cannot override below 0.8 confidence |
| No passwords in source | env vars only; the audit log drops secret-shaped fields |
| Verify screen before Post | `_verify_order_on_screen` |
| Confirm serial count | `_verify_serial_count`, plus a table-capacity check |
| Confirm CO04 range | gap detection refuses a range containing unposted orders |
| No accidental physical printing | printer name is config, `Microsoft Print to PDF` by default |
| Resume from last verified order | `state.py` + `app.py resume` |
| Human confirmation before posting | typed `START`, skippable with `--yes` once proven |

Two that are not on your list but follow from the data: PDFs are never silently
overwritten, and a resumed run refuses a workbook whose contents changed.

> Specific serial numbers, order numbers and the linked workbook's location are
> deliberately not reproduced here — this repository is public. The analysis
> above was performed against the real file; the values live in your workbook.

## Known gaps

- **`spool` PDF strategy is a stub.** It needs a PDF device type only Basis can
  create. `combined_split` and `per_document` are implemented.
- **No table scrolling.** If ZPRO shows fewer rows than an order has serials,
  the run stops rather than truncating. Paging can be added once we know the
  control type.
- **`sap/zpro.py`, `sap/co04.py`, `printing/pdf_writer.py` have not run against
  real SAP.** They cannot be, from here. Everything else is tested.

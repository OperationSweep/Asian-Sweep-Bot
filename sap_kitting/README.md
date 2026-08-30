# SAP ZPRO kitting automation

Reads a scan spreadsheet, runs each work order through transaction **ZPRO**, and
saves one PDF per order named after the work order number.

Mistral is optional and deliberately kept out of the keystroke path. See
[Where Mistral fits](#where-mistral-fits).

---

## The honest constraint, first

A Mistral agent runs in Mistral's cloud. SAP GUI runs on your Windows desktop.
**Nothing in Mistral's cloud can reach your SAP GUI session directly.** So no
amount of agent configuration alone will do this - something has to run locally.
That something is this package.

The workable shapes, cheapest first:

| Shape | What runs locally | Mistral's role | Inbound network needed |
|---|---|---|---|
| **1. Script** (start here) | `run.py` | none, or API calls out to Mistral | no |
| **2. Chat-driven** | `kitting/mcp_server.py` | Le Chat calls your MCP tools | yes - a tunnel |
| **3. Studio agent** | same MCP server | a Studio agent deployed into Le Chat | yes - a tunnel |

Shape 1 gets you the 70% saving. Shapes 2 and 3 only add a chat interface on
top, and they require exposing a machine that is logged in to production SAP to
an inbound connection - an IT decision, not a config flag. Get shape 1 working
first.

---

## Prerequisites

**On the Windows machine, once:**

1. SAP GUI for Windows (SAP GUI for Java has no scripting API).
2. Server-side: profile parameter `sapgui/user_scripting = TRUE`. Only Basis can
   set this, and on many production systems it is off by default. **Ask them
   first** - scripting is a supported SAP feature, but turning it on is their
   call and some sites require a change request.
3. Client-side: SAP GUI > Options > Accessibility & Scripting > Scripting >
   tick **Enable scripting**, and untick both *Notify when a script attaches to
   SAP GUI* and *Notify when a script opens a connection*. Left ticked, every
   run stalls on a modal the script cannot dismiss.
4. `pip install -r requirements.txt`

Verify scripting is live before anything else - open SAP GUI, then:

```
python inspect_screen.py
```

If that prints your system name and an element tree, you are ready. If it
cannot attach, stop here and fix step 2 or 3; nothing downstream will work.

---

## Setup

### 1. Find the ZPRO field IDs

ZPRO is a custom transaction, so its screen element IDs exist only on your
system. Nobody can supply them - you read them off your own screen:

```
# open ZPRO in SAP GUI, then:
python inspect_screen.py
```

Look for the field you normally type the order number into:

```
GuiCTextField     wnd[0]/usr/ctxtP_AUFNR  tooltip='Order'
```

Put that ID in `config.yaml` under `transaction.fields.order_number`.

While you are there, run `python inspect_screen.py` again **on the ZPRO output
screen** and look for an export or PDF button. If ZPRO has one, note its ID -
it makes the PDF step far more reliable than printing.

### 2. Configure

```
cp config.example.yaml config.yaml
```

Fill in: the SAP connection name, the ZPRO field ID from step 1, your
spreadsheet's column headers, and the PDF output folder.

`submit_vkey` is the key that runs the report after you type the order:
`0` = Enter, `8` = F8/Execute. Most Z report transactions use 8.

### 3. Check the sheet parses

```
python run.py --sheet kitting.xlsx
```

Dry run is the default. It prints every work order it found and the exact
keystrokes it would send, and touches SAP not at all. Confirm the order numbers
and component counts match what the kitter scanned.

### 4. One order for real

```
python run.py --sheet kitting.xlsx --only 4500123456 --execute
```

Watch it drive SAP. Check the PDF. Only then run the full batch:

```
python run.py --sheet kitting.xlsx --execute
```

---

## Getting the PDF out

The one genuinely site-specific step, because it depends on how ZPRO renders
output. Three strategies in `config.yaml` under `pdf.strategy`:

- **`preview_button`** - ZPRO's output screen has its own export/PDF button.
  Best when it exists. Needs `pdf.preview_button.button_id` from
  `inspect_screen.py`.
- **`pdf_printer`** *(default)* - prints to a SAP output device mapped to a
  Windows virtual PDF printer, then types the filename into the Windows save
  dialog. Works nearly everywhere. The weak point is the save dialog: its title
  is localised, so if your Windows is not English, set
  `pdf.pdf_printer.save_dialog_title` to the actual title.
- **`spool`** - print to a spool with a PDF device type, then download. Cleanest
  for unattended runs, but needs Basis to create a PDF device
  (device type `PDF1`/`PDFUC`). Left as a stub with instructions, because the
  download path depends on the device they give you.

---

## Where Mistral fits

The SAP sequence is five fixed steps. A language model improvising them buys
nothing and can post the wrong thing to a production ERP, so `zpro.py` is plain
deterministic code and `brain.mode: none` is the default.

Mistral does two jobs that *are* hard to write rules for (`kitting/brain.py`):

**Column mapping.** When a new site sends a differently-labelled export:

```
export MISTRAL_API_KEY=...
python run.py --sheet new_site.xlsx --suggest-columns
```

It reads the headers and sample rows and prints YAML to paste into
`config.yaml`. Review it, paste it, and the steady-state run needs no LLM call
at all.

**Failure triage.** With `brain.mode: mistral`, when ZPRO throws a message the
code does not recognise, Mistral classifies it `retry` / `skip` / `stop` with a
one-line reason for the kitter. It cannot escalate to "press this key" - it
returns a verdict and `run.py` decides. `allow_write_tools` stays `false`.

Cost is negligible either way: a handful of calls per batch, only on failures.

### Driving it from Le Chat

Once shape 1 is solid and your IT team has settled the network question:

```
pip install "mcp[cli]"
python -m kitting.mcp_server --sheet kitting.xlsx --http --port 8000
```

That exposes `list_orders`, `kit_order`, and `sap_status`. Register the endpoint
as a custom MCP connector in Mistral AI Studio; connectors are centrally
registered and become available in Le Chat, so you can then say *"kit work order
4500123456"* in chat. `kit_order` defaults to `execute=False` and returns the
planned keystrokes, so the chat path is dry-run by default too.

---

## Files

```
run.py               CLI: dry run by default, --execute to drive SAP
inspect_screen.py    dumps SAP screen element IDs - run this first
config.example.yaml  every site-specific value, commented
kitting/
  models.py          WorkOrder / Component, order-number normalising
  sheet.py           spreadsheet -> WorkOrder objects
  sap.py             SAP GUI Scripting wrapper; dry-run intercepts here
  zpro.py            the ZPRO flow
  pdf.py             the three PDF export strategies
  brain.py           optional Mistral: column mapping + failure triage
  mcp_server.py      optional: expose as MCP tools for Le Chat
tests/               pytest suite for the non-SAP logic
```

## Safety notes

- Dry run is the default everywhere, including the MCP tool.
- Credentials come from `SAP_USER` / `SAP_PASSWORD` environment variables, never
  from `config.yaml`. Better still, log in to SAP by hand and let the script
  attach to the existing session - then it never handles a password at all.
- `run.stop_on_error: true` halts the batch on the first failure rather than
  ploughing through 40 orders posting the same mistake.
- PDFs are never silently overwritten; set `pdf.overwrite: true` if you want that.
- `config.yaml` is gitignored - it describes your production system.

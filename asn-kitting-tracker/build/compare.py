"""Run one scenario through the Excel workbook (LibreOffice recalculation) and the JS engine; report every difference.
usage: python3 compare.py scenario.json [--keep]   -> prints PASS/FAIL and returns (excel, engine) dicts when imported"""
import sys, os, json, subprocess, math, datetime
from openpyxl import load_workbook
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.environ.get("KIT_SCRATCH", "/tmp/claude-0/-home-user/0a9d6962-6e96-5f3a-ae3c-2b9037388c4d/scratchpad/t")
LO = "/opt/lo26/root/opt/libreoffice26.2/program/soffice"
PROF = "file://" + os.path.join(os.path.dirname(S), "lo26prof")

def excel_outputs(scen, js):
    base = os.path.splitext(os.path.basename(scen))[0]
    raw = os.path.join(S, base + "_raw.xlsx"); outdir = os.path.join(S, "rc")
    sc = json.load(open(scen)); CLx = lambda n: __import__("openpyxl").utils.get_column_letter(n)
    nS = len(js["rv"]["summary"]); nR = len(js["rv"]["reps"]); nL = len(js["proposal"]["lines"]); nP = len(js["proposal"]["rows"])
    sc["_widen"] = {"Repeater View!E9": f"E9:{CLx(4 + max(nS, 1))}14", "Repeater View!B17": f"B17:{CLx(1 + 6 + nS)}17",
                    "Repeater View!B18": f"B18:{CLx(1 + 6 + nS)}{17 + max(nR, 1)}",
                    "Record Kitting!B19": f"B19:L{18 + max(nL, 1)}", "Record Kitting!N19": f"N19:AA{18 + max(nP, 1)}"}
    scen2 = os.path.join(S, base + "_w.json"); json.dump(sc, open(scen2, "w"))
    subprocess.run([sys.executable, os.path.join(HERE, "build_xlsx.py"), raw, scen2, "--test"], check=True, capture_output=True)
    subprocess.run([LO, "--headless", "--norestore", "-env:UserInstallation=" + PROF, "--convert-to", "xlsx:Calc MS Excel 2007 XML", "--outdir", outdir, raw],
                   check=True, capture_output=True)
    wb = load_workbook(os.path.join(outdir, base + "_raw.xlsx"), data_only=True)
    g = lambda sh, r, c: wb[sh].cell(r, c).value
    def block(sh, r0, c0, ncol, stop=lambda row: row[0] in (None, "", "#N/A")):
        out = []; r = r0
        while True:
            row = [wb[sh].cell(r, c0 + j).value for j in range(ncol)]
            if stop(row): break
            out.append(row); r += 1
        return out
    x = {}
    plan = block("Calc", 8, 1, 32, stop=lambda row: row[0] in (None, "", "#N/A") or row[0] > 1000)
    x["plan"] = [dict(aspRow=p[0], wsum=p[15], dEnd=p[16], dBefore=p[17], dNext4=p[18], valid=p[20], reqLines=p[21], built=p[22], complete=p[23],
                      partial=p[24], remaining=p[25], pct=p[26], dueThis=p[27], behind=p[28], shortage=p[29], topDiffers=p[30], status=p[31])
                 for p in plan if p[19] == 1]
    x["lines"] = [[l[0], l[1], l[3], l[6], l[7], l[8], l[9], l[11], l[12], l[15], l[16]] for l in block("Calc", 8, 34, 17)]
    x["coois"] = [[c[0], c[15], c[13] or "", c[7] or "", c[8] or "", c[10] or ""] for c in block("COOIS Review", 6, 1, 16)]
    lg = block("Kitting Log", 6, 1, 17, stop=lambda row: all(v in (None, "") for v in row[:14]))
    x["logCheck"] = [[l[0] or "", l[15], l[16] or ""] for l in lg]
    ad = [g("Dashboard", r, 30) for r in range(2, 11)]
    x["kpi"] = dict(plannedAll=ad[0], plannedCfg=ad[1], complete=ad[2], partial=ad[3], dueThis=ad[4], behind=ad[5], shortage=ad[8])
    summ = [[wb["Repeater View"].cell(r, c).value for r in range(9, 15)] for c in range(5, 32)]
    msg = lambda v: isinstance(v, str) and (v.startswith("Assembly setup") or v.startswith("No repeaters"))
    x["rv"] = {"summary": [s for s in summ if s[0] not in (None, "", "#N/A") and not msg(s[0])],
               "reps": [r for r in block("Repeater View", 18, 2, 30) if not msg(r[0])]}
    x["proposal"] = {"lines": [[l[0], l[3], l[4], l[5], l[6], l[7], l[8], l[9]] for l in block("Record Kitting", 19, 2, 11)],
                     "rows": block("Record Kitting", 19, 14, 14)}
    x["thisWeek"] = g("Repeater View", 5, 14)
    x["_wb"] = wb
    errs = []
    for ws in wb.worksheets:
        if ws.title in ("ASP", "COOIS"): continue
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if isinstance(v, str) and v.startswith("#") and v.rstrip("!?/0") in ("#VALUE", "#REF", "#NAME", "#DIV", "#NUM", "#CALC", "#SPILL", "#NULL"):
                    errs.append(f"{ws.title}!{cell.coordinate}={v}")
    x["_errors"] = errs
    return x

def engine_outputs(scen):
    return json.loads(subprocess.run(["node", os.path.join(HERE, "engine_run.js"), scen], check=True, capture_output=True, text=True).stdout)

def norm(v):
    if v is None: return ""
    if isinstance(v, bool): return int(v)
    if isinstance(v, datetime.datetime): return (v - datetime.datetime(1899, 12, 30)).days
    if isinstance(v, float) and abs(v - round(v)) < 1e-9: return int(round(v))
    if isinstance(v, float): return round(v, 6)
    return v

def compare(scen, quiet=False):
    js = engine_outputs(scen); xl = excel_outputs(scen, js)
    diffs = []
    def cmp(path, a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            for k in b: cmp(f"{path}.{k}", a.get(k), b[k])
        elif isinstance(b, list):
            a = a or []
            if len(a) != len(b): diffs.append(f"{path}: excel {len(a)} rows vs engine {len(b)}")
            for i, (p, q) in enumerate(zip(a, b)): cmp(f"{path}[{i}]", p, q)
        else:
            if norm(a) != norm(b): diffs.append(f"{path}: excel={a!r} engine={b!r}")
    # rep rows: trim excel rows to engine width
    xr = xl["rv"]["reps"]; jr = js["rv"]["reps"]
    if jr: xl["rv"]["reps"] = [r[:len(jr[0])] for r in xr]
    xl["rv"]["summary"] = [s[:len(js["rv"]["summary"][0])] for s in xl["rv"]["summary"]] if js["rv"]["summary"] else xl["rv"]["summary"]
    xl["proposal"]["rows"] = [r for r in xl["proposal"]["rows"] if not str(r[0]).startswith("Nothing")]
    if js["proposal"]["blocking"]: xl["proposal"]["lines"] = []; js["proposal"]["lines"] = []
    key = lambda r: (str(r[2]), str(r[5]), str(r[9]))
    xl["proposal"]["rows"].sort(key=key); js["proposal"]["rows"].sort(key=key)
    js["proposal"].pop("blocking")
    cmp("", {k: v for k, v in xl.items() if k not in ("_wb", "_errors")}, js)
    if xl["_errors"]: diffs.append(f"{len(xl['_errors'])} formula error cells: " + ", ".join(xl["_errors"][:8]))
    if not quiet:
        print(("PASS" if not diffs else "FAIL") + f"  {os.path.basename(scen)}  ({len(js['plan'])} plan rows, {len(js['lines'])} lines, {len(js['coois'])} orders, "
              f"{len(js['logCheck'])} log rows, {len(js['rv']['reps'])} REP rows, {len(js['proposal']['rows'])} proposal rows)")
        for d in diffs[:40]: print("   ", d)
    return xl, js, diffs

if __name__ == "__main__":
    compare(sys.argv[1])

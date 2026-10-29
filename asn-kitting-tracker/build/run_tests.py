"""Scenario tests. Each step is run through BOTH the Excel workbook (recalculated by LibreOffice) and the JS engine;
compare.py fails the step if any shown number or flag differs. The assertions below then check the business rules.
Synthetic data is labelled TEST in every project / order / variant name it invents.
usage: python3 run_tests.py [scenario-name ...]"""
import sys, os, json, copy, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import compare, S

BASE = json.load(open(os.path.join(S, "base.json")))      # real ASP + COOIS + reference requirements (scen_from_files.py)
def serial(y, m, d): return (datetime.date(y, m, d) - datetime.date(1899, 12, 30)).days
LOGC = ["Entry ID", "Entry date", "Record type", "Variant ID", "Stage", "Assembly code", "REPs kitted", "REP from", "REP to", "Order", "Order qty", "Void", "Void reason", "Note"]

RESULTS = []
def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail)); print(("   ok   " if cond else "   FAIL ") + name + ("" if cond else "  -> " + str(detail)))

def run(tag, sc):
    p = os.path.join(S, f"{tag}.json"); json.dump(sc, open(p, "w"))
    xl, js, diffs = compare(p)
    check(f"{tag}: Excel and engine agree", not diffs, diffs[:3])
    return xl, js

def confirm(sc, js):
    """simulate Paste Values of the green block into the Kitting Log (rows exactly as proposed)"""
    for r in js["proposal"]["rows"]:
        sc["log"].append({c: ("" if v is None else v) for c, v in zip(LOGC, r)})
    sc.pop("entry", None)

def plan(js, variant): return next(p for p in js["plan"] if p["aspRow"] == variant) if isinstance(variant, int) else None
def prow(js, sc, variant):
    rows = [i for i, r in enumerate(sc["asp"]["rows"]) if r[7] == variant]
    return next(p for p in js["plan"] if p["aspRow"] == rows[0] + 2)
def line(js, variant, code, stage=None):
    return next(l for l in js["lines"] if l[0] == variant and l[2] == code and (stage is None or l[1] == stage))
def coois(js, order): return next(c for c in js["coois"] if c[0] == order)
def logchecks(js): return [c[2] for c in js["logCheck"]]

# ---------------------------------------------------------------- synthetic ASP / COOIS helpers
HDR = ["Export time", "PLAN_VERSION_SWAN", "Project Id", "Project Name", "Product", "Planning code", "Prod Id", "Friendly_name", "Seabed Temp",
       "Body Type", "Nber FP", "System Qty", "Planned Qty", "Prod. progress", "ISO Week of DR2M_CALCULATED", "ISO Week of DR2M_DEMAND_DATE"]
def weeks(start_y, start_w, n):
    out = []; y, w = start_y, start_w
    for _ in range(n):
        out.append(f"{y % 100} W{w}")
        last = 53 if y in (2026, 2032) else 52
        w += 1
        if w > last: y, w = y + 1, 1
    return out
def asp(rows, wk):
    header = HDR + wk
    body = []
    for r in rows:
        row = [serial(2026, 9, 4), "ASP TEST", r["pid"], r["proj"], r["product"], r.get("pc", "PC"), r["top"], r.get("fr"), "COLD", "T1",
               r.get("fp", 4), r["sys"], r["pl"], 0, None, None] + [r.get("w", {}).get(h) for h in wk]
        body.append(row)
    return {"header": header, "rows": body}
def co(rows):
    hdr = ["Order", "Order Type", "Material Number", "Material description", "Plant", "Batch", "Order quantity (GMEIN)", "Unit of measure (=GMEIN)",
           "Release date (actual)", "Delivered quantity (GMEIN)", "Created on", "Entered by", "Change date", "Last changed by", "System Status"]
    return {"header": hdr, "rows": [[o, "REP", m, "TEST " + m, "8000", None, q, "EA", d, 0, d, "TEST", d, "TEST", s] for o, m, q, d, s in rows]}

def real(**kw):
    sc = copy.deepcopy(BASE); sc["settings"]["reportDate"] = serial(2026, 10, 29); sc["log"] = []; sc.update(kw); return sc

# ================================================================= scenarios
def t00_empty_and_real():
    print("T00  Real ASP + COOIS with an empty log, and a workbook with no ASP / COOIS loaded")
    sc = real(entry={"variant": "E2A-R4P-T1-C", "stage": "PSB", "reps": 3}, rvVariant="E2A-R4P-T1-C")
    xl, js = run("t00a", sc)
    k = js["kpi"]
    check("real data: planned repeaters for set-up variants 403 (39 + 109 + 255)", k["plannedCfg"] == 403, k)
    check("real data: 7 kits due this week, 24 behind (26 W44, nothing recorded)", k["dueThis"] == 7 and k["behind"] == 24, k)
    e = copy.deepcopy(sc); e["asp"]["rows"] = []; e["coois"]["rows"] = []
    xl, js = run("t00b", e)
    check("empty ASP / COOIS: progress can still be recorded, no orders proposed, shortage 3 shown",
          [r[2] for r in js["proposal"]["rows"]] == ["Kitting Progress"] and js["proposal"]["lines"][0][7] == 3, js["proposal"])

def t01_shared_psb():
    print("T01  E2A 4FP and 12FP share PSB 91YAF03404AAA with different per-REP quantities")
    sc = real(entry={"variant": "E2A-R12P-T5-C", "stage": "PSB", "reps": 3}, rvVariant="E2A-R12P-T5-C")
    xl, js = run("t01a", sc)
    pl = js["proposal"]["lines"][0]
    check("12FP: 3 REPs x 3 PSB = 9 units required", pl[1] == 9, pl)
    check("12FP: 9 orders proposed", len([r for r in js["proposal"]["rows"] if r[2] == "COOIS order"]) == 9, len(js["proposal"]["rows"]))
    confirm(sc, js)
    sc["entry"] = {"variant": "E2A-R4P-T1-C", "stage": "PSB", "reps": 3}
    xl, js = run("t01b", sc)
    pl = js["proposal"]["lines"][0]
    check("4FP: 3 REPs x 1 PSB = 3 units required", pl[1] == 3, pl)
    first = {r["Order"] for r in sc["log"] if r["Record type"] == "COOIS order"}
    new = {r[9] for r in js["proposal"]["rows"] if r[2] == "COOIS order"}
    check("4FP proposal does not reuse the 9 orders allocated to 12FP", not (first & new) and len(new) == 3, first & new)
    l12 = line(js, "E2A-R12P-T5-C", "91YAF03404AAA"); l4 = line(js, "E2A-R4P-T1-C", "91YAF03404AAA")
    check("12FP PSB line: recorded 9, allocated 9, complete REPs 3", l12[3:6] == [9, 9, 9] and l12[7] == 3, l12)
    check("4FP PSB line untouched until confirmed", l4[3] == 0 and l4[4] == 0, l4)
    confirm(sc, js)
    xl, js = run("t01c", sc)
    check("after both entries: 12 PSB orders allocated, none twice", sum(1 for c in js["coois"] if c[0] in first | new and c[2]) == 12)
    check("all log rows OK", set(logchecks(js)) == {"OK"}, set(logchecks(js)))
    return sc

def t02_no_double_allocation(sc):
    print("T02  An order already allocated to one variant cannot be allocated again")
    sc = copy.deepcopy(sc)
    taken = next(r for r in sc["log"] if r["Variant ID"] == "E2A-R12P-T5-C" and r["Record type"] == "COOIS order")
    sc["log"].append(dict(taken, **{"Entry ID": "K00099", "Variant ID": "E2A-R4P-T1-C", "Note": "TEST manual duplicate"}))
    sc["entry"] = {"variant": "E2A-R4P-T1-C", "stage": "PSB", "reps": 1}
    xl, js = run("t02", sc)
    dup = [c for c in js["logCheck"] if c[2] == "Duplicate allocation - fix"]
    check("typed duplicate is flagged on both rows", len(dup) == 2, dup)
    check("proposal never offers an allocated order", not ({r[9] for r in js["proposal"]["rows"] if r[9]} & {r["Order"] for r in sc["log"] if r["Order"]}))
    sc["log"][-1]["Void"] = "Y"; sc["log"][-1]["Void reason"] = "TEST duplicate removed"
    sc.pop("entry")
    xl, js = run("t02b", sc)
    check("voiding the duplicate clears the flag and keeps the row (struck through)", "Duplicate allocation - fix" not in logchecks(js) and logchecks(js)[-1] == "Void", logchecks(js)[-3:])

def t03_new_coois_repeats(sc):
    print("T03  A new COOIS export repeats existing orders and adds new ones")
    sc = copy.deepcopy(sc)
    before = {r["Order"] for r in sc["log"] if r["Record type"] == "COOIS order"}
    sc["coois"]["rows"] = sc["coois"]["rows"] + [[f"9TEST{i:04d}", "REP", "91YAF03404AAA", "TEST new PSB", "8000", None, 1, "EA", serial(2026, 10, 28), 0, serial(2026, 10, 28), "TEST", None, None, "REL PRT"] for i in range(5)] \
        + [r for r in sc["coois"]["rows"] if r[0] in before][:3]          # three already-allocated orders appear twice
    xl, js = run("t03", sc)
    l12 = line(js, "E2A-R12P-T5-C", "91YAF03404AAA")
    check("allocations preserved, not double counted (12FP still 9 allocated)", l12[4] == 9, l12)
    check("new orders are unallocated and available", all(coois(js, f"9TEST{i:04d}")[2] == "" for i in range(5)))
    check("all log rows still OK", set(logchecks(js)) == {"OK"}, set(logchecks(js)))

def t04_missing_changed(sc):
    print("T04  An allocated order is missing or changed in a later export")
    sc = copy.deepcopy(sc)
    alloc = [r["Order"] for r in sc["log"] if r["Record type"] == "COOIS order"]
    gone, changed, qty = alloc[0], alloc[1], alloc[2]
    rows = [r for r in sc["coois"]["rows"] if r[0] != gone]
    for r in rows:
        if r[0] == changed: r[2] = "92YWS04548AAA"
        if r[0] == qty: r[6] = 2
    sc["coois"]["rows"] = rows
    xl, js = run("t04", sc)
    ck = {c[0]: c[2] for c in js["logCheck"]}
    rowck = {r["Order"]: js["logCheck"][i][2] for i, r in enumerate(sc["log"])}
    check("missing order flagged 'Not in current COOIS - review' (not treated as cancelled)", rowck[gone] == "Not in current COOIS - review", rowck[gone])
    check("material change flagged", rowck[changed] == "Material changed - review", rowck[changed])
    check("quantity change flagged", rowck[qty] == "Qty changed - review", rowck[qty])
    check("COOIS Review marks the changed order", coois(js, changed)[1] == "Material changed - review", coois(js, changed))
    check("history kept: 12FP PSB still shows 9 allocated", line(js, "E2A-R12P-T5-C", "91YAF03404AAA")[4] == 9)

def t05_shared_unallocated():
    print("T05  A shared order has no confirmed contract allocation")
    sc = real()
    xl, js = run("t05", sc)
    psb = [c for c in js["coois"] if c[0] and c[1].startswith("Shared")]
    check("unallocated PSB / shared-code orders show 'Shared code - no contract allocation'", len(psb) > 100, len(psb))
    p4 = prow(js, sc, "E2A-R4P-T1-C"); p12 = prow(js, sc, "E2A-R12P-T5-C")
    check("no contract gets credit from unallocated shared orders", p4["complete"] == 0 and p12["complete"] == 0)

def t06_cnf_before_picking():
    print("T06  CNF appears before physical picking")
    sc = real()
    for r in sc["coois"]["rows"]:
        if r[2] == "92YLS00548BAA": r[14] = "REL CNF PRC"
    xl, js = run("t06", sc)
    cnf = [c for c in js["coois"] if c[4] == "Yes"]
    check("CNF orders visible as CNF in COOIS Review", len(cnf) >= 28, len(cnf))
    pc = [c for c in js["coois"] if c[3] == "Yes" and c[4] == "Yes"]
    check("PCNF never read as CNF (no order has both tokens)", not pc, pc[:2])
    check("CNF does not make anything kitted (4FP LASA recorded 0, complete 0)", line(js, "E2A-R4P-T1-C", "92YLS00548BAA")[3] == 0
          and prow(js, sc, "E2A-R4P-T1-C")["complete"] == 0)

def t07_clsd():
    print("T07  An order is CLSD")
    sc = real(entry={"variant": "E2A-R4P-T1-C", "stage": "Boat", "reps": 20})
    xl, js = run("t07", sc)
    clsd = [c for c in js["coois"] if c[5] == "Yes"]
    check("CLSD order flagged for review", clsd and clsd[0][1] == "CLSD - review", clsd)
    check("CLSD order never proposed", clsd[0][0] not in {r[9] for r in js["proposal"]["rows"]})
    pl = js["proposal"]["lines"][0]
    check("Boat: 17 orders, 1 CLSD -> 16 available, shortage 4 for 20 REPs", pl[5] == 16 and pl[7] == 4, pl)

def t08_partial_and_shortage():
    print("T08  Partial assembly-stage update and a shortage")
    sc = real(entry={"variant": "E2A-R4P-T1-C", "stage": "Erbium", "assembly": "92RRA00548AAA", "reps": 2.5})
    xl, js = run("t08a", sc)
    pl = js["proposal"]["lines"]
    check("line-only entry: only the spool line is proposed (2.5 REPs x 8 = 20 units)", len(pl) == 1 and pl[0][1] == 20, pl)
    confirm(sc, js)
    xl, js = run("t08b", sc)
    sp = line(js, "E2A-R4P-T1-C", "92RRA00548AAA")
    check("spool line: 20 covered = 2 complete REPs, 3 started", sp[5] == 20 and sp[7] == 2 and sp[8] == 3, sp)
    p = prow(js, sc, "E2A-R4P-T1-C")
    check("stage and kit not complete (other erbium lines 0), partly kitted 3", p["complete"] == 0 and p["partial"] == 3, p)
    # shortage: only 8 PSB orders exist (TEST copy keeps 8 of 103) for 3 REPs x 3 on 12FP
    sc2 = real(entry={"variant": "E2A-R12P-T5-C", "stage": "PSB", "reps": 3})
    keep = [r for r in sc2["coois"]["rows"] if r[2] == "91YAF03404AAA"][:8]
    sc2["coois"]["rows"] = [r for r in sc2["coois"]["rows"] if r[2] != "91YAF03404AAA"] + keep
    xl, js = run("t08c", sc2)
    pl = js["proposal"]["lines"][0]
    check("9 needed, 8 available -> 8 proposed, shortage 1", pl[4] == 9 and pl[6] == 8 and pl[7] == 1, pl)
    confirm(sc2, js)
    xl, js = run("t08d", sc2)
    l = line(js, "E2A-R12P-T5-C", "91YAF03404AAA")
    check("PSB stage not fully covered: 9 recorded, 8 covered, 1 without order, complete REPs 2", l[3] == 9 and l[5] == 8 and l[6] == 1 and l[7] == 2, l)
    check("Repeater View summary shows PSB 2 complete, 1 unit short", [s for s in js["rv"]["summary"] if s[0] == "PSB"][0][1] == 2 and [s for s in js["rv"]["summary"] if s[0] == "PSB"][0][5] == 1,
          js["rv"]["summary"])
    sc2["coois"]["rows"].append(["9TEST0100", "REP", "91YAF03404AAA", "TEST later PSB", "8000", None, 1, "EA", serial(2026, 10, 30), 0, None, "TEST", None, None, "REL"])
    sc2["entry"] = {"variant": "E2A-R12P-T5-C", "stage": "PSB", "reps": 0}
    xl, js = run("t08e", sc2)
    check("later COOIS: REPs kitted = 0 proposes only the missing order", [r[9] for r in js["proposal"]["rows"]] == ["9TEST0100"], js["proposal"]["rows"])

def t09_asp_update():
    print("T09  ASP update adds or removes a variant without erasing recorded progress")
    sc = real(entry={"variant": "E2A-R4P-T1-C", "stage": "PSB", "reps": 2})
    xl, js = run("t09a", sc); confirm(sc, js)
    sc["asp"]["rows"] = [r for r in sc["asp"]["rows"] if r[7] != "E2A-R4P-T1-C"]
    new = list(sc["asp"]["rows"][0]); new[2:8] = ["HTEST", "TEST Project", "REPEATERS", "R5B12.8REP", "92ERPTEST1A++", "TEST-R8P-T1-C"]; new[11] = 5; new[12] = 5
    sc["asp"]["rows"].append(new)
    xl, js = run("t09b", sc)
    check("progress row kept and flagged 'Variant not in current ASP - review'", "Variant not in current ASP - review" in logchecks(js), logchecks(js))
    check("recorded units kept (4FP PSB recorded 2)", line(js, "E2A-R4P-T1-C", "91YAF03404AAA")[3] == 2)
    st = prow(js, sc, "TEST-R8P-T1-C")["status"]
    check("new variant appears with 'Assembly setup required'", st == "Assembly setup required", st)
    wb = xl["_wb"]
    msgs = [wb["Dashboard"].cell(r, 2).value for r in range(19, 26)]
    check("Dashboard data check lists the missing variant", any("E2A-R4P-T1-C" in str(m) for m in msgs), msgs)

def t10_year_end():
    print("T10  Kit target week crosses the end of a (53-week) year")
    wk = weeks(2026, 48, 12)
    sc = {"asp": asp([dict(pid="HTEST", proj="TEST YearEnd", product="REPEATERS", top="92ERP04548A++", fr="E2A-R4P-T1-C", sys=4, pl=4,
                           w={"27 W1": 1, "27 W2": 1, "27 W3": 1, "26 W53": 1})], wk),
          "coois": co([("8TEST0001", "91YAF03404AAA", 1, serial(2026, 12, 1), "REL")]),
          "requirements": BASE["requirements"], "stages": BASE["stages"], "settings": {"kitLead": 3, "reportDate": serial(2026, 12, 23)},
          "log": [], "rvVariant": "E2A-R4P-T1-C"}
    xl, js = run("t10", sc)
    reps = {r[0]: r for r in js["rv"]["reps"]}
    kw = {r[0]: r[2 + 6 + 1] for r in js["rv"]["reps"]}
    check("26 W53 -> kit 26 W50; 27 W1 -> 26 W51; 27 W2 -> 26 W52; 27 W3 -> 26 W53", [kw[1], kw[2], kw[3], kw[4]] == ["26 W50", "26 W51", "26 W52", "26 W53"], kw)
    check("report date 23 Dec 2026 is 26 W52", js["thisWeek"] == "26 W52", js["thisWeek"])
    p = js["plan"][0]
    check("due by end of 26 W52 = 3, before = 2 -> behind 2, due this week 1", (p["dEnd"], p["dBefore"], p["behind"], p["dueThis"]) == (3, 2, 2, 1), p)
    sc["settings"]["reportDate"] = serial(2027, 1, 4)
    xl, js = run("t10b", sc)
    check("report date 4 Jan 2027 is 27 W1; all 4 behind", js["thisWeek"] == "27 W1" and js["plan"][0]["behind"] == 4, (js["thisWeek"], js["plan"][0]))

def t11_missing_requirements():
    print("T11  Assembly requirements are missing")
    sc = real(entry={"variant": "E2A-R8P-T4-C", "stage": "PSB", "reps": 1}, rvVariant="E2A-R8P-T4-C")
    xl, js = run("t11", sc)
    check("ASP variant without Settings rows -> 'Assembly setup required'", prow(js, sc, "E2A-R8P-T4-C")["status"] == "Assembly setup required")
    check("nothing to paste for an unconfigured variant", js["proposal"]["rows"] == [])
    wb = xl["_wb"]
    check("Record Kitting explains why", any("Assembly setup required" in str(wb["Record Kitting"].cell(r, 5).value) for r in range(6, 15)))
    check("Repeater View says setup required", "Assembly setup required" in str(wb["Repeater View"].cell(18, 2).value))

def t12_management_order_change():
    print("T12  Management instruction changes the kitting order")
    sc = real(entry={"variant": "E2A-R4P-T1-C", "stage": "LASA", "reps": 2, "note": "TEST mgmt instruction: 4FP before 12FP"})
    xl, js = run("t12a", sc); confirm(sc, js)
    xl, js = run("t12b", sc)
    check("entry recorded against the variant actually kitted, no error", set(logchecks(js)) == {"OK"}, set(logchecks(js)))
    l = line(js, "E2A-R4P-T1-C", "92YLS00548BAA")
    check("4FP LASA: 2 REPs covered", l[5] == 2, l)
    check("12FP LASA untouched (still 0)", line(js, "E2A-R12P-T5-C", "92YLS00548BAA")[3] == 0)
    sc["entry"] = {"variant": "E2A-R12P-T5-C", "stage": "LASA", "reps": 1}
    xl, js = run("t12c", sc)
    taken = {r["Order"] for r in sc["log"] if r["Record type"] == "COOIS order"}
    check("shared LASA orders taken by 4FP are not offered to 12FP", not (taken & {r[9] for r in js["proposal"]["rows"]}))
    p4 = prow(js, sc, "E2A-R4P-T1-C"); p12 = prow(js, sc, "E2A-R12P-T5-C")
    check("plan comparison stays honest: 12FP still behind its own plan, not an error", p12["status"] == "Kit behind" and p4["status"] in ("Kit behind", "On track", "Kit due this week"), (p4["status"], p12["status"]))

def t13_rep_level_and_correction():
    print("T13  REP-level recording, contract-level pool and correction")
    sc = real(rvVariant="E2A-R4P-T1-C")
    for st_ in ["LASA", "PSB"]:
        sc["entry"] = {"variant": "E2A-R4P-T1-C", "stage": st_, "reps": 2, "from": 5, "to": 6}
        xl, js = run(f"t13_{st_}", sc); confirm(sc, js)
    sc["entry"] = {"variant": "E2A-R4P-T1-C", "stage": "LASA", "reps": 3}
    xl, js = run("t13_pool", sc); confirm(sc, js)
    xl, js = run("t13b", sc)
    reps = {r[0]: r for r in js["rv"]["reps"]}
    check("REP 5-6 LASA = Kitted (recorded REP numbers)", reps[5][2] == "Kitted" and reps[6][2] == "Kitted", (reps[5], reps[6]))
    check("contract-level 3 LASA shown as Kitted* on REP 1-3 (earliest open positions)", [reps[i][2] for i in (1, 2, 3, 4)] == ["Kitted*", "Kitted*", "Kitted*", ""], [reps[i][2] for i in (1, 2, 3, 4)])
    check("REP 5 next kit = POB, REP 1 next kit = PSB", reps[5][8] == "POB" and reps[1][8] == "PSB", (reps[5][8], reps[1][8]))
    pool_id = sc["log"][-1]["Entry ID"]
    for r in sc["log"]:
        if r["Entry ID"] == pool_id and r["Record type"] == "Kitting Progress": r["Void"] = "Y"; r["Void reason"] = "TEST wrong variant"
    xl, js = run("t13c", sc)
    reps = {r[0]: r for r in js["rv"]["reps"]}
    check("voiding one row voids the whole entry (progress + its orders)", sum(1 for c in js["logCheck"] if c[0] == pool_id and c[2] == "Void") == 4)
    check("after correction REP 1 LASA is open again; orders released", reps[1][2] == "" and line(js, "E2A-R4P-T1-C", "92YLS00548BAA")[4] == 2)

if __name__ == "__main__":
    only = set(sys.argv[1:])
    def want(n): return not only or n in only
    if want("t00"): t00_empty_and_real()
    if want("t01") or want("t02") or want("t03") or want("t04"):
        s1 = t01_shared_psb()
        if want("t02") or not only: t02_no_double_allocation(s1)
        if want("t03") or not only: t03_new_coois_repeats(s1)
        if want("t04") or not only: t04_missing_changed(s1)
    for n, f in [("t05", t05_shared_unallocated), ("t06", t06_cnf_before_picking), ("t07", t07_clsd), ("t08", t08_partial_and_shortage),
                 ("t09", t09_asp_update), ("t10", t10_year_end), ("t11", t11_missing_requirements), ("t12", t12_management_order_change),
                 ("t13", t13_rep_level_and_correction)]:
        if want(n): f()
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} checks passed")
    json.dump([{"check": n, "pass": ok, "detail": str(d)[:300]} for n, ok, d in RESULTS], open(os.path.join(S, "test-results.json"), "w"), indent=1)
    sys.exit(1 if bad else 0)

"""Inline SheetJS + engine (+ optional seed data) into one standalone HTML file.
usage: python3 build_html.py out.html sheetjs.js [seed-scenario.json]
  without a seed scenario the page starts with the reference requirements only (no ASN plan or order data)."""
import sys, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
out, sheetjs = sys.argv[1], sys.argv[2]
seedsrc = sys.argv[3] if len(sys.argv) > 3 else None
ref = json.load(open(os.path.join(HERE, "reference-data.json")))
seed = {"requirements": ref["requirements"], "stages": ref["stages"], "settings": {"kitLead": ref["settings"]["kitLead"], "reportDate": None}}
if seedsrc:
    sc = json.load(open(seedsrc))
    def trim(r):
        r = list(r)
        while r and r[-1] in (None, ""): r.pop()
        return r
    seed["asp"] = {"header": sc["asp"]["header"], "rows": [trim(r) for r in sc["asp"]["rows"]], "file": sc.get("aspFile", "ASP GH SME AUG 2026.xlsx"), "loadedAt": sc.get("loadedAt")}
    seed["coois"] = {"header": sc["coois"]["header"][:15], "rows": [r[:15] for r in sc["coois"]["rows"] if r and r[0] not in (None, "")], "file": sc.get("cooisFile", "export.xlsx"), "loadedAt": sc.get("loadedAt")}
html = open(os.path.join(HERE, "tracker.template.html")).read()
eng = open(os.path.join(HERE, "engine.js")).read()
lib = open(sheetjs).read()
for name, code in [("lib", lib), ("engine", eng)]:
    assert "</script" not in code.lower(), name
seedjs = json.dumps(seed, separators=(",", ":")).replace("</", "<\\/")
html = html.replace("/*__SHEETJS__*/", lib, 1).replace("/*__ENGINE__*/", eng, 1).replace("/*__SEED__*/null", seedjs, 1)
open(out, "w").write(html)
print("built", out, f"{len(html) / 1024:.0f} KB", "with ASN data" if seedsrc else "no ASN data")

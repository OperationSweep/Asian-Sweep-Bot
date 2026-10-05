from growtest import *
import datetime as dt
R={}
# ---------- TEST 1: new contract, 20 assemblies (> WKE's 16), plan across ISO year boundary, partial sets
wb=load()
add_rows(wb,"Contracts","tblContracts",[{"Contract ID":"TEST-R20P-T1","Friendly name":"Test project · 20FP","Project":"Test","Top-level assembly code":"92ERPTEST01A++",
   "Amps per repeater":20,"Total repeaters required":10,"Kit-release lead (weeks before final build)":2,"AMPS-build lead (weeks before final build)":1,
   "Plan revision":"Test rev A","Plan updated on":dt.date(2026,10,5),"Plan updated by":"Tester"}])
rows=[]
for i in range(1,21):
    q=5 if i==20 else 2; s=9 if i==20 else 7   # code20: 1 set + 4 ; others 3 sets + 1
    rows.append({"Contract":"TEST-R20P-T1","Assembly group":f"GROUP {1+(i-1)//5}","Assembly code":f"TST{i:03d}","Description":f"Test assembly {i}",
                 "Qty per repeater":q,"Cumulative supplied to date":s,"Updated on":dt.date(2026,10,5),"Updated by":"Tester","Source reference":"test"})
add_rows(wb,"Assemblies & Totals","tblAssemblies",rows)
add_rows(wb,"Weekly Plan","tblPlan",[{"Contract":"TEST-R20P-T1","Final build week (Monday)":d,"Repeaters planned":q} for d,q in
   ((dt.date(2026,12,21),2),(dt.date(2026,12,28),3),(dt.date(2027,1,4),1),(dt.date(2027,1,11),2))])
wb["Dashboard"]["C3"]="TEST-R20P-T1"; wb["Gantt"]["C3"]="TEST-R20P-T1"; wb["Gantt"]["C6"]=dt.date(2026,12,9)
v=run(wb,"t1"); d,P,lst=dash(v); g=v["Gantt"]
R["T1 errors"]=errs(v)
R["T1 list rows"]=len(lst); R["T1 kits"]=P["Kits (number or message)"]; R["T1 limiting row"]=[x for x in lst if x[1]=="TST020"]
R["T1 tiles"]=[d["B8"].value,d["D8"].value,d["E8"].value,d["H8"].value,d["J8"].value]
R["T1 schedule msg"]=d["C12"].value; R["T1 next action"]=d["C16"].value
wk=[g.cell(10,c).value for c in range(5,57)]; yr=[g.cell(9,c).value for c in range(5,57)]
R["T1 gantt weeks"]=wk[:8]; R["T1 gantt years"]=[y for y in yr[:8]]
R["T1 gantt rows"]={g[f"B{r}"].value:[(wk[c-5],g.cell(r,c).value) for c in range(5,57) if g.cell(r,c).value not in (None,"")] for r in (13,14,15,18)}
R["T1 dropdown name"]=str(v.defined_names["ContractList"].attr_text)
import json; print(json.dumps(R,indent=0,default=str))

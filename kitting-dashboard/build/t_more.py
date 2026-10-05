from growtest import *
import datetime as dt, json
R={}
E2A="E2A-R12P-T5-C"
# ---- T2 duplicate key + T3 incomplete (blank qty) + T4 contract w/o assemblies
wb=load()
add_rows(wb,"Assemblies & Totals","tblAssemblies",[{"Contract":E2A,"Assembly group":"ERBIUM ASSY","Assembly code":"92RRA00548AAA","Description":"dup test","Qty per repeater":24,"Cumulative supplied to date":10,"Updated on":dt.date(2026,10,5)}])
v=run(wb,"t2"); d,P,lst=dash(v)
R["T2 duplicate: kits tile"]=d["B8"].value; R["T2 setup line"]=d["C15"].value; R["T2 next"]=d["C16"].value
R["T2 check values in list"]=sorted({x[10] for x in lst}); R["T2 rows"]=len(lst)
asm=v["Assemblies & Totals"]; R["T2 sheet checks"]=[asm.cell(r,12).value for r in range(8,asm.max_row+1) if asm.cell(r,3).value=="92RRA00548AAA"]
wb=load()
rows,_=find_rows(wb,"Assemblies & Totals","tblAssemblies",lambda x:x["Contract"]==E2A and x["Assembly code"]=="92UAP04548BCA")
setcell(wb,"Assemblies & Totals","tblAssemblies",rows[0],"Qty per repeater",None)
v=run(wb,"t3"); d,P,lst=dash(v)
R["T3 blank qty: kits tile"]=d["B8"].value; R["T3 setup"]=d["C15"].value; R["T3 row"]=[x for x in lst if x[1]=="92UAP04548BCA"]
wb=load(); wb["Dashboard"]["C3"]="E2A-R4P-T1-C"; wb["Gantt"]["C3"]="E2A-R4P-T1-C"
v=run(wb,"t4"); d,P,lst=dash(v)
R["T4 no assemblies: kits"]=d["B8"].value; R["T4 list"]=d["B21"].value; R["T4 next"]=d["C16"].value; R["T4 setup"]=d["C15"].value; R["T4 gantt D18"]=v["Gantt"]["C19"].value
R["T4 contracts check"]=[(v["Contracts"].cell(r,1).value,v["Contracts"].cell(r,13).value) for r in range(8,20) if v["Contracts"].cell(r,1).value]
# ---- T5 plan edits on E2A: move W42 housing (2026-10-12, qty2) -> 2026-11-02 ; split W43 (3) -> 1 + new 2 on 2026-10-26 ; increase W44 1->4 ; cancel W45 (delete)
wb=load()
def prow(date): return find_rows(wb,"Weekly Plan","tblPlan",lambda x:x["Contract"]==E2A and x["Final build week (Monday)"] and x["Final build week (Monday)"].date()==date)[0]
base=None
r42=prow(dt.date(2026,10,12)); r43=prow(dt.date(2026,10,19)); r44=prow(dt.date(2026,10,26)); r45=prow(dt.date(2026,11,2))
R["T5 found rows"]=[r42,r43,r44,r45]
setcell(wb,"Weekly Plan","tblPlan",r42[0],"Final build week (Monday)",dt.datetime(2026,11,9))
setcell(wb,"Weekly Plan","tblPlan",r43[0],"Repeaters planned",1)
setcell(wb,"Weekly Plan","tblPlan",r44[0],"Repeaters planned",4)
delete_row(wb,"Weekly Plan","tblPlan",r45[0])
add_rows(wb,"Weekly Plan","tblPlan",[{"Contract":E2A,"Final build week (Monday)":dt.date(2026,10,26),"Repeaters planned":2,"Note":"split from W43"}])
v=run(wb,"t5"); d,P,lst=dash(v); g=v["Gantt"]
R["T5 due now (was 31)"]=P["Kits due by this week"]; R["T5 next4 (was 2)"]=P["Kits due next 4 weeks"]; R["T5 scheduled (was 126)"]=P["Scheduled total"]
R["T5 schedule msg"]=d["C12"].value
wk=[g.cell(10,c).value for c in range(5,57)]
R["T5 gantt housing"]=[(wk[c-5],g.cell(15,c).value) for c in range(5,57) if g.cell(15,c).value not in (None,"")][:14]
R["T5 supplied unchanged"]=d["B8"].value
# ---- T6 lead time change: E2A kit lead 2->3
wb=load()
rr,_=find_rows(wb,"Contracts","tblContracts",lambda x:x["Contract ID"]==E2A)
setcell(wb,"Contracts","tblContracts",rr[0],"Kit-release lead (weeks before final build)",3)
v=run(wb,"t6"); d,P,lst=dash(v); g=v["Gantt"]; wk=[g.cell(10,c).value for c in range(5,57)]
R["T6 due now with lead 3"]=P["Kits due by this week"]; R["T6 tile sub"]=d["D9"].value
R["T6 gantt kit row"]=[(wk[c-5],g.cell(13,c).value) for c in range(5,57) if g.cell(13,c).value not in (None,"")][:8]
# ---- T7 supplied totals update incl partial + correction (reduce) + target entered
wb=load()
def arow(code): return find_rows(wb,"Assemblies & Totals","tblAssemblies",lambda x:x["Contract"]==E2A and x["Assembly code"]==code)[0][0]
for code,qtot in (("92RRA00548AAA",336+10),("92YLS00548BAA",15),("92YLS00548BBA",29)):
    r=arow(code); setcell(wb,"Assemblies & Totals","tblAssemblies",r,"Cumulative supplied to date",qtot); setcell(wb,"Assemblies & Totals","tblAssemblies",r,"Updated on",dt.date(2026,10,5))
r=arow("92UAP04548BCA"); setcell(wb,"Assemblies & Totals","tblAssemblies",r,"Cumulative supplied to date",12); setcell(wb,"Assemblies & Totals","tblAssemblies",r,"Correction note","-1 duplicate counted")
wb["Dashboard"]["K18"]=15
v=run(wb,"t7"); d,P,lst=dash(v)
R["T7 kits (boat3 reduced to 12)"]=d["B8"].value
R["T7 rows"]=[x[1:9] for x in lst if x[1] in ("92RRA00548AAA","92YLS00548BBA","92UAP04548BCA")]
R["T7 target"]=d["L18"].value; R["T7 additional"]=P["Additional assemblies needed"]; R["T7 next"]=d["C16"].value
for k in list(R):
    pass
R["errors all tests"]={n:errs(load_workbook(f"/tmp/claude-0/-home-user-Asian-Sweep-Bot/0a9d6962-6e96-5f3a-ae3c-2b9037388c4d/scratchpad/out/rc/{n}_t.xlsx",data_only=True)) for n in ("t2","t3","t4","t5","t6","t7")}
print(json.dumps(R,indent=0,default=str))

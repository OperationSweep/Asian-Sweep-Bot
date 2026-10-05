"""R5B AMP Kitting Control: multi-contract, manual release log, plan vs kitted."""
import sys, json, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule, CellIsRule, DataBarRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as CL
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.workbook.properties import CalcProperties
from openpyxl.comments import Comment

OUT=sys.argv[1]; S=json.load(open(sys.argv[2]))
NAVY="141A26"; INK="1E2433"; ROSE="B0245E"; GREY="5D6576"; LINE="D9DDE5"; PANEL="F3F4F7"; WHITE="FFFFFF"; MUTE="AEB6C6"
OK="1F8A5B"; OK_S="DDF2E7"; WARN="A8660B"; WARN_S="FBF0DC"; CRIT="C0392B"; CRIT_S="FBE6E3"; INFO="3558B8"; INFO_S="E3EAFA"; BLUE="0000FF"; YEL="FFF2B3"
F="Arial"
def font(sz=11,b=False,c=INK,i=False): return Font(name=F,size=sz,bold=b,color=c,italic=i)
def fill(c): return PatternFill("solid",start_color=c,end_color=c)
thin=Side(style="thin",color=LINE); BOX=Border(top=thin,bottom=thin,left=thin,right=thin); BOT=Border(bottom=thin)
C=Alignment(horizontal="center",vertical="center",wrap_text=True); L=Alignment(horizontal="left",vertical="center",wrap_text=True)
def hdr(ws,r,c,t,bg=INK,h=None):
    x=ws.cell(r,c,t); x.font=font(10,True,WHITE); x.fill=fill(bg); x.alignment=C; x.border=BOX
def title(ws,t,sub):
    ws["A1"]=t; ws["A1"].font=font(16,True,NAVY); ws["A2"]=sub; ws["A2"].font=font(10,c=GREY,i=True)

NC=S.get("contract_rows",60); NK=S.get("kit_rows",600); NW=S.get("plan_rows",1500); NL=S.get("log_rows",4000)
SLOTS=S.get("slots",20); WEEKS=40; PAST=12
wb=Workbook()

# ================= Contracts =================
ct=wb.active; ct.title="Contracts"; ct.sheet_view.showGridLines=False
title(ct,"CONTRACTS — R5B AMP KITTING","One row per top-level code (++). Blue = inputs. Total repeaters can change when batches change (e.g. 109 → 117).")
C0=6; C1=C0+NC-1
ch=["Contract (Friendly name)","Project","Top Code (++)","FP","Amps / Repeater","Total Repeaters","Notes","Kit Lines","Repeaters Kitted","Amps Kitted","Plan to Date","Vs Plan","Total in Weekly Plan","% Kitted","Status","Last Release","Kit Lead (wks)"]
for j,h in enumerate(ch,1): hdr(ct,C0-1,j,h,ROSE if (j<=7 or j==17) else NAVY)
ct.row_dimensions[C0-1].height=32
KA=f"'Kit Lists'!$A$6:$A${5+NK}"; KI=f"'Kit Lists'!$I$6:$I${5+NK}"
WA=f"'Weekly Plan'!$A$6:$A${5+NW}"; WD=f"'Weekly Plan'!$D$6:$D${5+NW}"; WE=f"'Weekly Plan'!$E$6:$E${5+NW}"
LA=f"'Release Log'!$A$6:$A${5+NL}"; LB=f"'Release Log'!$B$6:$B${5+NL}"; LC=f"'Release Log'!$C$6:$C${5+NL}"; LD=f"'Release Log'!$D$6:$D${5+NL}"
ASOF="Dashboard!$Q$3"
for i in range(NC):
    r=C0+i
    if i<len(S["contracts"]):
        c=S["contracts"][i]
        for j,k in enumerate(["name","project","top","fp","amps","total","note"],1): ct.cell(r,j,c.get(k))
        ct.cell(r,17,c.get("lead",2))
    ct[f"H{r}"]=f'=IF(A{r}="","",COUNTIF({KA},A{r}))'
    ct[f"I{r}"]=f'=IF(OR(A{r}="",H{r}=0),"",_xlfn.MINIFS({KI},{KA},A{r}))'
    ct[f"J{r}"]=f'=IF(I{r}="","",I{r}*E{r})'
    ct[f"K{r}"]=f'=IF(A{r}="","",SUMIFS({WD},{WA},A{r},{WE},"<="&({ASOF}+7*N(Q{r}))))'
    ct[f"L{r}"]=f'=IF(I{r}="","",I{r}-K{r})'
    ct[f"M{r}"]=f'=IF(A{r}="","",SUMIFS({WD},{WA},A{r}))'
    ct[f"N{r}"]=f'=IF(OR(I{r}="",N(F{r})=0),"",I{r}/F{r})'
    ct[f"O{r}"]=(f'=IF(A{r}="","",IF(H{r}=0,"NO KIT LIST",IF(I{r}>=F{r},"COMPLETE",IF(L{r}>0,"AHEAD +"&L{r},IF(L{r}=0,"ON PLAN","BEHIND "&L{r})))))')
    ct[f"P{r}"]=f'=IF(A{r}="","",IF(COUNTIF({LB},A{r})=0,"–",_xlfn.MAXIFS({LA},{LB},A{r})))'
    for j in range(1,18):
        x=ct.cell(r,j); x.border=BOX; x.alignment=L if j in (1,2,3,7) else C
        x.font=font(10,j==1,BLUE if (j<=7 or j==17) else INK)
    ct[f"N{r}"].number_format="0%"; ct[f"P{r}"].number_format="dd-mmm-yy"
for c,w in zip("ABCDEFGHIJKLMNOPQ",[20,22,16,6,10,11,26,8,11,10,10,9,12,9,15,11,10]): ct.column_dimensions[c].width=w
ct.freeze_panes="B6"
for v,fc,bc in (("COMPLETE",OK,OK_S),("AHEAD",OK,OK_S),("ON PLAN",INFO,INFO_S),("BEHIND",CRIT,CRIT_S),("NO KIT",GREY,"ECEEF3")):
    ct.conditional_formatting.add(f"O{C0}:O{C1}",FormulaRule(formula=[f'LEFT($O{C0},{len(v)})="{v}"'],fill=fill(bc),font=Font(name=F,color=fc,bold=True)))
CN=f"Contracts!$A${C0}:$A${C1}"

# ================= Kit Lists =================
kl=wb.create_sheet("Kit Lists"); kl.sheet_view.showGridLines=False
title(kl,"KIT LISTS — SUB-ASSEMBLIES PER REPEATER (ZMRP BREAKDOWN)","One row per sub-assembly per contract: how many go into ONE repeater. Enter once per contract. Blue = inputs; grey columns calculate.")
kh=["Contract","Sequence","Assy Code","Assy Description","Qty per Repeater","Slot","Key","Released","Repeaters Kitted","Lookup"]
for j,h in enumerate(kh,1): hdr(kl,5,j,h,ROSE if j<=5 else NAVY)
for i in range(NK):
    r=6+i
    if i<len(S["kits"]):
        for j,v in enumerate(S["kits"][i],1): kl.cell(r,j,v)
    kl[f"F{r}"]=f'=IF(A{r}="","",COUNTIF($A$6:A{r},A{r}))'
    kl[f"G{r}"]=f'=IF(A{r}="","",A{r}&"|"&F{r})'
    kl[f"H{r}"]=f'=IF(A{r}="","",SUMIFS({LD},{LB},A{r},{LC},C{r}))'
    kl[f"I{r}"]=f'=IF(OR(A{r}="",N(E{r})=0),"",INT(H{r}/E{r}))'
    kl[f"J{r}"]=f'=IF(A{r}="","",A{r}&"|"&C{r})'
    for j in range(1,11):
        x=kl.cell(r,j); x.border=BOX; x.font=font(10,c=BLUE if j<=5 else GREY); x.alignment=L if j in (1,2,3,4) else C
for c,w in zip("ABCDEFGHIJ",[20,15,17,44,10,6,22,10,10,30]): kl.column_dimensions[c].width=w
kl.column_dimensions["G"].hidden=True; kl.column_dimensions["J"].hidden=True
kl.freeze_panes="A6"; kl.auto_filter.ref=f"A5:I{5+NK}"
dvk=DataValidation(type="list",formula1=f"={CN}",allow_blank=True); kl.add_data_validation(dvk); dvk.add(f"A6:A{5+NK}")
KG=f"'Kit Lists'!$G$6:$G${5+NK}"; KC=f"'Kit Lists'!$C$6:$C${5+NK}"; KB=f"'Kit Lists'!$B$6:$B${5+NK}"; KD=f"'Kit Lists'!$D$6:$D${5+NK}"; KE=f"'Kit Lists'!$E$6:$E${5+NK}"; KH=f"'Kit Lists'!$H$6:$H${5+NK}"; KJ=f"'Kit Lists'!$J$6:$J${5+NK}"

# ================= Weekly Plan =================
wp=wb.create_sheet("Weekly Plan"); wp.sheet_view.showGridLines=False
title(wp,"WEEKLY RELEASE PLAN — REPEATERS TO KIT PER WEEK","Release weeks from the plan / CO41. One row per contract per week. Only weeks with a quantity are needed.")
for j,h in enumerate(["Contract","ISO Year","ISO Week","Repeaters to Release","Week Starts (Mon)","Note"],1): hdr(wp,5,j,h,ROSE if j in (1,2,3,4,6) else NAVY)
for i in range(NW):
    r=6+i
    if i<len(S["plan"]):
        for j,v in enumerate(S["plan"][i],1): wp.cell(r,[1,2,3,4,6][j-1] if j<=5 else j,v)
    wp[f"E{r}"]=f'=IF(OR(B{r}="",C{r}=""),"",DATE(B{r},1,4)-WEEKDAY(DATE(B{r},1,4),2)+1+(C{r}-1)*7)'
    for j in range(1,7):
        x=wp.cell(r,j); x.border=BOX; x.font=font(10,c=GREY if j==5 else BLUE); x.alignment=L if j in (1,6) else C
    wp[f"E{r}"].number_format="dd-mmm-yy"
for c,w in zip("ABCDEF",[20,9,9,12,13,30]): wp.column_dimensions[c].width=w
wp.freeze_panes="A6"; wp.auto_filter.ref=f"A5:F{5+NW}"
dvw=DataValidation(type="list",formula1=f"={CN}",allow_blank=True); wp.add_data_validation(dvw); dvw.add(f"A6:A{5+NW}")

# ================= Release Log =================
lg=wb.create_sheet("Release Log"); lg.sheet_view.showGridLines=False
title(lg,"RELEASE LOG — EVERY KIT RELEASED TO PRODUCTION","One line per release: date, contract, assy code, qty. Negative qty corrects a mistake. This is the only sheet updated day to day.")
lg["A3"]="Example: 05-Oct-26 · E2A-R12P-T5-C · 92RRA00548AAA · 24 · N.Bakare · Rep 14"; lg["A3"].font=font(10,c=GREY)
for j,h in enumerate(["Date","Contract","Assy Code","Qty Released","Released By","Note (WO / repeater)","Description","Check"],1): hdr(lg,5,j,h,ROSE if j<=6 else NAVY)
for i in range(NL):
    r=6+i
    if i<len(S["log"]):
        d,cn,code,q,by,note=S["log"][i]
        lg[f"A{r}"]=datetime.date.fromisoformat(d); lg[f"B{r}"]=cn; lg[f"C{r}"]=code; lg[f"D{r}"]=q; lg[f"E{r}"]=by or None; lg[f"F{r}"]=note
    lg[f"G{r}"]=f'=IF(C{r}="","",IFERROR(INDEX({KD},MATCH(B{r}&"|"&C{r},{KJ},0)),"Not on this contract\'s kit list"))'
    lg[f"H{r}"]=f'=IF(AND(B{r}="",C{r}="",D{r}=""),"",IF(B{r}="","Missing contract",IF(C{r}="","Missing code",IF(LEFT(G{r},3)="Not","Wrong code",IF(D{r}="","Missing qty",IF(A{r}="","Missing date",""))))))'
    for j in range(1,9):
        x=lg.cell(r,j); x.border=BOX; x.font=font(10,c=BLUE if j<=6 else GREY); x.alignment=C if j in (1,4,8) else L
    lg[f"A{r}"].number_format="dd-mmm-yy"; lg[f"D{r}"].font=font(11,True,BLUE)
for c,w in zip("ABCDEFGH",[11,20,17,11,14,22,40,15]): lg.column_dimensions[c].width=w
lg.freeze_panes="A6"; lg.auto_filter.ref=f"A5:H{5+NL}"
for dv,rng in ((DataValidation(type="list",formula1=f"={CN}",allow_blank=True,showErrorMessage=True,error="Pick a contract from the Contracts sheet."),f"B6:B{5+NL}"),
               (DataValidation(type="list",formula1=f"={KC}",allow_blank=True),f"C6:C{5+NL}"),
               (DataValidation(type="whole",operator="notEqual",formula1="0",allow_blank=True,showErrorMessage=True,error="Whole number (negative to correct)."),f"D6:D{5+NL}"),
               (DataValidation(type="date",operator="greaterThan",formula1="40000",allow_blank=True,showErrorMessage=True,error="Enter a date"),f"A6:A{5+NL}")):
    lg.add_data_validation(dv); dv.add(rng)
lg.conditional_formatting.add(f"H6:H{5+NL}",FormulaRule(formula=['$H6<>""'],fill=fill(CRIT_S),font=Font(name=F,color=CRIT,bold=True)))

# ================= Calc (hidden) =================
ca=wb.create_sheet("Calc")
SEL="Dashboard!$D$3"
ca["A1"]="Helper sheet for the Dashboard chart and table — do not edit."
# slots rows 4..4+SLOTS-1: code, per
ca["A3"]="Slot"; ca["B3"]="Code"; ca["C3"]="Qty/Rep"
ca["D1"]=f"={ASOF}-{7*PAST}"
for c in range(WEEKS):
    ca.cell(2,4+c).value=f"=$D$1+{7*c}"; ca.cell(2,4+c).number_format="dd-mmm"
for s in range(SLOTS):
    r=4+s
    ca[f"A{r}"]=s+1
    ca[f"B{r}"]=f'=IFERROR(INDEX({KC},MATCH({SEL}&"|"&A{r},{KG},0)),"")'
    ca[f"C{r}"]=f'=IF(B{r}="","",INDEX({KE},MATCH({SEL}&"|"&A{r},{KG},0)))'
    for c in range(WEEKS):
        col=CL(4+c)
        ca[f"{col}{r}"]=f'=IF($B{r}="","",INT(SUMIFS({LD},{LB},{SEL},{LC},$B{r},{LA},"<="&MIN({col}$2+6,{ASOF}+6))/$C{r}))'
KR=4+SLOTS+1  # rows: week label, plan cum, kitted cum
ca[f"C{KR}"]="Week"; ca[f"C{KR+1}"]="Kit plan (cumulative)"; ca[f"C{KR+2}"]="Kitted (flat after today)"; ca[f"C{KR+3}"]="Contract total"
for c in range(WEEKS):
    col=CL(4+c)
    ca[f"{col}{KR}"]=f'="W"&_xlfn.ISOWEEKNUM({col}$2)'
    ca[f"{col}{KR+1}"]=f'=SUMIFS({WD},{WA},{SEL},{WE},"<="&({col}$2+7*Dashboard!$S$3))'
    ca[f"{col}{KR+2}"]=f'=IF(COUNT({col}4:{col}{3+SLOTS})=0,0,MIN({col}4:{col}{3+SLOTS}))'
    ca[f"{col}{KR+3}"]=f"=Dashboard!$H$3"
ca.sheet_state="hidden"

# ================= Dashboard =================
ds=wb.create_sheet("Dashboard",0); ds.sheet_view.showGridLines=False; ds.sheet_view.zoomScale=80
widths={"A":2,"B":13,"C":17,"D":36,"E":9,"F":10,"G":10,"H":10,"I":11,"J":12,"K":2,"L":10,"M":10,"N":10,"O":10,"P":10,"Q":12}
for k,v in widths.items(): ds.column_dimensions[k].width=v
for c in range(2,18):
    for r in (1,2,3,4): ds.cell(r,c).fill=fill(NAVY)
ds.row_dimensions[2].height=36; ds.row_dimensions[3].height=30
ds["B2"]="R5B AMP KITTING CONTROL"; ds["B2"].font=font(22,True,WHITE); ds["B2"].alignment=Alignment(vertical="center")
ds["B3"]="CONTRACT ▸"; ds["B3"].font=font(10,True,MUTE); ds["B3"].alignment=Alignment(horizontal="right",vertical="center")
ds.merge_cells("D3:F3"); ds["D3"]=S["default_contract"]; ds["D3"].font=font(16,True,WHITE); ds["D3"].fill=fill(ROSE); ds["D3"].alignment=C
for c in "EF": ds[f"{c}3"].fill=fill(ROSE)
dvs=DataValidation(type="list",formula1=f"={CN}",allow_blank=False); ds.add_data_validation(dvs); dvs.add("D3")
CR=f"MATCH({SEL},{CN},0)"
def cv(col): return f"INDEX(Contracts!${col}${C0}:${col}${C1},{CR})"
ds["G3"]="TOTAL REPS"; ds["G3"].font=font(9,True,MUTE); ds["G3"].alignment=Alignment(horizontal="right",vertical="center",wrap_text=True)
ds["H3"]=f"=IFERROR({cv('F')},0)"; ds["H3"].font=font(16,True,WHITE); ds["H3"].alignment=C
ds["I3"]="AMPS / REP"; ds["I3"].font=font(9,True,MUTE); ds["I3"].alignment=Alignment(horizontal="right",vertical="center",wrap_text=True)
ds["J3"]=f"=IFERROR({cv('E')},0)"; ds["J3"].font=font(16,True,WHITE); ds["J3"].alignment=C
ds["S3"]=f"=IFERROR(N({cv('Q')}),2)"; ds["S3"].font=font(8,c=NAVY)
ds["P3"]="AS OF ▸"; ds["P3"].font=font(10,True,MUTE); ds["P3"].alignment=Alignment(horizontal="right",vertical="center")
ds["Q2"]="=TODAY()"; ds["Q2"].font=font(10,c=MUTE); ds["Q2"].number_format="dd-mmm-yy"; ds["Q2"].alignment=C
ds["Q3"]="=Q2-WEEKDAY(Q2,2)+1"; ds["Q3"].font=font(13,True,WHITE); ds["Q3"].number_format='"W"00'; ds["Q3"].alignment=C
ds["Q3"].number_format="dd-mmm"
ds["P2"]="DATE"; ds["P2"].font=font(9,True,MUTE); ds["P2"].alignment=Alignment(horizontal="right",vertical="center")
ds["Q4"]='="Week "&_xlfn.ISOWEEKNUM(Q3)'; ds["Q4"].font=font(9,True,MUTE); ds["Q4"].alignment=C
ds["Q2"].comment=Comment("Leave =TODAY() or type a date to view the position as of that week.","Dashboard")
ds["B4"]=f'=IFERROR({cv("B")}&"  ·  top code "&{cv("C")}&"  ·  "&{cv("D")}&"FP  ·  "&{cv("H")}&" sub-assemblies per repeater"&IF({cv("G")}&""="","","  ·  "&{cv("G")}),"Pick a contract")'
ds["B4"].font=font(10,c=MUTE)
# KPI tiles rows 6-8
KIT=f"IFERROR({cv('I')},0)"
tiles=[("B","C","REPEATERS KITTED",f'=IF({cv("H")}=0,"–",{cv("I")}&" / "&$H$3)',f'=IFERROR(TEXT({cv("N")},"0%")&" of contract · "&($H$3-{KIT})&" to go","add a kit list for this contract")'),
       ("D","D","AMPS KITTED",f"=IFERROR({cv('J')},0)",f'="of "&TEXT($H$3*$J$3,"#,##0")&" amps ("&$J$3&" per repeater)"'),
       ("E","G","PLAN TO DATE",f"=IFERROR({cv('K')},0)",f'="kits due by "&$Q$4&" (housing "&"W"&_xlfn.ISOWEEKNUM($Q$3+7*$S$3)&", "&$S$3&"-wk lead)"'),
       ("H","J","VS PLAN",f'=IFERROR(IF({cv("H")}=0,"–",IF({cv("L")}>0,"+"&{cv("L")},{cv("L")})),"–")',f'=IFERROR({cv("O")},"")'),
       ("L","N","NEXT 4 WEEKS",f'=SUMIFS({WD},{WA},{SEL},{WE},">"&($Q$3+7*$S$3),{WE},"<="&($Q$3+7*$S$3+28))','="repeaters to kit next 4 weeks"'),
       ("O","Q","LAST RELEASE",f"=IFERROR({cv('P')},\"–\")",f'=COUNTIF({LB},{SEL})&" release lines logged"')]
ds.row_dimensions[6].height=20; ds.row_dimensions[7].height=52; ds.row_dimensions[8].height=28
for a,b,lab,val,sub in tiles:
    for r in (6,7,8):
        if a!=b: ds.merge_cells(f"{a}{r}:{b}{r}")
        ca_,cb_=ds[f"{a}{r}"].column,ds[f"{b}{r}"].column
        for c in range(ca_,cb_+1): ds.cell(r,c).fill=fill(PANEL); ds.cell(r,c).border=Border(left=Side(style="thick",color=ROSE) if c==ca_ else None)
    ds[f"{a}6"]=lab; ds[f"{a}6"].font=font(10,True,GREY); ds[f"{a}6"].alignment=Alignment(horizontal="left",vertical="bottom",indent=1)
    ds[f"{a}7"]=val; ds[f"{a}7"].font=font(30,True,NAVY); ds[f"{a}7"].alignment=Alignment(horizontal="left",vertical="center",indent=1)
    ds[f"{a}8"]=sub; ds[f"{a}8"].font=font(9,c=GREY); ds[f"{a}8"].alignment=Alignment(horizontal="left",vertical="top",indent=1,wrap_text=True)
ds["B7"].font=font(36,True,ROSE); ds["D7"].number_format="#,##0"; ds["O7"].number_format="dd-mmm-yy"; ds["O7"].font=font(22,True,NAVY)
ds.conditional_formatting.add("H7",FormulaRule(formula=['LEFT($H$7,1)="+"'],font=Font(name=F,size=30,bold=True,color=OK)))
ds.conditional_formatting.add("H7",FormulaRule(formula=['LEFT($H$7,1)="-"'],font=Font(name=F,size=30,bold=True,color=CRIT)))
# progress bar row 9
ds["B10"]="CONTRACT PROGRESS"; ds["B10"].font=font(10,True,GREY)
ds.merge_cells("D10:J10"); ds["D10"]=f'=IFERROR({cv("N")},0)'; ds["D10"].number_format="0%"; ds["D10"].font=font(10,True); ds["D10"].alignment=Alignment(horizontal="left",vertical="center")
ds.conditional_formatting.add("D10",DataBarRule(start_type="num",start_value=0,end_type="num",end_value=1,color=ROSE,showValue=True))
# target + sub-assy table
T0=14; T1=T0+SLOTS-1
ds["B12"]="SUB-ASSEMBLIES"; ds["B12"].font=font(13,True,NAVY)
ds["F12"]="RELEASE TARGET ▸"; ds["F12"].font=font(9,True,GREY); ds.merge_cells("F12:H12"); ds["F12"].alignment=Alignment(horizontal="right",vertical="center")
ds["I12"]="=IFERROR(INDEX(Contracts!$K$6:$K$65,MATCH(D3,Contracts!$A$6:$A$65,0))+L7,0)".replace("$K$65",f"$K${C1}").replace("$A$65",f"$A${C1}")
ds["I12"].font=font(14,True,WHITE); ds["I12"].fill=fill(ROSE); ds["I12"].alignment=C
ds["J12"]="reps · type to override"; ds["J12"].font=font(8,c=GREY,i=True)
for j,h in enumerate(["Sequence","Assy Code","Description","Qty / Rep","Released","Repeaters","Toward Next","Needed for Target","To Release"]): hdr(ds,T0-1,2+j,h)
ds.row_dimensions[T0-1].height=30
for s in range(SLOTS):
    r=T0+s; key=f'{SEL}&"|"&{s+1}'
    m=f"MATCH({key},{KG},0)"
    ds[f"B{r}"]=f'=IFERROR(INDEX({KB},{m}),"")'
    ds[f"C{r}"]=f'=IFERROR(INDEX({KC},{m}),"")'
    ds[f"D{r}"]=f'=IFERROR(INDEX({KD},{m}),"")'
    ds[f"E{r}"]=f'=IFERROR(INDEX({KE},{m}),"")'
    ds[f"F{r}"]=f'=IFERROR(INDEX({KH},{m}),"")'
    ds[f"G{r}"]=f'=IF(C{r}="","",INT(F{r}/E{r}))'
    ds[f"H{r}"]=f'=IF(C{r}="","",MOD(F{r},E{r})&" / "&E{r})'
    ds[f"I{r}"]=f'=IF(C{r}="","",$I$12*E{r})'
    ds[f"J{r}"]=f'=IF(C{r}="","",MAX(0,I{r}-F{r}))'
    for col in "BCDEFGHIJ":
        x=ds[f"{col}{r}"]; x.font=font(10); x.alignment=L if col in "BCD" else C
    ds[f"C{r}"].font=font(10,True); ds[f"D{r}"].font=font(9,c=GREY); ds[f"G{r}"].font=font(13,True,NAVY); ds[f"J{r}"].font=font(12,True)
    ds.row_dimensions[r].height=19
ds.conditional_formatting.add(f"G{T0}:G{T1}",FormulaRule(formula=[f'AND($C{T0}<>"",$G{T0}=MIN($G${T0}:$G${T1}),MAX($G${T0}:$G${T1})>MIN($G${T0}:$G${T1}))'],fill=fill(CRIT_S),font=Font(name=F,color=CRIT,bold=True,size=13)))
ds.conditional_formatting.add(f"J{T0}:J{T1}",FormulaRule(formula=[f'AND($C{T0}<>"",$J{T0}>0)'],fill=fill(WARN_S),font=Font(name=F,color=WARN,bold=True,size=12)))
ds.conditional_formatting.add(f"J{T0}:J{T1}",FormulaRule(formula=[f'AND($C{T0}<>"",$J{T0}=0)'],font=Font(name=F,color=OK,bold=True,size=12)))
ds.conditional_formatting.add(f"B{T0}:B{T1}",FormulaRule(formula=[f'$B{T0}=$B{T0-1}'],font=Font(name=F,color="C3C8D2")))
ds.conditional_formatting.add(f"B{T0}:J{T1}",FormulaRule(formula=[f'$C{T0}<>""'],border=Border(bottom=thin)))
TR=T1+1
ds[f"C{TR}"]="TOTAL"; ds[f"C{TR}"].font=font(10,True)
for col,fx in (("F","SUM"),("G","MIN"),("I","SUM"),("J","SUM")):
    ds[f"{col}{TR}"]=f'=IF(COUNT({col}{T0}:{col}{T1})=0,"",{fx}({col}{T0}:{col}{T1}))'; ds[f"{col}{TR}"].font=font(11,True,NAVY); ds[f"{col}{TR}"].alignment=C; ds[f"{col}{TR}"].border=Border(top=Side(style="medium",color=NAVY))
ds[f"D{TR}"]="Repeaters = lowest sub-assembly (highlighted red) — it limits the count"; ds[f"D{TR}"].font=font(8,c=GREY,i=True)
# chart area L12..Q
ds["L12"]="PLAN VS KITTED (repeaters, cumulative)"; ds["L12"].font=font(13,True,NAVY)
ch=LineChart(); ch.height=9.5; ch.width=17.5; ch.legend.position="b"; ch.y_axis.title=None; ch.x_axis.title=None
ch.y_axis.majorGridlines=None
data=Reference(ca,min_col=3,min_row=KR+1,max_col=3+WEEKS,max_row=KR+2)
ch.add_data(data,from_rows=True,titles_from_data=True)
ch.set_categories(Reference(ca,min_col=4,min_row=KR,max_col=3+WEEKS,max_row=KR))
cols=["8A91A0",ROSE,"1E2433"]
for sser,colr,w,dash in zip(ch.series,cols,[22000,32000,12000],[None,None,"dash"]):
    sser.graphicalProperties.line.solidFill=colr; sser.graphicalProperties.line.width=w; sser.smooth=False
    if dash: sser.graphicalProperties.line.dashStyle=dash
ch.x_axis.tickLblSkip=4; ch.x_axis.delete=False; ch.y_axis.delete=False
ds.add_chart(ch,"L13")
# latest releases for this contract
LR=TR+3
ds[f"B{LR-1}"]="LATEST RELEASES (this contract)"; ds[f"B{LR-1}"].font=font(12,True,NAVY)
for j,h in enumerate(["Date","Assy Code","Description","Qty","Released By","Note"]): hdr(ds,LR,2+j,h)
ds.merge_cells(start_row=LR,start_column=7,end_row=LR,end_column=10)
lg[f"I5"]="Row#"; lg["I5"].font=font(8,c=GREY)
for i in range(NL):
    r=6+i; lg[f"I{r}"]=f'=IF(B{r}={SEL},ROW(),"")'; lg[f"I{r}"].font=font(8,c="FFFFFF")
lg.column_dimensions["I"].hidden=True
LI=f"'Release Log'!$I$6:$I${5+NL}"
for k in range(8):
    r=LR+1+k; rr=f"IFERROR(LARGE({LI},{k+1}),0)"
    for col,src in (("B","A"),("C","C"),("D","G"),("E","D"),("F","E"),("G","F")):
        ds[f"{col}{r}"]=f"=IF({rr}=0,\"\",IF(INDEX('Release Log'!${src}:${src},{rr})=\"\",\"\",INDEX('Release Log'!${src}:${src},{rr})))"
        ds[f"{col}{r}"].border=BOT; ds[f"{col}{r}"].font=font(10); ds[f"{col}{r}"].alignment=L if col in "CDG" else C
    ds.merge_cells(f"G{r}:J{r}")
    ds[f"B{r}"].number_format="dd-mmm-yy"; ds[f"D{r}"].font=font(9,c=GREY); ds[f"E{r}"].font=font(11,True)
ds.freeze_panes="A5"
ds.page_setup.orientation="landscape"; ds.page_setup.fitToWidth=1; ds.page_setup.fitToHeight=1; ds.sheet_properties.pageSetUpPr.fitToPage=True
ds.print_area=f"A1:Q{LR+8}"

# ================= Portfolio =================
pf=wb.create_sheet("Portfolio",1); pf.sheet_view.showGridLines=False; pf.sheet_view.zoomScale=85
for c in range(2,13):
    for r in (1,2,3): pf.cell(r,c).fill=fill(NAVY)
pf.row_dimensions[2].height=36
pf["B2"]="R5B AMP KITTING — ALL CONTRACTS"; pf["B2"].font=font(22,True,WHITE)
pf["B3"]='="As of "&TEXT(Dashboard!$Q$3,"dd-mmm-yy")&"  ·  week "&_xlfn.ISOWEEKNUM(Dashboard!$Q$3)&"  ·  "&COUNTA(Contracts!$A$'+str(C0)+':$A$'+str(C1)+')&" contracts"'; pf["B3"].font=font(10,c=MUTE)
ph=["Contract","Project","Top Code","FP","Total Reps","Kitted","Progress","Amps Kitted","Plan to Date","Vs Plan","Status"]
for j,h in enumerate(ph): hdr(pf,5,2+j,h)
pf.row_dimensions[5].height=28
for i in range(NC):
    r=6+i; src=C0+i
    m={"B":"A","C":"B","D":"C","E":"D","F":"F","G":"I","H":"N","I":"J","J":"K","K":"L","L":"O"}
    for col,s in m.items():
        pf[f"{col}{r}"]=f'=IF(Contracts!$A${src}="","",IF(Contracts!{s}{src}="","–",Contracts!{s}{src}))'
        x=pf[f"{col}{r}"]; x.font=font(10,col=="B"); x.alignment=L if col in "BCD" else C
    pf[f"H{r}"].number_format="0%"; pf[f"I{r}"].number_format="#,##0"; pf[f"G{r}"].font=font(12,True,NAVY)
    pf.row_dimensions[r].height=20
pf.conditional_formatting.add(f"H6:H{5+NC}",DataBarRule(start_type="num",start_value=0,end_type="num",end_value=1,color=ROSE,showValue=True))
for v,fc,bc in (("COMPLETE",OK,OK_S),("AHEAD",OK,OK_S),("ON PLAN",INFO,INFO_S),("BEHIND",CRIT,CRIT_S),("NO KIT",GREY,"ECEEF3")):
    pf.conditional_formatting.add(f"L6:L{5+NC}",FormulaRule(formula=[f'LEFT($L6,{len(v)})="{v}"'],fill=fill(bc),font=Font(name=F,color=fc,bold=True)))
for c,w in zip("ABCDEFGHIJKL",[2,20,24,16,6,10,10,16,11,11,10,16]): pf.column_dimensions[c].width=w
pf.freeze_panes="A6"
pf.conditional_formatting.add(f"B6:L{5+NC}",FormulaRule(formula=['$B6<>""'],border=Border(bottom=thin)))
pf.page_setup.orientation="landscape"; pf.page_setup.fitToWidth=1; pf.page_setup.fitToHeight=0; pf.sheet_properties.pageSetUpPr.fitToPage=True
pf.column_dimensions["C"].width=30


# ================= Gantt =================
GW=S.get("gantt_weeks",52); GB=S.get("gantt_blocks",15); G0C=5  # first week column = E
gt=wb.create_sheet("Gantt",2); gt.sheet_view.showGridLines=False; gt.sheet_view.zoomScale=80
gc=wb.create_sheet("GanttCalc")
gt.column_dimensions["A"].width=2; gt.column_dimensions["B"].width=20; gt.column_dimensions["C"].width=17; gt.column_dimensions["D"].width=9
for c in range(G0C,G0C+GW): gt.column_dimensions[CL(c)].width=7.2
LASTG=CL(G0C+GW-1)
for c in range(2,G0C+GW):
    for r in (1,2): gt.cell(r,c).fill=fill(NAVY)
gt.row_dimensions[1].height=34
gt["B1"]="R5B AMP KITTING — RELEASE GANTT"; gt["B1"].font=font(20,True,WHITE); gt["B1"].alignment=Alignment(vertical="center")
gt["B2"]='="Repeater numbers per ISO week · housing (final build) = plan week W · AMPS build = W−1 · kit release = W−" & "lead (Contracts, default 2) · as of "&TEXT(Dashboard!$Q$3,"dd-mmm-yy")&" (W"&_xlfn.ISOWEEKNUM(Dashboard!$Q$3)&")"'
gt["B2"].font=font(10,c=MUTE)
gt["B4"]="START WEEK (Mon) ▸"; gt["B4"].font=font(9,True,GREY); gt["B4"].alignment=Alignment(horizontal="right",vertical="center")
gt["C4"]="=Dashboard!$Q$3-7*6"; gt["C4"].number_format="dd-mmm-yy"; gt["C4"].font=font(11,True,WHITE); gt["C4"].fill=fill(ROSE); gt["C4"].alignment=C
gt["C4"].comment=Comment("Defaults to 6 weeks before today. Type any Monday (e.g. 01/06/2026) to scroll the Gantt.","Gantt")
# legend
leg=[("E4","Kit planned",ROSE,"F9DCE7"),("G4","Kitted",OK,OK_S),("I4","Kit overdue",WHITE,CRIT),("K4","AMPS build",WARN,WARN_S),("M4","Housing / final",INFO,INFO_S),("O4","This week",NAVY,"FFF2B3")]
for cell,t,fc,bc in leg:
    x=gt[cell]; x.value=t; x.font=font(8,True,fc); x.fill=fill(bc); x.alignment=C
    nc=gt.cell(x.row,x.column+1); nc.fill=fill(bc)
    gt.merge_cells(start_row=x.row,start_column=x.column,end_row=x.row,end_column=x.column+1)
# header rows 6 year, 7 week, 8 date
HY,HW,HD=6,7,8
hdr(gt,HW,2,"Contract"); hdr(gt,HW,3,"Stage"); hdr(gt,HW,4,"Reps")
for r in (HY,HD):
    for c in (2,3,4): gt.cell(r,c).fill=fill(INK)
for k in range(GW):
    c=G0C+k; col=CL(c)
    gt[f"{col}{HD}"]=f"=$C$4-WEEKDAY($C$4,2)+1+{7*k}"; gt[f"{col}{HD}"].number_format="dd-mmm"
    gt[f"{col}{HW}"]=f'="W"&TEXT(_xlfn.ISOWEEKNUM({col}{HD}),"00")'
    gt[f"{col}{HY}"]=f'=IF(OR({k}=0,_xlfn.ISOWEEKNUM({col}{HD})=1),YEAR({col}{HD}+3),"")'
    for r,fz,fc in ((HY,9,MUTE),(HW,10,WHITE),(HD,8,MUTE)):
        x=gt[f"{col}{r}"]; x.font=font(fz,r==HW,fc); x.fill=fill(INK); x.alignment=C
gt.row_dimensions[HW].height=20
# GanttCalc: row 2 dates (helper col j=0..GW+2 -> col B+j), rows 4.. per block cumulative
gc["A1"]="Helper for Gantt — do not edit"; gc["A2"]="Week start"
for j in range(GW+3):
    gc.cell(2,2+j,f"=Gantt!$C$4-WEEKDAY(Gantt!$C$4,2)+1+{7*(j-1)}").number_format="dd-mmm"
B0=10
for b in range(GB):
    cr=C0+b; gr=4+b
    gc[f"A{gr}"]=f"=Contracts!$A${cr}"
    for j in range(GW+3):
        col=CL(2+j)
        gc[f"{col}{gr}"]=f'=IF($A{gr}="","",SUMIFS({WD},{WA},$A{gr},{WE},"<="&{col}$2))'
    r0=B0+b*4
    rows=[("Kit release","W−lead",2),("AMPS build","W−1",1),("Final build","Housing",0)]
    gt[f"B{r0}"]=f'=IF(Contracts!$A${cr}="","",Contracts!$A${cr})'; gt[f"B{r0}"].font=font(10,True)
    gt[f"B{r0+1}"]=f'=IF(Contracts!$A${cr}="","",Contracts!$C${cr})'; gt[f"B{r0+1}"].font=font(8,c=GREY)
    gt[f"B{r0+2}"]=f'=IF(Contracts!$A${cr}="","",IF(Contracts!$I${cr}="","no kit list","kitted: "&Contracts!$I${cr}&" / "&Contracts!$F${cr}))'; gt[f"B{r0+2}"].font=font(8,True,ROSE)
    for i,(lab,sub,off) in enumerate(rows):
        r=r0+i
        gt[f"C{r}"]=f'=IF(Contracts!$A${cr}="","","{lab}")'; gt[f"C{r}"].font=font(9,True,[ROSE,WARN,INFO][i])
        # total reps in visible window for that stage
        for k in range(GW):
            c=G0C+k; col=CL(c)
            if i==0: hi=f"OFFSET(GanttCalc!$B${gr},0,{k+1}+N(Contracts!$Q${cr}))"; lo=f"OFFSET(GanttCalc!$B${gr},0,{k}+N(Contracts!$Q${cr}))"
            else:
                hi=f"GanttCalc!{CL(2+k+1+off)}{gr}"; lo=f"GanttCalc!{CL(2+k+off)}{gr}"
            gt[f"{col}{r}"]=f'=IF($B${r0}="","",IF(N({hi})-N({lo})<=0,"",IF(N({hi})-N({lo})=1,"R"&{hi},"R"&({lo}+1)&"-"&{hi})))'
            x=gt[f"{col}{r}"]; x.font=font(8,True,INK); x.alignment=C
        gt[f"D{r}"]=f'=IF($B${r0}="","",SUMPRODUCT(--(E{r}:{LASTG}{r}<>""))&" wks")'; gt[f"D{r}"].font=font(8,c=GREY); gt[f"D{r}"].alignment=C
    # CF for this block
    kr=r0; ar=r0+1; hr=r0+2; rng=lambda rr:f"E{rr}:{LASTG}{rr}"
    lastrep=f"OFFSET(GanttCalc!$B${gr},0,COLUMN(E{kr})-COLUMN($E${kr})+1+N(Contracts!$Q${cr}))"
    gt.conditional_formatting.add(rng(kr),FormulaRule(formula=[f'AND(E{kr}<>"",N(Contracts!$I${cr})>={lastrep})'],fill=fill(OK_S),font=Font(name=F,size=8,bold=True,color=OK)))
    gt.conditional_formatting.add(rng(kr),FormulaRule(formula=[f'AND(E{kr}<>"",E${HD}<=Dashboard!$Q$3)'],fill=fill(CRIT),font=Font(name=F,size=8,bold=True,color=WHITE)))
    gt.conditional_formatting.add(rng(kr),FormulaRule(formula=[f'E{kr}<>""'],fill=fill("F9DCE7"),font=Font(name=F,size=8,bold=True,color=ROSE)))
    gt.conditional_formatting.add(rng(ar),FormulaRule(formula=[f'E{ar}<>""'],fill=fill(WARN_S),font=Font(name=F,size=8,bold=True,color=WARN)))
    gt.conditional_formatting.add(rng(hr),FormulaRule(formula=[f'E{hr}<>""'],fill=fill(INFO_S),font=Font(name=F,size=8,bold=True,color=INFO)))
    for rr in (kr,ar,hr): gt.row_dimensions[rr].height=17
    gt.row_dimensions[r0+3].height=6
    for c in range(2,G0C+GW): gt.cell(r0+3,c).border=Border(top=Side(style="thin",color=LINE))
# this-week column highlight
GEND=B0+GB*4
gt.conditional_formatting.add(f"E{HW}:{LASTG}{HD}",FormulaRule(formula=[f'E${HD}=Dashboard!$Q$3'],fill=fill("FFF2B3"),font=Font(name=F,bold=True,color=NAVY)))
gt.conditional_formatting.add(f"E{B0}:{LASTG}{GEND}",FormulaRule(formula=[f'AND(E${HD}=Dashboard!$Q$3,E{B0}="")'],fill=fill("FFFBE6")))
gt.freeze_panes=gt[f"E{B0}"]
gt.page_setup.orientation="landscape"; gt.page_setup.fitToWidth=1; gt.page_setup.fitToHeight=0; gt.sheet_properties.pageSetUpPr.fitToPage=True
gc.sheet_state="hidden"

# ================= How To Use =================
hu=wb.create_sheet("How To Use"); hu.sheet_view.showGridLines=False
hu.column_dimensions["B"].width=34; hu.column_dimensions["C"].width=110
hu["B2"]="R5B AMP KITTING CONTROL — HOW IT WORKS"; hu["B2"].font=font(18,True,NAVY)
rows=[("1. Update what has been kitted (every release)","",True),
 ("Where","Sheet 'Release Log'. This is the ONLY sheet you touch day to day.",False),
 ("What to type","One line per assy code you release: Date · Contract (drop-down) · Assy Code (drop-down) · Qty Released · Released By · Note (e.g. 'Rep 14' or the WO number). Description and Check fill in by themselves.",False),
 ("Example — 1 repeater of E2A-R12P-T5-C","14 lines, same date: 92YLS00548BAA 1 · 92YLS00548BBA 2 · 91YAF03404AAA 3 · 92YFD04548BAA 1 · 92YFD04548BBA 2 · 92YWS04548AAA 3 · 92RRA00548AAA 24 · 92YRA01548AAA 3 · 92YRA02548AAA 3 · 92YRA03548AAA 3 · 92YRA04548AAA 3 · 92UAP04548BAA 1 · 92UAP04548BBA 1 · 92UAP04548BCA 1. Tip: copy the 'To Release' column from the Dashboard.",False),
 ("Part release","Log only what actually went out (e.g. spool 16 of 24). The repeater counts once every code reaches a full set; the Dashboard 'Toward Next' column shows the part.",False),
 ("Mistake","Never delete. Add a correcting line with a negative qty (e.g. -3) and a note.",False),
 ("Check column","Red = something's wrong on that line (missing qty, code not on this contract's kit list, etc.).",False),
 ("2. Where the assembly codes go (once per contract)","",True),
 ("Where","Sheet 'Kit Lists'. One row per assy code: Contract · Sequence (LASER ASSY, PSB ASSY, OPF ASSY, POB ASSY, ERBIUM ASSY, BOAT ASSY…) · Assy Code · Description · Qty per Repeater.",False),
 ("Where it comes from","ZMRP breakdown of the contract's top code (++). Qty per Repeater = how many of that code go into ONE repeater (e.g. spool 24).",False),
 ("Order","Rows show on the Dashboard in the order you type them, grouped by sequence. Keep each contract's rows together.",False),
 ("New contract","First add the contract on 'Contracts' (friendly name, project, top code ++, FP, amps per repeater, total repeaters), then its rows on 'Kit Lists', then its weeks on 'Weekly Plan'.",False),
 ("3. Kitted ahead of time","",True),
 ("Just log it","Log the release with the real date you released it. The Dashboard compares kitted with the plan up to the 'As of' week: kitting early shows as AHEAD +n (green). Nothing else to change.",False),
 ("Plan moved","If the plan itself changes (CO41 dates move), edit the week/qty on 'Weekly Plan'. Kitting history stays untouched.",False),
 ("Planning the next batch","On the Dashboard, type the number of repeaters you want to reach in the pink 'Release Target' cell (e.g. management asks for 2 more: kitted + 2). 'To Release' shows exactly what to release per code.",False),
 ("4. Reading the Dashboard","",True),
 ("Repeaters kitted","Per code: released ÷ qty per repeater (rounded down). Contract figure = the LOWEST code, because a repeater needs every code. The limiting code is highlighted red.",False),
 ("Amps kitted","Repeaters kitted × amps per repeater (= FP).",False),
 ("Plan to date / Vs plan","'Weekly Plan' weeks are FINAL BUILD (housing) weeks. Kits are due 'Kit Lead' weeks earlier (Contracts, default 2: kit W−2, AMPS build W−1, housing W). Plan to date = repeaters whose housing week is up to 'As of' + lead. Vs plan = kitted − plan to date.",False),
 ("Gantt","Sheet 'Gantt': ISO weeks across, three rows per contract — Kit release (W−2), AMPS build (W−1), Final build / housing (W) — with the repeater numbers in each week. Kit cells turn green once kitted, red if overdue. Change the start week in the pink cell.",False),
 ("Contract total changes","Change 'Total Repeaters' on 'Contracts' (e.g. 109 → 117). Everything recalculates.",False),
 ("Why it stays fast","No SAP dumps. Only your plan numbers and release lines — a few hundred rows per contract.",False)]
r=4
for k,v,h in rows:
    if h: r+=1; hu[f"B{r}"]=k; hu[f"B{r}"].font=font(12,True,ROSE); r+=1; continue
    hu[f"B{r}"]=k; hu[f"B{r}"].font=font(11,True); hu[f"B{r}"].alignment=Alignment(vertical="top")
    hu[f"C{r}"]=v; hu[f"C{r}"].font=font(11); hu[f"C{r}"].alignment=Alignment(wrap_text=True,vertical="top"); hu.row_dimensions[r].height=34; r+=1

wb.move_sheet("Calc",offset=10); wb.move_sheet("GanttCalc",offset=10)
wb.calculation=CalcProperties(fullCalcOnLoad=True)
wb.active=0
wb.save(OUT)

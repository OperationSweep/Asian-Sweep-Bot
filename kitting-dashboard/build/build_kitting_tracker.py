"""Kitting tracker: paste raw COOIS export -> repeaters kitted / issued / delivered."""
import sys, json, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule, CellIsRule, DataBarRule
from openpyxl.utils import get_column_letter as CL
from openpyxl.workbook.properties import CalcProperties

OUT=sys.argv[1]; CFG=json.load(open(sys.argv[2])); RAW=json.load(open(sys.argv[3])) if len(sys.argv)>3 else None
PLAN=CFG["plan"]; NP=len(PLAN); NREP=CFG["repeaters"]; D=CFG["details"]
NAVY="141A26"; INK="1E2433"; ROSE="B0245E"; GREY="5D6576"; LINE="D9DDE5"; PANEL="F3F4F7"; WHITE="FFFFFF"; MUTE="AEB6C6"
OK="1F8A5B"; OK_S="DDF2E7"; WARN="A8660B"; WARN_S="FBF0DC"; CRIT="C0392B"; CRIT_S="FBE6E3"; INFO="3558B8"; INFO_S="E3EAFA"; BLUE="0000FF"
F="Arial"
def font(sz=11,b=False,c=INK,i=False): return Font(name=F,size=sz,bold=b,color=c,italic=i)
def fill(c): return PatternFill("solid",start_color=c,end_color=c)
thin=Side(style="thin",color=LINE); BOX=Border(top=thin,bottom=thin,left=thin,right=thin); BOT=Border(bottom=thin)
C=Alignment(horizontal="center",vertical="center",wrap_text=True); L=Alignment(horizontal="left",vertical="center",wrap_text=True)
def hdr(ws,r,c,t,bg=INK):
    x=ws.cell(r,c,t); x.font=font(10,True,WHITE); x.fill=fill(bg); x.alignment=C; x.border=BOX

wb=Workbook()
# ---------- Kitting Plan ----------
kp=wb.active; kp.title="Kitting Plan"; kp.sheet_view.showGridLines=False
kp["A1"]="KITTING PLAN — QTY TO BUILD ONE REPEATER"; kp["A1"].font=font(16,True,NAVY)
kp["A2"]="Source: kitting plan supplied by the user. Blue cells are inputs."; kp["A2"].font=font(10,c=GREY,i=True)
kp["A3"]="Contract repeaters"; kp["A3"].font=font(11,True); kp["C3"]=NREP; kp["C3"].font=font(12,True,BLUE); kp["C3"].fill=fill("FFFF00"); kp["C3"].alignment=C
for j,h in enumerate(["Sequence","Assy Code","Assy Description","Qty per Repeater","Contract Qty"],1): hdr(kp,5,j,h,NAVY)
for i,(s,code,d,per) in enumerate(PLAN):
    r=6+i
    for j,v in enumerate([s,code,d,per],1):
        x=kp.cell(r,j,v); x.font=font(10,c=BLUE); x.border=BOX; x.alignment=L if j<4 else C
    x=kp.cell(r,5,f"=D{r}*$C$3"); x.font=font(10); x.border=BOX; x.alignment=C
PL0,PL1=6,5+NP
for c,w in zip("ABCDE",[15,18,46,16,14]): kp.column_dimensions[c].width=w
KP_CODE=f"'Kitting Plan'!$B${PL0}:$B${PL1}"; KP_PER=f"'Kitting Plan'!$D${PL0}:$D${PL1}"; REPS="'Kitting Plan'!$C$3"

# ---------- COOIS Raw ----------
raw=wb.create_sheet("COOIS Raw")
if RAW:
    cols=RAW["columns"]
    for j,h in enumerate(cols,1): raw.cell(1,j,h)
    for i,row in enumerate(RAW["rows"],2):
        for j,v in enumerate(row,1):
            if v is None or v=="": continue
            if isinstance(v,str) and v.startswith("D:"): v=datetime.date.fromisoformat(v[2:])
            raw.cell(i,j,v)
    for j,h in enumerate(cols,1):
        if "date" in h.lower():
            for i in range(2,len(RAW["rows"])+2): raw.cell(i,j).number_format="dd/mm/yyyy"
raw.freeze_panes="A2"

# ---------- COOIS Data (derived) ----------
cd=wb.create_sheet("COOIS Data"); cd.sheet_view.showGridLines=False
N0,N1=6,6+CFG.get("rows",2000)-1
cd["A1"]="COOIS DATA — READ AUTOMATICALLY FROM 'COOIS Raw'"; cd["A1"].font=font(16,True,NAVY)
cd["A2"]="Do not type here. Paste the COOIS export into 'COOIS Raw' (cell A1, with headers). Everything below recalculates."; cd["A2"].font=font(10,c=GREY,i=True)
# header column positions
lookups=[("Order","Order"),("Material","Material Number"),("Desc","Material desc*"),("Qty","Order quantity*"),("Status","System Status"),("RelDate","Release date*")]
cd["A3"]="Column found in COOIS Raw:"; cd["A3"].font=font(9,c=GREY)
for j,(k,pat) in enumerate(lookups):
    c=cd.cell(4,j+1,f'=IFERROR(MATCH("{pat}",\'COOIS Raw\'!$1:$1,0),0)'); c.font=font(8,c=GREY); c.alignment=C
heads=["WO (Order)","Assy Code","Description","Qty","SAP System Status","Release Date","In Plan","Qty / Rep","Kitted (PRT)","Issued (GMPS)","Delivered (DLV)","Stage","Seq # in Code","Repeater #","Contract"]
for j,h in enumerate(heads,1): hdr(cd,5,j,h,NAVY)
def rawv(colref,r): return f"INDEX('COOIS Raw'!$A:$GZ,ROW()-4,{colref})"
for r in range(N0,N1+1):
    cd[f"A{r}"]=f'=IF(OR($A$4=0,{rawv("$A$4",r)}=""),"",IFERROR(--{rawv("$A$4",r)},{rawv("$A$4",r)}))'
    cd[f"B{r}"]=f'=IF(A{r}="","",TRIM({rawv("$B$4",r)}))'
    cd[f"C{r}"]=f'=IF(OR(A{r}="",$C$4=0),"",{rawv("$C$4",r)})'
    cd[f"D{r}"]=f'=IF(A{r}="","",IF($D$4=0,1,IFERROR(--{rawv("$D$4",r)},1)))'
    cd[f"E{r}"]=f'=IF(A{r}="","",{rawv("$E$4",r)}&"")'
    cd[f"F{r}"]=f'=IF(A{r}="","",IFERROR(DATEVALUE({rawv("$F$4",r)}),{rawv("$F$4",r)}))'
    cd[f"G{r}"]=f'=IF(A{r}="","",IF(ISNA(MATCH(B{r},{KP_CODE},0)),"Not in plan","Yes"))'
    cd[f"H{r}"]=f'=IF(G{r}="Yes",INDEX({KP_PER},MATCH(B{r},{KP_CODE},0)),"")'
    cd[f"I{r}"]=f'=IF(A{r}="","",IF(ISNUMBER(SEARCH("PRT",E{r})),D{r},0))'
    cd[f"J{r}"]=f'=IF(A{r}="","",IF(ISNUMBER(SEARCH("GMPS",E{r})),D{r},0))'
    cd[f"K{r}"]=f'=IF(A{r}="","",IF(ISNUMBER(SEARCH("DLV",E{r})),D{r},0))'
    cd[f"L{r}"]=f'=IF(A{r}="","",IF(K{r}>0,"Delivered",IF(ISNUMBER(SEARCH("CNF",E{r})),"In production",IF(J{r}>0,"Issued",IF(I{r}>0,"Kitted","Released")))))'
    cd[f"M{r}"]=(f'=IF(G{r}<>"Yes","",COUNTIFS($B${N0}:$B${N1},B{r},$F${N0}:$F${N1},"<"&F{r})'
                 f'+COUNTIFS($B${N0}:$B${N1},B{r},$F${N0}:$F${N1},F{r},$A${N0}:$A${N1},"<="&A{r}))')
    cd[f"N{r}"]=f'=IF(M{r}="","",ROUNDUP(M{r}/H{r},0))'
    cd[f"O{r}"]=f'=IF(N{r}="","",IF(N{r}<={REPS},"Rep "&N{r},"Surplus"))'
    for j in range(1,16):
        x=cd.cell(r,j); x.font=font(9,c=GREY if j in (3,5) else INK); x.border=BOT
        x.alignment=Alignment(horizontal="center" if j not in (3,5) else "left",vertical="center")
    cd[f"A{r}"].number_format="0"; cd[f"F{r}"].number_format="dd-mmm-yy"
for c,w in zip("ABCDEFGHIJKLMNO",[13,16,34,6,34,11,10,8,9,9,10,13,9,10,10]): cd.column_dimensions[c].width=w
cd.freeze_panes="C6"; cd.auto_filter.ref=f"A5:O{N1}"
cd.conditional_formatting.add(f"O{N0}:O{N1}",FormulaRule(formula=[f'$O{N0}="Surplus"'],fill=fill(WARN_S),font=Font(name=F,color=WARN,bold=True)))
cd.conditional_formatting.add(f"G{N0}:G{N1}",FormulaRule(formula=[f'$G{N0}="Not in plan"'],fill=fill(CRIT_S),font=Font(name=F,color=CRIT,bold=True)))
for st,fc,bc in (("Delivered",OK,OK_S),("In production",WARN,WARN_S),("Issued",INFO,INFO_S),("Kitted",INFO,INFO_S)):
    cd.conditional_formatting.add(f"L{N0}:L{N1}",FormulaRule(formula=[f'$L{N0}="{st}"'],fill=fill(bc),font=Font(name=F,color=fc,bold=True)))
R=lambda c:f"'COOIS Data'!${c}${N0}:${c}${N1}"

# ---------- Dashboard ----------
ds=wb.create_sheet("Dashboard",0); ds.sheet_view.showGridLines=False; ds.sheet_view.zoomScale=75
FIRST=5  # column E = rep 1
LASTC=FIRST+NREP-1
widths={"A":2,"B":13,"C":17,"D":40}
for k,v in widths.items(): ds.column_dimensions[k].width=v
for c in range(FIRST,LASTC+1): ds.column_dimensions[CL(c)].width=7.5
EDGE=CL(LASTC)
for c in range(2,LASTC+1):
    for r in (1,2,3): ds.cell(r,c).fill=fill(NAVY)
ds.row_dimensions[2].height=40
ds["B2"]=CFG["title"]; ds["B2"].font=font(24,True,WHITE); ds["B2"].alignment=Alignment(vertical="center")
ds["B3"]=f'="Contract {D["contract"]}  ·  {D["program"]}  ·  {D["erp"]}  ·  {D["config"]}  ·  Repeaters 1–"&{REPS}&"  ·  "&COUNT({R("A")})&" WOs in COOIS  ·  latest release "&TEXT(MAX({R("F")}),"dd-mmm-yy")'
ds["B3"].font=font(11,c=MUTE)
# KPI tiles row 5-7
GR=lambda col: f"{col}{G0}:{col}{G1}"
L0=11; L1=L0+NP-1   # ledger rows
G0=L1+5; G1=G0+NP-1 # grid rows
tiles=[("B","C","REPEATERS KITTED",f'=MIN(H{L0}:H{L1})&" / "&{REPS}',f'="Every code has ≥ "&MIN(H{L0}:H{L1})&" full repeater kits (WO printed in SAP)"'),
       ("D","D","WORK ORDERS KITTED",f'=SUM(G{L0}:G{L1})',f'=SUM(F{L0}:F{L1})&" needed for "&{REPS}&" reps · "&SUM(I{L0}:I{L1})&" surplus to review"'),
       (CL(FIRST),CL(FIRST+3),"ISSUED (GMPS)",f'=MIN(K{L0}:K{L1})&" reps"','="components issued for all codes"'),
       (CL(FIRST+4),CL(FIRST+7),"DELIVERED (DLV)",f'=MIN(M{L0}:M{L1})&" reps"','="all 14 codes goods-receipted"'),
       (CL(FIRST+8),EDGE,"OPEN WOs",f'=SUM(N{L0}:N{L1})','="kitted, not yet delivered"')]
ds.row_dimensions[5].height=20; ds.row_dimensions[6].height=52; ds.row_dimensions[7].height=30
for a,b,lab,val,sub in tiles:
    for r in (5,6,7):
        if a!=b: ds.merge_cells(f"{a}{r}:{b}{r}")
        ca=ds[f"{a}{r}"].column; cb=ds[f"{b}{r}"].column
        for c in range(ca,cb+1):
            ds.cell(r,c).fill=fill(PANEL); ds.cell(r,c).border=Border(left=Side(style="thick",color=ROSE) if c==ca else None)
    ds[f"{a}5"]=lab; ds[f"{a}5"].font=font(10,True,GREY); ds[f"{a}5"].alignment=Alignment(horizontal="left",vertical="bottom",indent=1)
    ds[f"{a}6"]=val; ds[f"{a}6"].font=font(30,True,NAVY); ds[f"{a}6"].alignment=Alignment(horizontal="left",vertical="center",indent=1)
    ds[f"{a}7"]=sub; ds[f"{a}7"].font=font(9,c=GREY); ds[f"{a}7"].alignment=Alignment(horizontal="left",vertical="top",indent=1,wrap_text=True)
ds["B6"].font=font(40,True,ROSE)

# Ledger
ds[f"B{L0-2}"]="KITTED BY ASSY CODE"; ds[f"B{L0-2}"].font=font(14,True,NAVY)
ds[f"D{L0-2}"]="Kitted = WO released and printed (PRT) in COOIS. Kits = kitted WOs ÷ qty per repeater."; ds[f"D{L0-2}"].font=font(9,c=GREY,i=True)
lh=["Sequence","Assy Code","Description","Qty / Rep","Contract Qty","WOs Kitted","Repeater Kits","Kitted vs Contract","Surplus WOs","Issued (GMPS)","Issued Reps","Delivered","Delivered Reps","Open WOs"]
lc=["B","C","D"]+[CL(FIRST+i) for i in range(11)]
for col,h in zip(lc,lh): hdr(ds,L0-1,ds[f"{col}1"].column,h)
ds.row_dimensions[L0-1].height=34
# ledger columns E..O mapped: E per, F contract, G kitted, H kits, I surplus? need fixed letters
# fixed letters: E=per F=contract G=kitted H=kits I=vs contract(J?) -> define explicitly
for i,(s,code,dsc,per) in enumerate(PLAN):
    r=L0+i; k=PL0+i
    ds[f"B{r}"]=f"='Kitting Plan'!A{k}"; ds[f"C{r}"]=f"='Kitting Plan'!B{k}"; ds[f"D{r}"]=f"='Kitting Plan'!C{k}"
    ds[f"E{r}"]=f"='Kitting Plan'!D{k}"; ds[f"F{r}"]=f"='Kitting Plan'!E{k}"
    ds[f"G{r}"]=f'=SUMIFS({R("I")},{R("B")},C{r})'
    ds[f"H{r}"]=f'=IF(E{r}=0,0,INT(G{r}/E{r}))'
    ds[f"I{r}"]=f'=MAX(0,G{r}-F{r})'
    ds[f"J{r}"]=f'=SUMIFS({R("J")},{R("B")},C{r})'
    ds[f"K{r}"]=f'=IF(E{r}=0,0,INT(J{r}/E{r}))'
    ds[f"L{r}"]=f'=SUMIFS({R("K")},{R("B")},C{r})'
    ds[f"M{r}"]=f'=IF(E{r}=0,0,INT(L{r}/E{r}))'
    ds[f"N{r}"]=f'=G{r}-L{r}'
    for col in "BCDEFGHIJKLMN":
        x=ds[f"{col}{r}"]; x.border=BOT; x.font=font(11); x.alignment=L if col in "BCD" else C
    ds[f"C{r}"].font=font(11,True); ds[f"D{r}"].font=font(9,c=GREY); ds[f"H{r}"].font=font(14,True,NAVY)
    ds.row_dimensions[r].height=22
# fix ledger headers to real columns
for col,h in zip("BCDEFGHIJKLMN",["Sequence","Assy Code","Description","Qty / Rep","Contract Qty","WOs Kitted","Rep Kits","Surplus WOs","Issued","Issued Reps","Delivered","Delivered Reps","Open WOs"]):
    hdr(ds,L0-1,ds[f"{col}1"].column,h)
for c in range(ds["O1"].column,LASTC+1): ds.cell(L0-1,c).fill=fill(WHITE); ds.cell(L0-1,c).border=Border()
ds.conditional_formatting.add(f"H{L0}:H{L1}",FormulaRule(formula=[f"$H{L0}>={REPS}"],fill=fill(OK_S),font=Font(name=F,color=OK,bold=True,size=14)))
ds.conditional_formatting.add(f"H{L0}:H{L1}",FormulaRule(formula=[f"$H{L0}<{REPS}"],fill=fill(CRIT_S),font=Font(name=F,color=CRIT,bold=True,size=14)))
ds.conditional_formatting.add(f"I{L0}:I{L1}",CellIsRule(operator="greaterThan",formula=["0"],fill=fill(WARN_S),font=Font(name=F,color=WARN,bold=True)))
ds.conditional_formatting.add(f"B{L0}:B{L1}",FormulaRule(formula=[f"$B{L0}=$B{L0-1}"],font=Font(name=F,color="C3C8D2")))
TR=L1+1
ds[f"C{TR}"]="TOTAL / MIN"; ds[f"C{TR}"].font=font(11,True)
for col,fx in (("F","SUM"),("G","SUM"),("H","MIN"),("I","SUM"),("J","SUM"),("K","MIN"),("L","SUM"),("M","MIN"),("N","SUM")):
    ds[f"{col}{TR}"]=f"={fx}({col}{L0}:{col}{L1})"; ds[f"{col}{TR}"].font=font(12,True,NAVY); ds[f"{col}{TR}"].alignment=C
    ds[f"{col}{TR}"].border=Border(top=Side(style="medium",color=NAVY))
ds[f"D{TR}"]="Rep kits / reps columns show the MIN — the limiting code"; ds[f"D{TR}"].font=font(9,c=GREY,i=True)

# Repeater grid
ds[f"B{G0-2}"]="REPEATER KIT TRACKER"; ds[f"B{G0-2}"].font=font(14,True,NAVY)
ds[f"D{G0-2}"]="WOs are assigned to repeaters in release order (oldest first). K = kitted · I = components issued · D = delivered · – = not kitted"; ds[f"D{G0-2}"].font=font(9,c=GREY,i=True)
hdr(ds,G0-1,2,"Sequence"); hdr(ds,G0-1,3,"Assy Code"); hdr(ds,G0-1,4,"Description")
for n in range(1,NREP+1): hdr(ds,G0-1,FIRST+n-1,f"Rep {n}",NAVY)
ds.row_dimensions[G0-1].height=26
for i in range(NP):
    r=G0+i; lr=L0+i
    ds[f"B{r}"]=f"=B{lr}"; ds[f"C{r}"]=f"=C{lr}"; ds[f"D{r}"]=f"=D{lr}"
    for n in range(1,NREP+1):
        c=FIRST+n-1; ref=f"{CL(c)}{r}"
        base=f'{R("B")},$C{r},{R("N")},{n}'
        ds[ref]=(f'=IF(COUNTIFS({base},{R("I")},">0")<$E{lr},"–",'
                 f'IF(COUNTIFS({base},{R("K")},">0")>=$E{lr},"D",IF(COUNTIFS({base},{R("J")},">0")>=$E{lr},"I","K")))')
        x=ds[ref]; x.alignment=C; x.font=font(11,True); x.border=Border(top=Side(style="thin",color=WHITE),bottom=Side(style="thin",color=WHITE),left=Side(style="thin",color=WHITE),right=Side(style="thin",color=WHITE))
    for col in "BCD": ds[f"{col}{r}"].font=font(10 if col!="D" else 9, col=="C", INK if col!="D" else GREY); ds[f"{col}{r}"].border=BOT
    ds.row_dimensions[r].height=20
GA=f"{CL(FIRST)}{G0}:{EDGE}{G1}"
for v,fc,bc in (("D",OK,OK_S),("I",WARN,WARN_S),("K",INFO,INFO_S),("–",GREY,"ECEEF3")):
    ds.conditional_formatting.add(GA,FormulaRule(formula=[f'{CL(FIRST)}{G0}="{v}"'],fill=fill(bc),font=Font(name=F,color=fc,bold=True)))
SR=G1+1
ds[f"C{SR}"]="REPEATER STATUS"; ds[f"C{SR}"].font=font(10,True)
ds[f"D{SR}"]="Kitted = all codes kitted · Delivered = all codes delivered"; ds[f"D{SR}"].font=font(9,c=GREY,i=True)
for n in range(1,NREP+1):
    col=CL(FIRST+n-1); rng=f"{col}{G0}:{col}{G1}"
    ds[f"{col}{SR}"]=f'=IF(COUNTIF({rng},"–")>0,"OPEN",IF(COUNTIF({rng},"D")={NP},"DLV",IF(COUNTIF({rng},"K")=0,"ISSUED","KITTED")))'
    ds[f"{col}{SR}"].font=font(9,True,WHITE); ds[f"{col}{SR}"].alignment=C
SA=f"{CL(FIRST)}{SR}:{EDGE}{SR}"
for v,bc in (("DLV",OK),("ISSUED",WARN),("KITTED",INFO),("OPEN",GREY)):
    ds.conditional_formatting.add(SA,FormulaRule(formula=[f'{CL(FIRST)}{SR}="{v}"'],fill=fill(bc),font=Font(name=F,color=WHITE,bold=True)))
ds.row_dimensions[SR].height=22
ds[f"C{SR+1}"]="Surplus WOs (beyond rep "+str(NREP)+")"; ds[f"C{SR+1}"].font=font(10,True,WARN)
ds[f"D{SR+1}"]=f'=COUNTIF({R("O")},"Surplus")&" WOs — filter Contract = Surplus on COOIS Data to see which"'; ds[f"D{SR+1}"].font=font(10,c=WARN)
ds[f"C{SR+2}"]="Not in plan"; ds[f"C{SR+2}"].font=font(10,True,CRIT)
ds[f"D{SR+2}"]=f'=COUNTIF({R("G")},"Not in plan")&" WOs in COOIS for codes not on the kitting plan"'; ds[f"D{SR+2}"].font=font(10,c=CRIT)
ds.freeze_panes="A4"
ds.page_setup.orientation="landscape"; ds.page_setup.fitToWidth=1; ds.page_setup.fitToHeight=1; ds.sheet_properties.pageSetUpPr.fitToPage=True
ds.print_area=f"A1:{EDGE}{SR+2}"

# ---------- How To Use ----------
hu=wb.create_sheet("How To Use"); hu.sheet_view.showGridLines=False
hu.column_dimensions["B"].width=28; hu.column_dimensions["C"].width=105
hu["B2"]="HOW THE KITTING COUNT WORKS"; hu["B2"].font=font(18,True,NAVY)
rows=[("Refresh (weekly)","",True),
 ("1. Run COOIS","Material = the 14 assy codes (multiple selection). Exclude TECO as usual. Layout must include: Order, Material Number, Material description, Order quantity, System Status, Release date (actual).",False),
 ("2. Paste","Export to spreadsheet, select all, copy, and paste into 'COOIS Raw' cell A1 (headers in row 1). Clear old data first. Column order does not matter — headers are matched by name.",False),
 ("3. Read","The Dashboard recalculates. Nothing else to type.",False),
 ("Definitions","",True),
 ("Kitted","A WO is kitted when COOIS shows it released and printed: status contains PRT (or PPRT). Printing the order papers / pick list is the production controller's kitting step.",False),
 ("Issued (GMPS)","Goods movement posted: components issued to the WO in SAP.",False),
 ("Delivered (DLV)","Finished assembly goods-receipted.",False),
 ("Repeater kits","Kitted WOs ÷ qty per repeater (from 'Kitting Plan'), rounded down. REPEATERS KITTED = the lowest value across all 14 codes, because a repeater needs every code.",False),
 ("Repeater #","Each WO is given a repeater number by release order within its code (oldest first): seq ÷ qty per repeater, rounded up. E.g. spool orders 1–24 = Rep 1, 25–48 = Rep 2.",False),
 ("Surplus","WOs numbered beyond the contract repeaters (13). They are extra releases — usually rework / replacement orders whose original was not TECO'd. Review and TECO as needed.",False),
 ("How to check '13'","Filter 'COOIS Data' on Assy Code: the count of WOs ÷ qty per repeater gives the repeaters kitted for that code. The Dashboard shows the lowest — that is the answer for the contract.",False)]
r=4
for k,v,h in rows:
    if h: r+=1; hu[f"B{r}"]=k; hu[f"B{r}"].font=font(12,True,ROSE); r+=1; continue
    hu[f"B{r}"]=k; hu[f"B{r}"].font=font(11,True); hu[f"B{r}"].alignment=Alignment(vertical="top")
    hu[f"C{r}"]=v; hu[f"C{r}"].font=font(11); hu[f"C{r}"].alignment=Alignment(wrap_text=True,vertical="top"); hu.row_dimensions[r].height=34; r+=1

wb.move_sheet("COOIS Raw",offset=2)
wb.calculation=CalcProperties(fullCalcOnLoad=True)
wb.active=0
wb.save(OUT)

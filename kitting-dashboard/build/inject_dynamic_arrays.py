"""Add Excel dynamic-array metadata so t="array" cells spill in Microsoft 365.
usage: inject_da.py in.xlsx out.xlsx [widen]   widen = test-only: widen array refs so LibreOffice shows full spill"""
import sys,zipfile,re
src,dst=sys.argv[1],sys.argv[2]; widen=len(sys.argv)>3
z=zipfile.ZipFile(src); files={n:z.read(n) for n in z.namelist()}; order=z.namelist(); z.close()
meta=('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<metadata xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:xda="http://schemas.microsoft.com/office/spreadsheetml/2017/dynamicarray">'
 '<metadataTypes count="1"><metadataType name="XLDAPR" minSupportedVersion="120000" copy="1" pasteAll="1" pasteValues="1" merge="1" splitFirst="1" rowColShift="1" clearFormats="1" clearComments="1" assign="1" coerce="1" cellMeta="1"/></metadataTypes>'
 '<futureMetadata name="XLDAPR" count="1"><bk><extLst><ext uri="{bdbb8cdc-fa1e-496e-a857-3c3f30c029c3}"><xda:dynamicArrayProperties fDynamic="1" fCollapsed="0"/></ext></extLst></bk></futureMetadata>'
 '<cellMetadata count="1"><bk><rc t="1" v="0"/></bk></cellMetadata></metadata>').encode()
files["xl/metadata.xml"]=meta
if "xl/metadata.xml" not in order: order.append("xl/metadata.xml")
ct=files["[Content_Types].xml"].decode()
if "metadata.xml" not in ct: ct=ct.replace("</Types>",'<Override PartName="/xl/metadata.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheetMetadata+xml"/></Types>')
files["[Content_Types].xml"]=ct.encode()
rel=files["xl/_rels/workbook.xml.rels"].decode()
if "sheetMetadata" not in rel: rel=rel.replace("</Relationships>",'<Relationship Id="rIdDAmeta" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sheetMetadata" Target="metadata.xml"/></Relationships>')
files["xl/_rels/workbook.xml.rels"]=rel.encode()
def widen_ref(m):
    ref=m.group(1)
    col=re.match(r"([A-Z]+)(\d+)",ref); c,rw=col.group(1),int(col.group(2))
    return f'ref="{ref}:Z{rw+60}"' if c=="B" else f'ref="{ref}"'
for n in files:
    if n.startswith("xl/worksheets/sheet") and n.endswith(".xml"):
        x=files[n].decode()
        x=re.sub(r'<c r="([A-Z]+\d+)"((?:(?! cm=)[^>])*)><f t="array"',lambda m:f'<c r="{m.group(1)}"{m.group(2)} cm="1"><f t="array"',x)
        if widen: x=re.sub(r'ref="(B21)"',lambda m:'ref="B21:L80"',x)
        files[n]=x.encode()
z=zipfile.ZipFile(dst,"w",zipfile.ZIP_DEFLATED)
for n in order: z.writestr(n,files[n])
z.close()

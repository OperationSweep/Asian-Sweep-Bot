"""Generate a sample scan sheet shaped like a typical kitting export.

Run: python tests/make_sample.py
Produces tests/sample_kitting.xlsx - used by test_sheet.py and by
`python run.py --sheet tests/sample_kitting.xlsx --dry-run` so the whole
pipeline can be rehearsed without SAP or a real spreadsheet.
"""

from pathlib import Path

import pandas as pd

ROWS = [
    # Order on the first row of each block only, the rest blank - the layout a
    # barcode scanner usually produces.
    ("4500123456", "FLT-1550-DWDM", "SN-AA1001", 1, "optic filter"),
    ("",           "FLT-1550-DWDM", "SN-AA1002", 1, "optic filter"),
    ("",           "CPL-2X2-50-50", "SN-BB2001", 2, "coupler"),
    ("4500123457", "FLT-1310-CWDM", "SN-AA1003", 1, "optic filter"),
    ("",           "CPL-1X4-SPLIT", "SN-BB2002", 4, "coupler"),
    ("4500123458", "CPL-1X8-SPLIT", "SN-BB2003", 8, "coupler"),
]

def main() -> None:
    frame = pd.DataFrame(
        ROWS, columns=["Work Order", "Material", "Serial Number", "Qty", "Type"]
    )
    out = Path(__file__).with_name("sample_kitting.xlsx")
    frame.to_excel(out, index=False)
    print(f"wrote {out}")

if __name__ == "__main__":
    main()

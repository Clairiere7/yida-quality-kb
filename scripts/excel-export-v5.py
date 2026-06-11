"""
Excel 截图导出 v5 — 截整个 sheet 的带图形区域
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from win32com.client import Dispatch

EXCEL = r"C:\Users\26433\Desktop\南洋万邦实习材料\P100204013检规(1).xlsx"
OUT = Path(r"C:\Users\26433\Desktop\南洋万邦实习材料\knowledge-base\drawings")

SHEETS = {
    "P100206001": "P100206001",
    "P100206002": "P100204013",
    "P100206003集流管": "P100206003",
    "P100206004集流管": "P100206004",
    "P100206006翅片": "P100204006",
}

def main():
    print("Starting Excel...")
    excel = Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False

    try:
        wb = excel.Workbooks.Open(EXCEL, ReadOnly=False)

        for sheet_name, pid in SHEETS.items():
            ws = wb.Worksheets(sheet_name)
            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            for f in out_dir.glob("excel_export_*.png"):
                f.unlink()

            try: ws.Unprotect()
            except: pass

            used = ws.UsedRange
            rows = used.Rows.Count
            cols = used.Columns.Count
            print(f"\n{sheet_name} -> {pid}: {rows} rows x {cols} cols")

            # Copy the used range as picture (captures shapes + cells together)
            used.CopyPicture(1, 2)  # xlScreen=1, xlBitmap=2

            chart_name = f"_X_{pid}"
            try: excel.Charts(chart_name).Delete()
            except: pass

            chart = excel.Charts.Add()
            chart.Name = chart_name
            chart.Paste()

            out_path = str(out_dir / "excel_export_01.png")
            chart.Export(out_path, "PNG")
            chart.Delete()

            sz = Path(out_path).stat().st_size
            print(f"  -> excel_export_01.png {sz//1024}KB")
            total = 1

        print(f"\nDone: {len(SHEETS)} sheets exported")

    finally:
        wb.Close(SaveChanges=False)
        excel.Quit()

if __name__ == "__main__":
    main()

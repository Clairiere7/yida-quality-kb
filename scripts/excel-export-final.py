"""
Excel 导出 FINAL — Select+CopyPicture + 超大Chart输出
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import pythoncom
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
    pythoncom.CoInitialize()
    print("Starting Excel...")
    excel = Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False

    try:
        wb = excel.Workbooks.Open(EXCEL, ReadOnly=False, UpdateLinks=False)
        time.sleep(1)
        total = 0

        for sheet_name, pid in SHEETS.items():
            ws = wb.Worksheets(sheet_name)
            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            for f in out_dir.glob("excel_export_*.png"):
                f.unlink()

            try: ws.Unprotect()
            except: pass

            # Option A: range around each shape
            shapes = ws.Shapes
            print(f"\n{sheet_name} -> {pid} ({shapes.Count} shapes)")

            # If too many failures on individual shapes, fall back to full sheet
            for i in range(1, shapes.Count + 1):
                shape = shapes.Item(i)
                if shape.Type not in (13, 6): continue  # Picture=13, Group=6

                try:
                    shape.Select()
                    sel = excel.Selection
                    # Use range around shape — copy just the relevant cells
                    tl = shape.TopLeftCell
                    br = shape.BottomRightCell
                    tr = max(1, tl.Row - 3)
                    btr = min(ws.UsedRange.Rows.Count, br.Row + 3)
                    lc = max(1, tl.Column - 1)
                    rc = min(ws.UsedRange.Columns.Count, br.Column + 1)

                    rng = ws.Range(ws.Cells(tr, lc), ws.Cells(btr, rc))
                    rng.CopyPicture(1, 2)  # xlScreen=1, xlBitmap=2

                except:
                    # Fallback: try to copy JUST the whole used range
                    try: ws.UsedRange.CopyPicture(1, 2)
                    except: continue

                cname = f"_EE_{pid}_{total}"
                try: excel.Charts(cname).Delete()
                except: pass

                chart = excel.Charts.Add()
                chart.Name = cname
                # Large chart for high-res output
                chart.ChartArea.Width = 1920
                chart.ChartArea.Height = 1440
                chart.Paste()

                out_path = str(out_dir / f"excel_export_{total+1:02d}.png")
                chart.Export(out_path, "PNG")
                chart.Delete()

                sz = Path(out_path).stat().st_size
                kb = sz // 1024
                tag = f"{kb}KB" if kb > 10 else f"TOO_SMALL({sz}B)"
                print(f"  {Path(out_path).name} {tag}")
                total += 1

        print(f"\nTotal: {total} images")

    finally:
        try: wb.Close(SaveChanges=False)
        except: pass
        excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()

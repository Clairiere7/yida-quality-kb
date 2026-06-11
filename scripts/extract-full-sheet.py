"""
Extract full sheet + row-range sections for high-quality drawings.
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import pythoncom
from win32com.client import Dispatch

EXCEL = r"C:\Users\26433\Desktop\南洋万邦实习材料\P100204013检规(1).xlsx"
OUT = Path(r"C:\Users\26433\Desktop\南洋万邦实习材料\knowledge-base\drawings")

# Row ranges for drawing sections (estimated from Excel structure)
# Adjust these based on which rows contain CAD drawings
PRODUCT_SECTIONS = {
    "P100206003": {
        "sheet": "P100206003集流管",
        "ranges": [
            ("drawing_01.png", 1, 22, 1, 12),   # left half
            ("drawing_02.png", 1, 22, 13, 22),  # right half
        ]
    }
}

def copy_range(excel, ws, r1, r2, c1, c2):
    rng = ws.Range(ws.Cells(r1, c1), ws.Cells(r2, c2))
    rng.CopyPicture(1, 2)

def main():
    pythoncom.CoInitialize()
    excel = Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    try:
        wb = excel.Workbooks.Open(EXCEL, ReadOnly=False, UpdateLinks=False)
        time.sleep(1)

        for pid, cfg in PRODUCT_SECTIONS.items():
            ws = wb.Worksheets(cfg["sheet"])
            try: ws.Unprotect()
            except: pass
            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            # First: full sheet
            try:
                ur = ws.UsedRange
                ur.CopyPicture(1, 2)
                cname = "_fullsheet"
                try: excel.Charts(cname).Delete()
                except: pass
                chart = excel.Charts.Add()
                chart.Name = cname
                chart.ChartArea.Width = 3840
                chart.ChartArea.Height = 2160
                chart.Paste()
                chart.Export(str(out_dir / "sheet_full.png"), "PNG")
                chart.Delete()
                sz = Path(out_dir / "sheet_full.png").stat().st_size
                print(f"[{pid}] Full sheet: {sz//1024}KB")
            except Exception as e:
                print(f"[{pid}] Full sheet FAIL: {e}")

            # Then: section-by-section
            for name, r1, r2, c1, c2 in cfg["ranges"]:
                try:
                    rng = ws.Range(ws.Cells(r1, c1), ws.Cells(r2, c2))
                    rng.CopyPicture(1, 2)
                    cname = f"_sec_{name}"
                    try: excel.Charts(cname).Delete()
                    except: pass
                    chart = excel.Charts.Add()
                    chart.Name = cname
                    chart.ChartArea.Width = 2560
                    chart.ChartArea.Height = 1920
                    chart.Paste()
                    chart.Export(str(out_dir / name), "PNG")
                    chart.Delete()
                    sz = Path(out_dir / name).stat().st_size
                    print(f"  {name}: {sz//1024}KB (rows {r1}-{r2}, cols {c1}-{c2})")
                except Exception as e:
                    print(f"  {name} FAIL: {e}")

    finally:
        try: wb.Close(SaveChanges=False)
        except: pass
        excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()

"""
Excel 逐图导出 v4 — 解锁形状后再 CopyPicture
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
        # Unprotect workbook structure if needed
        try: wb.Unprotect()
        except: pass
        total = 0

        for sheet_name, pid in SHEETS.items():
            ws = wb.Worksheets(sheet_name)
            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            for f in out_dir.glob("excel_export_*.png"):
                f.unlink()

            # Try to unprotect sheet (ignore if not protected)
            try:
                ws.Unprotect()
            except:
                pass

            shapes = ws.Shapes
            print(f"\n{sheet_name} -> {pid} ({shapes.Count} shapes)")

            for i in range(1, shapes.Count + 1):
                shape = shapes.Item(i)
                if shape.Type not in (13, 6):  # Picture or Group
                    continue

                sh_name = shape.Name
                try:
                    # Unlock: set LockAspectRatio, Placement, and Locked
                    try: shape.LockAspectRatio = False
                    except: pass
                    try: shape.Placement = 3  # xlFreeFloating
                    except: pass
                    try: shape.Locked = False
                    except: pass
                    try: shape.AlternativeText = ""
                    except: pass

                    # Alternate: select the shape then use Selection.CopyPicture
                    shape.Select()
                    sel = excel.Selection
                    sel.CopyPicture(1, 2)  # xlScreen=1, xlBitmap=2

                    # Create chart and paste
                    chart_name = f"_X_{pid}_{i}"
                    try: excel.Charts(chart_name).Delete()
                    except: pass

                    chart = excel.Charts.Add()
                    chart.Name = chart_name
                    chart.ChartArea.Width = max(shape.Width, 200)
                    chart.ChartArea.Height = max(shape.Height, 200)
                    chart.Paste()

                    out_path = str(out_dir / f"excel_export_{total+1:02d}.png")
                    chart.Export(out_path, "PNG")
                    chart.Delete()

                    sz = Path(out_path).stat().st_size
                    tag = f"{sz//1024}KB" if sz > 10240 else f"SMALL({sz}B)"
                    print(f"  {out_path.split(chr(92))[-1]} {tag} <-- {sh_name}")
                    total += 1

                except Exception as e:
                    print(f"  FAIL {sh_name}: {str(e)[:100]}")
                    try: chart.Delete()
                    except: pass

        print(f"\nTOTAL: {total} images")

    finally:
        wb.Close(SaveChanges=False)
        excel.Quit()

if __name__ == "__main__":
    main()

"""
Excel 导出 v6 — 逐个Shape范围截图，大尺寸 Chart 输出
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
    excel = None
    try:
        excel = Dispatch("Excel.Application")
    except:
        try:
            excel = Dispatch("Excel.Application")
        except Exception as e:
            print(f"Cannot start Excel: {e}")
            return

    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False

    try:
        print(f"Opening {EXCEL}...")
        wb = excel.Workbooks.Open(EXCEL, ReadOnly=False, UpdateLinks=False)
        time.sleep(1)

        for sheet_name, pid in SHEETS.items():
            ws = wb.Worksheets(sheet_name)
            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            for f in out_dir.glob("excel_export_*.png"):
                f.unlink()

            try: ws.Unprotect()
            except: pass

            shapes = ws.Shapes
            print(f"\n{sheet_name} -> {pid} ({shapes.Count} shapes)")

            count = 0
            for i in range(1, shapes.Count + 1):
                shape = shapes.Item(i)
                if shape.Type not in (13, 6):  # Picture=13, Group=6
                    continue

                sh_name = shape.Name
                try:
                    # Get the cells containing this shape with generous padding
                    tl = shape.TopLeftCell
                    br = shape.BottomRightCell
                    top_row = max(1, tl.Row - 5)
                    btm_row = min(ws.UsedRange.Rows.Count, br.Row + 5)
                    left_col = max(1, tl.Column - 2)
                    right_col = min(ws.UsedRange.Columns.Count, br.Column + 2)

                    rng = ws.Range(
                        ws.Cells(top_row, left_col),
                        ws.Cells(btm_row, right_col)
                    )
                    rng.CopyPicture(1, 2)  # xlScreen=1, xlBitmap=2

                    cname = f"_XX_{pid}_{i}"
                    try: excel.Charts(cname).Delete()
                    except: pass

                    chart = excel.Charts.Add()
                    chart.Name = cname
                    chart.ChartArea.Width = 900
                    chart.ChartArea.Height = 675
                    chart.Paste()

                    out_path = str(out_dir / f"excel_export_{count+1:02d}.png")
                    chart.Export(out_path, "PNG")
                    chart.Delete()

                    sz = Path(out_path).stat().st_size
                    tag = f"{sz//1024}KB" if sz > 8192 else f"SMALL({sz}B)"
                    print(f"  OK {Path(out_path).name} {tag} <-- {sh_name}")
                    count += 1

                except Exception as e:
                    print(f"  SKIP {sh_name}: {str(e)[:100]}")
                    try: chart.Delete()
                    except: pass

        print(f"\nDone!")

    finally:
        try: wb.Close(SaveChanges=False)
        except: pass
        excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()

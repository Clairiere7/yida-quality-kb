"""
Extract tech requirements images from Excel source.
Drawings section at bottom of each sheet needs re-extraction with higher quality.
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
    "P100204013": "P100206002",
}

def main():
    pythoncom.CoInitialize()
    excel = Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    try:
        wb = excel.Workbooks.Open(EXCEL, ReadOnly=False, UpdateLinks=False)
        time.sleep(1)

        total = 0
        for sheet_name, pid in SHEETS.items():
            ws = wb.Worksheets(sheet_name)
            try: ws.Unprotect()
            except: pass

            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            # Remove old tech_req files
            for f in out_dir.glob("tech_req*.png"):
                f.unlink()
            for f in out_dir.glob("extracted_*.png"):
                f.unlink()

            shapes = ws.Shapes
            print(f"\n{sheet_name} -> {pid} ({shapes.Count} shapes)")

            ur = ws.UsedRange
            total_rows = ur.Rows.Count
            total_cols = ur.Columns.Count
            print(f"  UsedRange: {total_rows} rows x {total_cols} cols")

            # Strategy: copy different row sections to cover all drawings + tech requirements
            # The bottom section usually contains tech requirements drawings

            # Full sheet capture
            for label, r1, r2 in [
                ("full", 1, total_rows),
                ("drawings_top", 1, max(20, total_rows // 2)),
                ("drawings_bottom", max(1, total_rows - 25), total_rows),
                ("tech_req_section", max(1, total_rows - 15), total_rows),
            ]:
                try:
                    rng = ws.Range(ws.Cells(r1, 1), ws.Cells(r2, total_cols))
                    rng.CopyPicture(1, 2)
                    cname = f"_tr_{pid}_{label}"
                    try: excel.Charts(cname).Delete()
                    except: pass
                    chart = excel.Charts.Add()
                    chart.Name = cname
                    chart.ChartArea.Width = 3840
                    chart.ChartArea.Height = 2400
                    chart.Paste()
                    fname = f"tech_req_section_{label}.png"
                    chart.Export(str(out_dir / fname), "PNG")
                    chart.Delete()
                    sz = (out_dir / fname).stat().st_size
                    print(f'  {fname}: {sz//1024}KB (rows {r1}-{r2})')
                    total += 1
                except Exception as e:
                    print(f'  {label} FAIL: {e}')

            # Also capture specific row groups that might contain individual tech requirement images
            try:
                # Identify rows containing pictures/shapes
                for i in range(1, total_rows, 10):
                    end_row = min(i + 12, total_rows)
                    rng = ws.Range(ws.Cells(i, 1), ws.Cells(end_row, total_cols))
                    try:
                        rng.CopyPicture(1, 2)
                        cname = f"_tr_{pid}_row{i}"
                        try: excel.Charts(cname).Delete()
                        except: pass
                        chart = excel.Charts.Add()
                        chart.Name = cname
                        chart.ChartArea.Width = 3840
                        chart.ChartArea.Height = 2400
                        chart.Paste()
                        fname = f"section_row{i:02d}_to_{end_row:02d}.png"
                        chart.Export(str(out_dir / fname), "PNG")
                        chart.Delete()
                        sz = (out_dir / fname).stat().st_size
                        if sz > 20000:  # only keep if meaningful
                            print(f'  {fname}: {sz//1024}KB')
                            total += 1
                        else:
                            (out_dir / fname).unlink()
                    except:
                        pass
            except Exception as e:
                print(f'  Row-wise extraction FAIL: {e}')

        print(f'\nTotal: {total} images extracted')

    finally:
        try: wb.Close(SaveChanges=False)
        except: pass
        excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()

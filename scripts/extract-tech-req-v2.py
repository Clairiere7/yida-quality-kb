"""
Extract tech requirements — brute force approach.
Re-open Excel fresh, unlock aggressively, copy ranges.
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import pythoncom
from win32com.client import Dispatch

EXCEL = r"C:\Users\26433\Desktop\南洋万邦实习材料\P100204013检规(1).xlsx"
OUT = Path(r"C:\Users\26433\Desktop\南洋万邦实习材料\knowledge-base\drawings")

def main():
    pythoncom.CoInitialize()
    excel = Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False

    try:
        wb = excel.Workbooks.Open(EXCEL, ReadOnly=False, UpdateLinks=False)
        time.sleep(2)

        total = 0

        for sheet_name, pid in [("P100206001", "P100206001"), ("P100206002", "P100204013")]:
            try:
                ws = wb.Worksheets(sheet_name)
            except Exception as e:
                print(f"Sheet {sheet_name} not found: {e}")
                continue

            # Unprotect sheet
            try: ws.Unprotect()
            except: pass
            # Protect/Unprotect to clear lock flags
            try: ws.Protect(DrawingObjects=False, Contents=True, Scenarios=True)
            except: pass
            try: ws.Unprotect()
            except: pass
            try: ws.EnableSelection = 0  # xlNoRestrictions
            except: pass

            # Disable shape lock
            try:
                for i in range(1, ws.Shapes.Count + 1):
                    shape = ws.Shapes.Item(i)
                    try: shape.Locked = False
                    except: pass
            except:
                pass

            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            ur = ws.UsedRange
            rows = ur.Rows.Count
            cols = ur.Columns.Count
            print(f"\n{sheet_name} -> {pid}: {rows}r x {cols}c, {ws.Shapes.Count} shapes")

            # Copy entire used range
            try:
                ur.CopyPicture(1, 2)
                cname = "_full"
                try: excel.Charts(cname).Delete()
                except: pass
                chart = excel.Charts.Add()
                chart.Name = cname
                chart.ChartArea.Width = 3840
                chart.ChartArea.Height = 2400
                chart.Paste()
                chart.Export(str(out_dir / "tech_req_full.png"), "PNG")
                chart.Delete()
                sz = Path(out_dir / "tech_req_full.png").stat().st_size
                print(f"  Full sheet: {sz//1024}KB")
                total += 1
            except Exception as e:
                print(f"  Full sheet FAIL: {e}")

            # Copy bottom section (where tech requirements typically are)
            for r1 in range(max(1, rows-30), rows+1, 5):
                r2 = min(r1 + 8, rows)
                if r2 <= r1: continue
                try:
                    rng = ws.Range(ws.Cells(r1, 1), ws.Cells(r2, cols))
                    rng.CopyPicture(1, 2)
                    cname = f"_r{r1}"
                    try: excel.Charts(cname).Delete()
                    except: pass
                    chart = excel.Charts.Add()
                    chart.Name = cname
                    chart.ChartArea.Width = 3840
                    chart.ChartArea.Height = 2400
                    chart.Paste()
                    fname = f"tech_req_{r1}-{r2}.png"
                    chart.Export(str(out_dir / fname), "PNG")
                    chart.Delete()
                    sz = Path(out_dir / fname).stat().st_size
                    if sz > 30000:
                        print(f"  {fname}: {sz//1024}KB")
                        total += 1
                    else:
                        (out_dir / fname).unlink()
                except:
                    pass

            # Copy top section (drawings area)
            for r1 in range(1, min(30, rows), 5):
                r2 = min(r1 + 8, rows)
                try:
                    rng = ws.Range(ws.Cells(r1, 1), ws.Cells(r2, cols))
                    rng.CopyPicture(1, 2)
                    cname = f"_t{r1}"
                    try: excel.Charts(cname).Delete()
                    except: pass
                    chart = excel.Charts.Add()
                    chart.Name = cname
                    chart.ChartArea.Width = 3840
                    chart.ChartArea.Height = 2400
                    chart.Paste()
                    fname = f"section_top_{r1}-{r2}.png"
                    chart.Export(str(out_dir / fname), "PNG")
                    chart.Delete()
                    sz = Path(out_dir / fname).stat().st_size
                    if sz > 30000:
                        print(f"  {fname}: {sz//1024}KB")
                        total += 1
                    else:
                        (out_dir / fname).unlink()
                except:
                    pass

        print(f"\nTotal: {total} images")

    finally:
        try: wb.Close(SaveChanges=False)
        except: pass
        excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()

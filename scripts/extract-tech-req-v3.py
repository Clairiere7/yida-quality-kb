"""
Extract tech requirements v3 — don't set chart size, just paste+export directly.
Also try PasteSpecial and JPEG export.
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import pythoncom
from win32com.client import Dispatch, constants

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

        for sheet_name, pid in [("P100206001", "P100206001"), ("P100206002", "P100204013")]:
            ws = wb.Worksheets(sheet_name)
            try: ws.Unprotect()
            except: pass

            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            ur = ws.UsedRange
            rows = ur.Rows.Count
            cols = ur.Columns.Count
            print(f"{sheet_name}: {rows}r x {cols}c")

            # Approach 1: ExportAsFixedFormat to image via PDF intermediate (hacky)
            # Better: use Excel's Camera tool or just copy smaller chunks

            # Let's try: save sheet as HTML/PNG using Excel's built-in export
            # Actually, let's try copying with ScreenUpdating off
            excel.ScreenUpdating = False

            # Try to copy the range and paste into a chart — but DON'T set ChartArea sizes
            for label, r1, r2 in [
                ("full", 1, rows),
                ("top_half", 1, rows // 2),
                ("bottom_half", rows // 2, rows),
                ("bottom_third", rows * 2 // 3, rows),
            ]:
                if r2 <= r1: continue
                try:
                    rng = ws.Range(ws.Cells(r1, 1), ws.Cells(r2, cols))
                    rng.CopyPicture(1, 2)  # xlScreen=1, xlBitmap=2

                    cname = f"_ex_{pid}_{label}"
                    try: excel.Charts(cname).Delete()
                    except: pass

                    chart = excel.Charts.Add()
                    chart.Name = cname
                    chart.Paste()
                    # Don't set ChartArea size — use default
                    fname = f"tech_req_{label}.png"
                    chart.Export(str(out_dir / fname), "PNG")
                    chart.Delete()

                    sz = (out_dir / fname).stat().st_size
                    print(f"  {fname}: {sz//1024}KB")
                except Exception as e:
                    print(f"  {label} FAIL: {e}")

        print("\nDone.")

    finally:
        try: wb.Close(SaveChanges=False)
        except: pass
        excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()

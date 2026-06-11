"""
Extract ALL shapes from Excel sheets — including auto-shapes and freeforms.
Saves each shape as a named PNG file.
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import pythoncom
from win32com.client import Dispatch, constants

EXCEL = r"C:\Users\26433\Desktop\南洋万邦实习材料\P100204013检规(1).xlsx"
OUT = Path(r"C:\Users\26433\Desktop\南洋万邦实习材料\knowledge-base\drawings")

SHEETS = {
    "P100206001": "P100206001",
    "P100206003集流管": "P100206003",
    "P100206004集流管": "P100206004",
    "P100206006翅片": "P100204006",
}

def main():
    pythoncom.CoInitialize()
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

            try: ws.Unprotect()
            except: pass

            shapes = ws.Shapes
            print(f"\n{sheet_name} -> {pid}: {shapes.Count} shapes total")

            for i in range(1, shapes.Count + 1):
                shape = shapes.Item(i)
                stype = shape.Type  # 1=AutoShape, 6=Group, 13=Picture, 14=TextBox, etc.
                print(f"  Shape {i}: type={stype}, name='{shape.Name}'", end='')

                # Try to get position info
                try:
                    tl = shape.TopLeftCell
                    br = shape.BottomRightCell
                    print(f" pos={tl.Address}-{br.Address}", end='')
                except:
                    pass

                # Export by copying the range AROUND the shape (not the shape itself)
                if stype in (1, 6, 13, 14):
                    try:
                        tr = max(1, shape.TopLeftCell.Row - 5)
                        br_max = min(ws.UsedRange.Rows.Count, shape.BottomRightCell.Row + 5)
                        lc = max(1, shape.TopLeftCell.Column - 1)
                        rc = min(ws.UsedRange.Columns.Count, shape.BottomRightCell.Column + 1)

                        rng = ws.Range(ws.Cells(tr, lc), ws.Cells(br_max, rc))
                        rng.CopyPicture(1, 2)  # xlScreen=1, xlBitmap=2

                        cname = f"shape_extract_{total}"
                        try: excel.Charts(cname).Delete()
                        except: pass

                        chart = excel.Charts.Add()
                        chart.Name = cname
                        chart.ChartArea.Width = 1600
                        chart.ChartArea.Height = 1200
                        chart.Paste()

                        # Save with shape info in filename
                        fname = f"shape_{i:02d}_type{stype}_{shape.Name.replace(' ', '_')[:30]}.png"
                        out_path = str(out_dir / fname)
                        chart.Export(out_path, "PNG")
                        chart.Delete()

                        sz = Path(out_path).stat().st_size
                        print(f" -> {fname} ({sz//1024}KB)")
                        total += 1
                    except Exception as e:
                        print(f" -> FAIL: {e}")
                else:
                    print(' (skipped)')

        print(f"\nTotal: {total} shapes exported")

    finally:
        try: wb.Close(SaveChanges=False)
        except: pass
        excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()

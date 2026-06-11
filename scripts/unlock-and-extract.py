"""
Unprotect sheets aggressively, then extract all shapes as images.
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
    "P100206003集流管": "P100206003",
    "P100206004集流管": "P100206004",
    "P100206006翅片": "P100204006",
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
            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            # Aggressive unprotect
            for pw in (None, '', '123', '1234', 'password', 'admin'):
                try:
                    if pw is None:
                        ws.Unprotect()
                    else:
                        ws.Unprotect(pw)
                    print(f'{sheet_name}: Unprotected (pw={pw})')
                    break
                except:
                    pass
            else:
                print(f'{sheet_name}: Could not unprotect')

            # Try to check if sheet is protected
            try:
                prot = ws.ProtectContents
                print(f'  ProtectContents={prot}')
            except:
                pass

            shapes = ws.Shapes
            print(f'  {shapes.Count} shapes')

            for i in range(1, shapes.Count + 1):
                shape = shapes.Item(i)
                stype = shape.Type
                print(f'  Shape {i}: type={stype}, name={shape.Name}', end='')
                try:
                    tl = shape.TopLeftCell
                    br = shape.BottomRightCell
                    print(f' {tl.Address}-{br.Address}', end='')
                except:
                    pass

                try:
                    tr = max(1, shape.TopLeftCell.Row - 8)
                    br_m = min(ws.UsedRange.Rows.Count, shape.BottomRightCell.Row + 8)
                    lc = max(1, shape.TopLeftCell.Column - 2)
                    rc = min(ws.UsedRange.Columns.Count, shape.BottomRightCell.Column + 2)
                    rng = ws.Range(ws.Cells(tr, lc), ws.Cells(br_m, rc))
                    rng.CopyPicture(1, 2)

                    cname = f"_ee_{total}"
                    try: excel.Charts(cname).Delete()
                    except: pass
                    chart = excel.Charts.Add()
                    chart.Name = cname
                    chart.Paste()
                    fname = f"extracted_{i:02d}.png"
                    out_path = str(out_dir / fname)
                    chart.Export(out_path, "PNG")
                    chart.Delete()
                    sz = Path(out_path).stat().st_size
                    print(f' -> {fname} ({sz//1024}KB)')
                    total += 1
                except Exception as e:
                    print(f' -> FAIL: {e}')

        print(f'\nTotal exported: {total}')

    finally:
        try: wb.Close(SaveChanges=False)
        except: pass
        excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()

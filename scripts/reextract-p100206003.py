"""
单产品重提取：只处理 P100206003，生成新图纸。
"""
import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import pythoncom
from win32com.client import Dispatch

EXCEL = r"C:\Users\26433\Desktop\南洋万邦实习材料\P100204013检规(1).xlsx"
OUT = Path(r"C:\Users\26433\Desktop\南洋万邦实习材料\knowledge-base\drawings\P100206003")

def main():
    pythoncom.CoInitialize()
    excel = Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    try:
        wb = excel.Workbooks.Open(EXCEL, ReadOnly=False, UpdateLinks=False)
        time.sleep(1)

        ws = wb.Worksheets("P100206003集流管")
        try: ws.Unprotect()
        except: pass

        shapes = ws.Shapes
        print(f"Shapes: {shapes.Count}")

        for i in range(1, shapes.Count + 1):
            shape = shapes.Item(i)
            stype = shape.Type
            print(f"Shape {i}: type={stype} name={shape.Name}", end='')
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

                cname = f"_new_{i}"
                try: excel.Charts(cname).Delete()
                except: pass
                chart = excel.Charts.Add()
                chart.Name = cname
                chart.Paste()
                fname = f"_new_{i:02d}.png"
                out_path = str(OUT / fname)
                chart.Export(out_path, "PNG")
                chart.Delete()
                sz = Path(out_path).stat().st_size
                print(f' -> {fname} ({sz//1024}KB)')
            except Exception as e:
                print(f' -> FAIL: {e}')

    finally:
        try: wb.Close(SaveChanges=False)
        except: pass
        excel.Quit()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    main()

"""
Excel 逐图导出 v2 — 直接操作 Shape 范围截图
"""
import os, sys, json
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
    print("=" * 50)
    excel = Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False

    try:
        wb = excel.Workbooks.Open(EXCEL, ReadOnly=True)
        total = 0

        for sheet_name, pid in SHEETS.items():
            ws = wb.Worksheets(sheet_name)
            out_dir = OUT / pid
            out_dir.mkdir(parents=True, exist_ok=True)

            # Clear old exports
            for f in out_dir.glob("excel_export_*.png"):
                f.unlink()

            shapes = ws.Shapes
            count = 0

            for i in range(1, shapes.Count + 1):
                shape = shapes.Item(i)

                # Only process Picture types (red circles are often separate Group shapes)
                if shape.Type not in (13, 6):  # msoPicture=13, msoGroup=6
                    continue

                sh_name = shape.Name
                try:
                    # Select the shape and its surrounding range
                    shape.Select()

                    # Use Excel's Camera tool approach:
                    # 1. Copy the shape
                    shape.Copy()

                    # 2. Get or create a temp chart, paste, export
                    chart_name = f"_tmp_{pid}_{count}"
                    try:
                        c = excel.Charts(chart_name)
                        c.Delete()
                    except:
                        pass

                    chart = excel.Charts.Add()
                    chart.Name = chart_name

                    # Size the chart to match the shape dimensions
                    try:
                        chart.ChartArea.Width = shape.Width
                        chart.ChartArea.Height = shape.Height
                    except:
                        pass

                    chart.Paste()

                    out_path = str(out_dir / f"excel_export_{count+1:02d}.png")
                    chart.Export(out_path, "PNG")

                    chart.Delete()
                    count += 1

                    # Check file size
                    size = Path(out_path).stat().st_size
                    print(f"  [{pid}] {out_path.split(chr(92))[-1]} <-- {sh_name} ({size//1024}KB)")

                except Exception as e:
                    print(f"  SKIP {sh_name}: {e}")
                    try:
                        chart.Delete()
                    except:
                        pass

            total += count

        print(f"\nDone: {total} images exported")

    finally:
        wb.Close(SaveChanges=False)
        excel.Quit()


if __name__ == "__main__":
    main()

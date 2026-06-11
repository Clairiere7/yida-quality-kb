"""
Excel 逐图导出脚本 — 将每个 sheet 中嵌入的 CAD 图 + 红圈标注合成导出
输出: knowledge-base/drawings/<productId>/excel_export_<N>.png
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from win32com.client import Dispatch, constants

EXCEL_PATH = r"C:\Users\26433\Desktop\南洋万邦实习材料\P100204013检规(1).xlsx"
DRAWINGS_DIR = Path(r"C:\Users\26433\Desktop\南洋万邦实习材料\knowledge-base\drawings")

# Sheet → ProductId mapping
SHEET_PRODUCT = {
    "P100206001": "P100206001",    # 冷凝器芯体
    "P100206002": "P100204013",    # 冷凝器芯体总成
    "P100206003集流管": "P100206003",  # 集流管
    "P100206004集流管": "P100206004",  # 集流管2
    "P100206006翅片": "P100204006",    # 翅片
}

def export_sheet_images(excel, sheet_name, product_id):
    """导出某个 sheet 中所有嵌入图片（含红圈标注）"""
    try:
        ws = excel.Worksheets(sheet_name)
    except:
        print(f"  ⚠ 找不到 sheet: {sheet_name}")
        return 0

    # 确保目标目录存在
    out_dir = DRAWINGS_DIR / product_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # 先清空旧导出
    for old in out_dir.glob("excel_export_*.png"):
        old.unlink()

    shapes = ws.Shapes
    count = 0
    exported_names = {}

    for i in range(1, shapes.Count + 1):
        shape = shapes.Item(i)

        # 只处理图片类型的 shape (msoPicture = 13) 或组合 (msoGroup = 6)
        if shape.Type not in (13, 6):  # 13=Picture, 6=Group
            continue

        # 跳过太小或太小的（<10KB 的是图标/标记，不是图纸）
        shape_name = shape.Name

        # 获取图片位置
        try:
            tl = shape.TopLeftCell
            br = shape.BottomRightCell
            if tl is None or br is None:
                continue
            # 计算图片覆盖的单元格范围
            top_row = tl.Row
            left_col = tl.Column
            bottom_row = br.Row
            right_col = br.Column

            # 扩大范围以包含标注文字和红圈
            top_row = max(1, top_row - 2)
            bottom_row = min(ws.UsedRange.Rows.Count, bottom_row + 2)
            left_col = max(1, left_col - 1)
            right_col = min(ws.UsedRange.Columns.Count, right_col + 1)
        except:
            continue

        # 构造单元格范围
        try:
            rng = ws.Range(
                ws.Cells(top_row, left_col),
                ws.Cells(bottom_row, right_col)
            )
        except:
            continue

        # 复制该区域为图片
        try:
            rng.CopyPicture(Format=2)  # xlBitmap = 2
        except:
            continue

        # 创建临时图表来粘贴并导出
        try:
            chart_name = f"_tmp_chart_{product_id}_{count}"
            try:
                old_chart = excel.Charts(chart_name)
                old_chart.Delete()
            except:
                pass

            chart = excel.Charts.Add()
            chart.Name = chart_name
            chart.ChartArea.ClearContents()
            chart.Paste()

            # 导出为 PNG
            out_path = out_dir / f"excel_export_{count+1:02d}.png"
            chart.Export(str(out_path), "PNG")

            chart.Delete()
            count += 1
            exported_names[f"excel_export_{count:02d}.png"] = shape_name
            print(f"    OK {out_path.name} <-- {shape_name}")
        except Exception as e:
            print(f"    ⚠ {shape_name} 导出失败: {e}")
            try:
                chart.Delete()
            except:
                pass

    # 写映射文件
    if count > 0:
        map_path = out_dir / f"export_map.json"
        with open(map_path, 'w', encoding='utf-8') as f:
            json.dump({"productId": product_id, "sheet": sheet_name, "exportedImages": exported_names}, f, ensure_ascii=False, indent=2)

    return count


def main():
    print("═" * 50)
    print("Excel → PNG 图片导出（含红圈标注）")
    print(f"源文件: {EXCEL_PATH}")
    print("═" * 50)

    excel = Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False

    try:
        wb = excel.Workbooks.Open(EXCEL_PATH, ReadOnly=True)
        print(f"已打开工作簿，共 {wb.Sheets.Count} 个 sheet\n")

        total = 0
        for sheet_name, product_id in SHEET_PRODUCT.items():
            print(f"📋 {sheet_name} → {product_id}")
            n = export_sheet_images(excel, sheet_name, product_id)
            total += n

        print(f"\n✅ 完成！共导出 {total} 张合成图片")

    finally:
        wb.Close(SaveChanges=False)
        excel.Quit()


if __name__ == "__main__":
    main()

"""
DeepSeek-OCR 技术要求图识别脚本
用法: python ocr-tech-specs.py [--api-key KEY] [--product P100206001]
输出: knowledge-base/products/<id>_tech_specs.json

若无 API key，将输出提示说明如何配置。
"""
import os, sys, json, argparse
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge-base"
DRAWINGS_DIR = KB_DIR / "drawings"

# 每个产品的"技术要求图"文件名模式
# 通常是最初的图片1.png 或最大的那张图（含文字表格）
TECH_IMAGE_PATTERNS = ["图片1.png", "image1.png", "技术要求.png"]

def find_tech_images(product_id: str):
    """为指定产品找到技术要求图纸"""
    prod_dir = DRAWINGS_DIR / product_id
    if not prod_dir.exists():
        return []
    images = []
    for pattern in TECH_IMAGE_PATTERNS:
        img = prod_dir / pattern
        if img.exists():
            images.append(str(img))
    # 如果没有匹配到的模式，取所有 png 文件中最大的
    if not images:
        pngs = sorted(prod_dir.glob("*.png"), key=lambda f: f.stat().st_size, reverse=True)
        if pngs:
            images = [str(pngs[0])]
    return images


def ocr_with_deepseek(image_path: str, api_key: str):
    """调用 DeepSeek-OCR 提取技术要求表格"""
    from deepseek_ocr import DeepSeekOCR

    client = DeepSeekOCR(
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1/chat/completions"
    )

    prompt = (
        "<image>\n"
        "<|grounding|>"
        "This is a technical specification sheet for automotive thermal management components. "
        "Extract ALL text into a structured multi-dimensional table. "
        "For each row, capture: "
        "1. Item number / marker number (like ①, ②, or 1, 2) "
        "2. Inspection item name (检验项目) "
        "3. Standard/specification value with tolerances (标准/规格值及公差) "
        "4. Inspection tool (检验工具) "
        "5. Frequency (检验频率) "
        "6. Control method (控制方法) "
        "7. Reaction plan (反应计划) "
        "Output as a clean JSON array of objects with keys: "
        "marker, item, standard, tool, frequency, control, reaction. "
        "Preserve ALL tolerance values exactly as written (±, +, -)."
    )

    result = client.parse(image_path, mode="grounding", prompt=prompt)
    return result


def extract_table_json(raw_text: str) -> list:
    """将 OCR 结果解析为 JSON 表格"""
    import re

    # 尝试提取 JSON 块
    json_match = re.search(r'\[[\s\S]*\]', raw_text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # 否则返回原始文本，需人工审核
    print("[WARN] 未能自动解析为 JSON，返回原始 OCR 文本")
    return [{"raw_ocr": raw_text}]


def main():
    parser = argparse.ArgumentParser(description="DeepSeek-OCR 技术要求图识别")
    parser.add_argument("--api-key", help="DeepSeek API Key (或设置环境变量 DEEPSEEK_API_KEY)")
    parser.add_argument("--product", help="指定产品ID (如 P100206001)，默认全部", default=None)
    parser.add_argument("--dry-run", action="store_true", help="仅列出待处理图片，不实际OCR")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("=" * 60)
        print("⚠ DeepSeek-OCR API Key 未配置")
        print("")
        print("配置方式 (任选其一):")
        print("  1. 环境变量: set DEEPSEEK_API_KEY=sk-xxxx")
        print("  2. 命令行参数: python ocr-tech-specs.py --api-key sk-xxxx")
        print("")
        print("获取 API Key: https://siliconflow.cn (硅基流动)")
        print("=" * 60)
        print("")
        print("当前将列出所有待处理的'技术要求图':")
        args.dry_run = True

    # 获取所有产品
    products_dir = KB_DIR / "products"
    product_files = list(products_dir.glob("*.json"))

    if args.product:
        product_files = [f for f in product_files if args.product in f.name]

    print(f"📋 待处理产品: {len(product_files)} 个")
    print()

    for pf in sorted(product_files):
        product_id = pf.stem
        print(f"◆ {product_id}")

        tech_images = find_tech_images(product_id)
        if not tech_images:
            print(f"  ⚠ 未找到技术要求图（目录: {DRAWINGS_DIR / product_id}）")
            continue

        for img in tech_images:
            size_kb = Path(img).stat().st_size / 1024
            print(f"  📄 {Path(img).name} ({size_kb:.0f} KB)")

            if not args.dry_run and api_key:
                print(f"  ⏳ OCR 识别中...")
                try:
                    raw = ocr_with_deepseek(img, api_key)
                    table = extract_table_json(raw)

                    out_path = products_dir / f"{product_id}_tech_specs.json"
                    with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            "productId": product_id,
                            "sourceImage": Path(img).name,
                            "extractedAt": __import__('datetime').datetime.now().isoformat(),
                            "techSpecs": table
                        }, f, ensure_ascii=False, indent=2)
                    print(f"  ✅ 已保存: {out_path}")
                except Exception as e:
                    print(f"  ❌ OCR 失败: {e}")

    print()
    print("=" * 60)
    if args.dry_run and not api_key:
        print("配置 API Key 后重新运行以执行 OCR: python ocr-tech-specs.py --api-key YOUR_KEY")
    else:
        print("✅ 完成")


if __name__ == "__main__":
    main()

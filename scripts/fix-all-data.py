"""
Fix ALL product JSON data — three tasks:
  Task 2: Fix standard field — remove red-circle digit prefix,
          use _dimAnnotation.values as the true dimension.
  Task 1: Ensure every check-item (seq N) with a red-circle marker (N-1)
          has the correct drawing image mapped (only that image).
  Task 3: Read existing tech_specs JSON (from OCR) and insert tech-specs
          as a reusable table into the product detail JSON.

Run:  python scripts/fix-all-data.py
"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

KB = os.path.join(os.path.dirname(__file__), '..', 'knowledge-base')
PRODS = os.path.join(KB, 'products')
DRAWINGS = os.path.join(KB, 'drawings')

IDS = ['P100204006', 'P100204013', 'P100206001', 'P100206003', 'P100206004']


def fix_product(pid):
    fp = os.path.join(PRODS, f'{pid}.json')
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f'\n{"="*60}')
    print(f'Fixing: {pid} — {data["productName"]}')
    print(f'{"="*60}')

    # ── Task 2: Fix standard field ──
    for item in data['checkItems']:
        da = item.get('_dimAnnotation')
        if not da or not da.get('values') or not da['values'][0]:
            # Also handle seq 1 text items with leading "1." prefix
            if item['seq'] == 1 and item.get('category') == '外观':
                old = item['standard']
                # Remove leading "1." if present
                cleaned = old.strip()
                if cleaned.startswith('1.'):
                    cleaned = cleaned[2:].strip()
                    item['standard'] = cleaned
                    print(f'  seq {item["seq"]:>2}: removed "1." prefix → "{cleaned[:50]}..."')
            continue

        true_dim = da['values'][0].strip()
        old_standard = item['standard']

        if old_standard != true_dim:
            item['standard'] = true_dim
            print(f'  seq {item["seq"]:>2}: "{old_standard}" → "{true_dim}"')

    # ── Task 1: Image mapping (seq N → red circle N-1 → drawing image) ──
    # The JSON already has _imageRefs for most items.  Verify consistency:
    #   seq N should reference drawing that shows red circle (N-1)
    #   drawing filename = drawing_{N-1}.png
    #
    # For items that LACK images: try to create them from existing drawings
    # or from the Excel export.
    for item in data['checkItems']:
        da = item.get('_dimAnnotation')
        if not da or not da.get('markers') or not da['markers'][0]:
            continue

        marker_num = da['markers'][0]['num']  # red circle number
        expected_drawing = f'drawing_{marker_num:02d}.png'
        existing_refs = item.get('_imageRefs', [])

        # Check if the correct image is already there
        has_correct = any(r.get('num') == marker_num for r in existing_refs)

        # Check if the drawing file exists
        drawing_path = os.path.join(DRAWINGS, pid, expected_drawing)

        if not has_correct and os.path.exists(drawing_path):
            item['_imageRefs'] = [{
                'name': expected_drawing,
                'url': f'/drawings/{pid}/{expected_drawing}',
                'num': marker_num
            }]
            print(f'  seq {item["seq"]:>2}: ADDED image ref → {expected_drawing} (red circle {marker_num})')
        elif not has_correct:
            print(f'  seq {item["seq"]:>2}: ⚠ No image for red circle {marker_num} (expected {expected_drawing})')
        else:
            # Image exists and is correct
            pass

    # ── Task 3: Insert tech specs ──
    tech_fp = os.path.join(PRODS, f'{pid}_tech_specs.json')
    if os.path.exists(tech_fp):
        with open(tech_fp, 'r', encoding='utf-8') as f:
            tech = json.load(f)
        # Add techSpecs to product data
        if tech.get('techSpecs') and len(tech['techSpecs']) > 0:
            data['_techSpecs'] = tech['techSpecs']
            data['_techSpecsSource'] = tech.get('sourceImage', 'ocr')
            print(f'  ✅ Tech specs inserted ({len(tech["techSpecs"])} items)')

    # ── Rebuild _allImages ──
    seen = {}
    all_imgs = []
    for item in data['checkItems']:
        for ref in item.get('_imageRefs', []):
            key = ref['name']
            if key not in seen:
                seen[key] = True
                all_imgs.append(ref)
    # Add tech_req images
    dd = os.path.join(DRAWINGS, pid)
    if os.path.isdir(dd):
        for fname in sorted(os.listdir(dd)):
            if fname.startswith('tech_req') and fname not in seen:
                all_imgs.append({
                    'name': fname,
                    'url': f'/drawings/{pid}/{fname}',
                    'num': 99,
                    'isTechReq': True
                })
                seen[fname] = True
    data['_allImages'] = all_imgs

    # Save
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  💾 Saved: {fp} ({len(all_imgs)} total images)')

    return data


def main():
    print('='*60)
    print('WAT: Fix ALL product data — Tasks 1,2,3')
    print('='*60)

    for pid in IDS:
        fix_product(pid)

    print(f'\n{"="*60}')
    print('✅ All products fixed.')
    print(f'{"="*60}')


if __name__ == '__main__':
    main()

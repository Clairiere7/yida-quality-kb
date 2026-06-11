"""
Smart image-to-red-circle remapping v2.
Key insight: drawings can cover MULTIPLE red circles.
The LAST drawing typically covers all remaining red circles.
"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

KB = Path(os.path.dirname(__file__)).parent / 'knowledge-base'
PRODS = KB / 'products'
DWS = KB / 'drawings'

# ── DRAWING COVERAGE CONFIG ──────────────────────
# For each product, specify which drawing covers which red circles.
# Format: 'product_id': { red_circle_num: 'drawing_XX.png' }
# Once configured, run this script. Unconfigured red circles fall back to drawing_01.
OVERRIDES = {
    'P100204006': {1:'drawing_01.png', 2:'drawing_01.png', 3:'drawing_02.png', 4:'drawing_02.png'},
    'P100206001': {1:'drawing_01.png', 2:'drawing_01.png', 3:'drawing_01.png', 4:'drawing_01.png', 5:'drawing_01.png', 6:'drawing_02.png', 7:'drawing_02.png', 8:'drawing_02.png', 9:'drawing_02.png'},
    'P100204013': {1:'drawing_01.png', 2:'drawing_01.png', 3:'drawing_01.png', 4:'drawing_01.png', 5:'drawing_01.png', 6:'drawing_01.png', 7:'drawing_03.png', 8:'drawing_03.png', 9:'drawing_02.png'},
    'P100206003': {1:'drawing_03.png', 2:'drawing_03.png', 3:'drawing_04.png', 4:'drawing_04.png', 5:'drawing_04.png', 6:'drawing_01.png', 7:'drawing_03.png', 8:'drawing_06.png', 9:'drawing_02.png', 10:'drawing_05.png', 11:'drawing_05.png'},
    'P100206004': {1:'drawing_01.png', 6:'drawing_01.png', 7:'drawing_01.png', 8:'drawing_01.png', 2:'drawing_02.png', 3:'drawing_02.png', 4:'drawing_02.png', 9:'drawing_03.png', 5:'drawing_04.png', 10:'drawing_04.png', 11:'drawing_04.png'},
}

def map_red_circle_to_drawing(red_num, drawings, max_red):
    """Map a red circle number to the best drawing file.

    Priority:
    1. Manual OVERRIDE config
    2. Exact drawing_XX match (drawing_03 → red circle 3)
    3. Last drawing covers all higher numbers
    4. drawing_01 as ultimate fallback
    """
    if not drawings:
        return None

    sorted_dws = sorted(drawings, key=lambda d: int(d.stem.split('_')[-1]))
    dw_nums = [int(d.stem.split('_')[-1]) for d in sorted_dws]

    # 1. Manual override
    if pid in OVERRIDES and red_num in OVERRIDES[pid]:
        return OVERRIDES[pid][red_num]

    # 2. Exact match
    matching = [d for d in sorted_dws if int(d.stem.split('_')[-1]) == red_num]
    if matching:
        return matching[0].name

    # 3. Last drawing covers everything beyond it
    if red_num > dw_nums[-1]:
        return sorted_dws[-1].name

    # 4. Red circle is between drawings — use the next higher drawing
    #    (because the lower drawing only covers its exact match)
    for dn in dw_nums:
        if dn > red_num:
            return sorted_dws[dw_nums.index(dn)].name

    # 5. Ultimate fallback
    return sorted_dws[0].name


IDS = ['P100204006', 'P100204013', 'P100206001', 'P100206003', 'P100206004']
for pid in IDS:

    fp = PRODS / f'{pid}.json'
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dd = DWS / pid
    drawings = sorted([f for f in dd.glob('drawing_*.png')]) if dd.exists() else []

    print(f'\n{"="*60}')
    print(f'{pid} — {data["productName"]}')
    print(f'Drawings: {[d.name for d in drawings]}')
    print(f'{"="*60}')

    # Find max red circle number for this product
    max_red = 1
    for item in data['checkItems']:
        da = item.get('_dimAnnotation')
        if da and da.get('markers') and da['markers']:
            max_red = max(max_red, da['markers'][0]['num'])

    for item in data['checkItems']:
        da = item.get('_dimAnnotation')
        if not da or not da.get('markers') or not da['markers'][0]:
            continue

        red_num = da['markers'][0]['num']
        dim_value = da['values'][0] if da.get('values') else '?'

        best_name = map_red_circle_to_drawing(red_num, drawings, max_red)

        if best_name:
            item['_imageRefs'] = [{
                'name': best_name,
                'url': f'/drawings/{pid}/{best_name}',
                'num': red_num
            }]
            # Check if exact match or neighbor
            dw_num = int(best_name.split('_')[-1].split('.')[0])
            if dw_num == red_num:
                status = '✅ exact'
            else:
                status = f'📎 drawing_{dw_num:02d} covers 红圈{red_num}'
        else:
            status = '❌ no image'
            item['_imageRefs'] = []

        print(f'  seq {item["seq"]:>2}: 红圈{red_num} (dim={dim_value}) → {status}')

    # Rebuild _allImages
    all_imgs = []
    seen = set()
    for item in data['checkItems']:
        for ref in item.get('_imageRefs', []):
            if ref['name'] not in seen:
                seen.add(ref['name'])
                all_imgs.append(ref)
    for f in sorted(dd.glob('tech_req*.png')) if dd.exists() else []:
        if f.name not in seen:
            all_imgs.append({'name': f.name, 'url': f'/drawings/{pid}/{f.name}', 'num': 99, 'isTechReq': True})
            seen.add(f.name)

    data['_allImages'] = all_imgs

    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'  💾 {len(all_imgs)} images total')

print(f'\n{"="*60}')
print('Done. Logic: last drawing covers all remaining red circles.')
print(f'{"="*60}')

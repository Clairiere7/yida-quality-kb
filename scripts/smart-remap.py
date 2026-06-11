"""
Smart image-to-red-circle remapping.
Logic: Each product's check items have red circle markers (symbol + num).
       Each drawing file covers specific red circles.
       Rather than naive seq→drawing_0X, map by RED CIRCLE NUMBER.

Strategy:
- Large drawings (covering most rows) = "overview" drawings = show ALL red circles
- Small/medium drawings covering specific rows = "detail" for specific red circles
- Map each check item to the drawing that most specifically covers its red circle.
"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

KB = Path(os.path.dirname(__file__)).parent / 'knowledge-base'
PRODS = KB / 'products'
DWS = KB / 'drawings'

IDS = ['P100204006', 'P100206001', 'P100206003', 'P100206004']

for pid in IDS:
    # Load product
    fp = PRODS / f'{pid}.json'
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dd = DWS / pid
    # Only use named drawing files (not extracted_, not tech_req)
    drawings = sorted([f for f in dd.glob('drawing_*.png')]) if dd.exists() else []

    print(f'\n{"="*60}')
    print(f'{pid} — {data["productName"]}')
    print(f'Drawings: {[d.name for d in drawings]}')
    print(f'{"="*60}')

    # Look at each check item
    for item in data['checkItems']:
        seq = item['seq']
        da = item.get('_dimAnnotation')
        if not da or not da.get('markers'):
            continue

        marker = da['markers'][0]
        red_num = marker['num']  # red circle number
        dim_value = da['values'][0] if da.get('values') else '?'

        # Find drawing that best covers this red circle
        best_drawing = None
        for dw in drawings:
            # Extract drawing number from filename
            dw_num = int(dw.stem.split('_')[-1])
            if dw_num == red_num:
                best_drawing = dw
                break

        if best_drawing:
            status = '✅'
            item['_imageRefs'] = [{
                'name': best_drawing.name,
                'url': f'/drawings/{pid}/{best_drawing.name}',
                'num': red_num
            }]
        else:
            # Try fallback: use drawing_01 (overview drawing)
            overview = dd / 'drawing_01.png'
            if overview.exists():
                status = '⚠️ fallback→01'
                item['_imageRefs'] = [{
                    'name': 'drawing_01.png',
                    'url': f'/drawings/{pid}/drawing_01.png',
                    'num': red_num
                }]
            else:
                status = '❌ no image'
                item['_imageRefs'] = []

        print(f'  seq {seq:>2}: red-circle {red_num} (dim={dim_value}) → {status} {item["_imageRefs"][0]["name"] if item["_imageRefs"] else "NONE"}')

    # Delete extracted_*.png files
    for f in dd.glob('extracted_*.png'):
        f.unlink()
        print(f'  🗑️ Deleted: {f.name}')

    # Rebuild _allImages (only named drawings + tech_req)
    all_imgs = []
    seen = set()
    for item in data['checkItems']:
        for ref in item.get('_imageRefs', []):
            if ref['name'] not in seen:
                seen.add(ref['name'])
                all_imgs.append(ref)
    # Add tech_req
    for f in sorted(dd.glob('tech_req*.png')) if dd.exists() else []:
        name = f.name
        if name not in seen:
            all_imgs.append({
                'name': name,
                'url': f'/drawings/{pid}/{name}',
                'num': 99,
                'isTechReq': True
            })
            seen.add(name)
    data['_allImages'] = all_imgs

    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'  💾 Saved: {len(all_imgs)} images total ({len(drawings)} drawings + {len([i for i in all_imgs if i.get("isTechReq")])} tech_req)')

print(f'\n{"="*60}')
print('Done. extracted_*.png deleted. Drawings mapped by red circle number.')
print(f'{"="*60}')

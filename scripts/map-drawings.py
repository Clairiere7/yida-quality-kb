"""
Map extracted shape images to check items based on position.
Rules:
- Shape position row proximity to table rows determines which red circle it annotates.
- Big images (covering wide range) are likely full drawings showing all red circles.
- Small images are cropped annotations for specific red circles.
- Rename to drawing_{N:02d}.png where N = red circle number.
"""
import os, sys, json, shutil
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

KB = Path(os.path.dirname(__file__)).parent / 'knowledge-base'
DRAWINGS = KB / 'drawings'
PRODUCTS = KB / 'products'

# from unlock-and-extract (run manually), we know:
# P100206001: 4 shapes at rows 4-21
# P100206003: 8 shapes
# P100206004: 6 shapes
# P100204006: 3 shapes

# For each product, manually map shape positions to red circles
# based on the extracted shapes' positions and the check items' red circle markers
#
# Strategy: Look at existing drawing_01.png / drawing_02.png and compare
# with the newly extracted shapes.  Existing named files are already mapped.

IDS = ['P100204006', 'P100206001', 'P100206003', 'P100206004']

for pid in IDS:
    dd = DRAWINGS / pid
    if not dd.exists():
        continue

    # List all PNGs
    all_pngs = sorted(dd.glob('*.png'))
    drawing_pngs = [f for f in all_pngs if f.stem.startswith('drawing_')]
    extracted_pngs = [f for f in all_pngs if f.stem.startswith('extracted_')]
    other_pngs = [f for f in all_pngs if not f.stem.startswith(('drawing_', 'extracted_', 'tech_req'))]

    print(f"\n{pid}: {len(drawing_pngs)} named drawings, {len(extracted_pngs)} extracted, {len(other_pngs)} other")

    # For extracted images, try to figure out what red circle they show
    # Look at file size to identify the "big" drawing (full sheet vs cropped annotation)
    if extracted_pngs:
        sizes = [(f, f.stat().st_size) for f in extracted_pngs]
        sizes.sort(key=lambda x: x[1])
        for f, sz in sizes:
            kb = sz // 1024
            # Small images (< 50KB) are likely tiny annotations, skip
            # Medium images (50-500KB) are likely individual red circle drawings
            # Large images (>500KB) are likely full-sheet drawings
            tag = 'LARGE' if kb > 500 else ('small' if kb < 50 else 'medium')
            print(f'  {f.name}: {kb}KB ({tag})')

print('\nDone scanning. Check extracted_*.png files in each drawings folder.')

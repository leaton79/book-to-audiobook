import sys; import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_extract import get_lines
import pymupdf
d = pymupdf.open(sys.argv[1])
for p in map(int, sys.argv[2:]):
    print('=== page', p, d[p - 1].rect.height)
    for l in get_lines(d[p - 1])[:40]:
        print(round(l['x0']), round(l['y0']), round(l['x1']), l['size'], 'B' if l['bold'] else '-', 'I' if l['ital'] else '-', '|', l['t'][:75])

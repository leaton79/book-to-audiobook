import sys, collections, pymupdf
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_extract import get_lines
d = pymupdf.open(sys.argv[1]); f = float(sys.argv[2]) if len(sys.argv) > 2 else 1.35
c = collections.Counter()
for p in range(0, len(d), max(1, len(d) // 30)):
    for l in get_lines(d[p]): c[l['size']] += len(l['t'])
body = c.most_common(1)[0][0]
print('body', body, 'pages', len(d))
for i, pg in enumerate(d):
    ls = get_lines(pg)
    big = [l['t'].strip()[:50] for l in ls if l['size'] > body * f]
    if big: print(i + 1, '|', ' / '.join(big[:3]), '|| first:', ls[0]['t'].strip()[:40])

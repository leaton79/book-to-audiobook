import pymupdf, re
from textclean import clean
def from_toc(path, level, rule, last_page=None):
    d = pymupdf.open(path)
    toc = [(e[0], clean(e[1].replace('\n', ' ')), e[2]) for e in d.get_toc() if e[0] <= level]
    secs = []
    for i, (lv, t, p) in enumerate(toc):
        end = max(p, (toc[i + 1][2] - 1) if i + 1 < len(toc) else (last_page or len(d)))
        r = rule(t, i)
        if r: secs.append((p, end, r[0], r[1]))
    return secs
def chapnum(t):
    m = re.match(r'^(\d+)\.?\s+(.*)$', t)
    return (int(m.group(1)), m.group(2)) if m else (None, t)
def part_title(t):
    m = re.match(r'^PART\s+([IVX]+|\w+)[:.]?\s*(.*)$', t, re.I)
    nums = {'I':'One','II':'Two','III':'Three','IV':'Four','V':'Five','VI':'Six','VII':'Seven','VIII':'Eight'}
    if not m: return t
    n = nums.get(m.group(1).upper(), m.group(1).title()); rest = m.group(2).strip()
    return f'Part {n}: {rest}' if rest else f'Part {n}'

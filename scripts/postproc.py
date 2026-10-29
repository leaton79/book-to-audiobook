import re
from wordfreq import zipf_frequency as _zz
_HY = re.compile(r'\b([A-Za-z]{2,})- (?!(?:and|or|to|through|as|nor|but)\b)([a-z]{2,})\b')
def _fixhy(t):
    def f(m):
        a, b = m.group(1), m.group(2)
        j = (a + b).lower()
        zj, za, zb = _zz(j, 'en'), _zz(a.lower(), 'en'), _zz(b, 'en')
        if zj >= 3.0 or (zj >= 2.0 and zj >= min(za, zb) - 1.5): return a + b
        if za >= 2.5 and zb >= 2.5: return a + '-' + b
        return a + b
    return _HY.sub(f, t)

def _fix_note(t):
    return re.sub(r'^(\d+)\s*[.)]?\s+', r'\1. ', t)

def finalize(book):
    for b_ in book['blocks']:
        if b_['t'] in ('p', 'quote', 'cap'): b_['x'] = _fixhy(b_['x'])
    book['blocks'] = [b_ for b_ in book['blocks'] if not (b_['t'] in ('p', 'quote') and (sum(c.isalpha() for c in b_['x']) < 3 and not b_['x'].strip().endswith('?')))]
    for g in book.get('notes', []):
        g['items'] = [_fixhy(i) for i in g['items']]
    out = []
    for b in book['blocks']:
        x = b['x'].strip()
        if not x: continue
        if b['t'] == 'cap' and not x.startswith('Image description') and out and out[-1]['t'] == 'cap' and re.fullmatch(r'(Table|Figure|Fig\.|TABLE|FIGURE|Exhibit|Box|Chart|Map|Plate)\s*[\dA-Z.\-]+\.?', out[-1]['x']):
            out[-1]['x'] = out[-1]['x'].rstrip('.') + ': ' + x
            continue
        nb = {'t': b['t'], 'x': x}
        if 'pno' in b: nb['pno'] = b['pno']
        out.append(nb)
    for i, b in enumerate(out):
        if b['t'] == 'p' and i > 0 and out[i - 1]['t'] == 'h1':
            m = re.match(r'^([A-Z][A-Z’\']+)(\s+[a-z])', b['x'])
            if m and _zz(m.group(1).lower(), 'en') > 2.5:
                b['x'] = m.group(1)[0] + m.group(1)[1:].lower() + b['x'][len(m.group(1)):]
    for b in out:
        if re.match(r'^[—–-]\s*[a-z]', b['x']) and b['x'] == b['x'].lower() and len(b['x']) < 120:
            b['x'] = re.sub(r"\b([a-z])", lambda m: m.group(1).upper(), b['x'])
        if b['t'] == 'cap':
            b['x'] = re.sub(r'^(TABLE|FIGURE)', lambda m: m.group(1).title(), b['x'])
            m = re.match(r'^((?:Figure|Table)\s+[\dA-Z.]+\.?)\s+(.*)$', b['x'])
            if m:
                rest = m.group(2); letters = [c for c in rest if c.isalpha()]
                if letters and sum(c.isupper() for c in letters) / len(letters) > 0.8:
                    rest = rest.lower(); rest = rest[0].upper() + rest[1:]
                    rest = re.sub(r'\b(i)\b', 'I', rest)
                b['x'] = m.group(1).rstrip('.') + ': ' + rest
            if b['x'][-1] not in '.!?”)': b['x'] += '.'
    book['blocks'] = out
    merged = []
    for g in book.get('notes', []):
        if not g['items']: continue
        if merged and merged[-1]['h'] == g['h']: merged[-1]['items'] += g['items']
        else: merged.append(g)
    book['notes'] = merged
    for g in book['notes']:
        m = re.match(r'^0?(\d{1,2})\.?\s+(.+)$', g.get('h') or '')
        if m: g['h'] = f'Chapter {int(m.group(1))}: {m.group(2)}'
        g['items'] = [_fix_note(i) for i in g['items']]
    return book

import re, unicodedata

LIG = {'ﬀ': 'ff', 'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬃ': 'ffi', 'ﬄ': 'ffl', 'ﬅ': 'st', 'ﬆ': 'st'}
SPACES = '\u00a0\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u202f\u205f\u3000\t\r\n'

def clean(t):
    if not t: return ''
    t = re.sub(r'([ﬀ-ﬆ]) (?=[a-z])', r'\1', t)
    for k, v in LIG.items(): t = t.replace(k, v)
    for z in ('\u00ad', '\u200b', '\u200c', '\u200d', '\u2060', '\ufeff'): t = t.replace(z, '')  # soft hyphen, zero-width chars
    t = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', ' ', t)
    for s in SPACES: t = t.replace(s, ' ')
    t = re.sub(r'^[\ue000-\uf8ff]\s*', '• ', t)  # leading private-use glyph (Symbol/Wingdings bullet)
    t = re.sub(r'[\ue000-\uf8ff]', '', t)  # remaining private-use glyphs
    t = re.sub(r'(?<=[A-Za-z])�(?=[a-z])', 'ti', t)
    t = t.replace('�', '')
    t = t.replace('■', '•').replace('▪', '•')
    t = re.sub(r'•\s*•', '•', t)
    t = re.sub(r'(?<=\S)\s*•\s*', ' ', t) if t.count('•') > 1 and not t.startswith('•') else t
    t = re.sub(r'•(?=\S)', '• ', t)
    t = re.sub(r' {2,}', ' ', t).strip()
    t = re.sub(r' ([,.;:!?])(?=\s|$)', r'\1', t)
    t = re.sub(r'\( ', '(', t); t = re.sub(r' \)', ')', t)
    return t

SMALL = {'a','an','the','and','but','or','nor','for','so','yet','as','at','by','in','of','on','to','up','via','with','from','into','over','vs','vs.'}

def smart_title(t):
    """Title-case a heading only if it is ALL CAPS."""
    letters = [c for c in t if c.isalpha()]
    if not letters or not all(c.isupper() for c in letters): return t
    words = t.lower().split(' ')
    out = []
    for i, w in enumerate(words):
        core = w.strip('“”"‘’\'(:')
        if i > 0 and core in SMALL and not out[-1].endswith(':'):
            out.append(w)
        else:
            m = re.search(r'[a-z]', w)
            out.append(w[:m.start()] + w[m.start()].upper() + w[m.start()+1:] if m else w)
    s = ' '.join(out)
    for a in ['Ai', 'Lgbt', 'Dna', 'Tmi', 'Us', 'Gsu', 'Y2k', 'Nlp', 'Gpt']:
        s = re.sub(r'\b' + a + r'\b', a.upper(), s)
    return s

def fix_leadin_caps(t):
    """'THE VOICES OF PEOPLE WITH dyslexia' -> 'The voices of people with dyslexia'."""
    m = re.match(r'^((?:[“"‘]?[A-Z0-9][A-Z0-9’\'\-,.]*\s+){2,})(?=[a-z])', t)
    if not m: return t
    lead = m.group(1)
    if sum(c.isalpha() for c in lead) < 6: return t
    low = lead.lower()
    i = re.search(r'[a-z]', low).start()
    low = low[:i] + low[i].upper() + low[i+1:]
    low = re.sub(r'\bi\b', 'I', low)
    return low + t[len(lead):]

from wordfreq import zipf_frequency as _z
def join_hyphen(a, b):
    """a ends with 'word-', b starts with 'word...'. Return joined text."""
    m1 = re.search(r'([A-Za-zÀ-ɏ]+)-$', a); m2 = re.match(r'([a-zÀ-ɏ]+)', b)
    if not m1 or not m2: return a + b
    w1, w2 = m1.group(1), m2.group(1)
    j = (w1 + w2).lower()
    zj, z1, z2 = _z(j, 'en'), _z(w1.lower(), 'en'), _z(w2.lower(), 'en')
    if zj >= 3.0 or (zj >= 2.0 and zj >= min(z1, z2) - 1.5): return a[:-1] + b
    if z1 >= 3.0 and z2 >= 3.0: return a + b
    return a[:-1] + b

_WRE = re.compile(r"\b[A-Za-z]+\b")
def lig_repair(t):
    """Repair dropped 'Th' and 'ft' ligatures: 'Te'->'The', 'draf'->'draft'."""
    def fix(m):
        w = m.group(0)
        zw = _z(w.lower(), 'en')
        if zw >= 4.5: return w
        cands = []
        if w[0] == 'T' and len(w) > 1 and w[1].islower(): cands.append('Th' + w[1:])
        if w[0] == 't' and len(w) > 1: cands.append('th' + w[1:])
        for i, ch in enumerate(w):
            if ch == 'f' and (i + 1 == len(w) or w[i + 1] != 't'):
                cands.append(w[:i + 1] + 't' + w[i + 1:])
        best, bz = w, zw
        for c in cands:
            zc = _z(c.lower(), 'en')
            if zc >= 3.0 and zc - zw > 1.5 and zc > bz: best, bz = c, zc
        return best
    return _WRE.sub(fix, t)

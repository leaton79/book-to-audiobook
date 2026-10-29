"""Extract a PDF book into book JSON using a per-book page-range config (cfg_<slug>.py with SRC and CFG).
Sections: [(start, end, kind, title)], 1-based PDF pages inclusive; kind chap|part|cont|notes|back. See SKILL.md for config keys.
"""
import os, re, sys, json, statistics, importlib, collections
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.getcwd())
from textclean import clean, smart_title, fix_leadin_caps, join_hyphen, lig_repair
from postproc import finalize

DCWORDS = set('in it is if its into as at an and all after among also although any again about above across against along already always america american americans ask asked are art around area areas able academic access according actually age ago ahead aim air ancient another answer anyone anything apart approach arguably argue argued argument articles assessment attention author authors available away instead institutions ideas idea important imagine increasingly indeed initially instructors intelligence interest internet issue issues itself ironically inside'.split())
MARKRE = re.compile(r'^[\s\d*†‡§,\-–]+$')
REFHEADS = {'references', 'notes', 'works cited', 'bibliography', 'endnotes', 'suggested readings and links',
            'suggested readings', 'further reading', 'reference', 'works consulted', 'citations',
            'references and further reading', 'literature cited', 'bibliographic essay', 'select bibliography', 'selected bibliography', 'selected references'}
CAPRE = r'^(Figure|FIGURE|Fig\.|FIG\.|Table|TABLE|Plate|PLATE|Exhibit|EXHIBIT|Chart|Map)\s+[\dIVXA-Z]+[.\d]*\.?(\s+[A-Z“"‘(\d]|\s*$)'
BULLETS = r'[■□●○•▪▫◆◇►▶✓✔\-–\s]+'

def line_info(line):
    spans = [s for s in line['spans'] if s['text'].strip() != '' or s['text'] == ' ']
    big = [s for s in spans if s['text'].strip()]
    if not big: return None
    cnt = collections.Counter()
    for s in big: cnt[round(s['size'], 1)] += len(s['text'].strip())
    size = cnt.most_common(1)[0][0]
    ys = [s['origin'][1] for s in big if abs(s['size'] - size) < 0.6]
    baseline = statistics.median(ys) if ys else big[0]['origin'][1]
    out = []
    for s in spans:
        t = s['text']
        sup = (s['flags'] & 1) or (s['size'] < size * 0.82 and s['origin'][1] < baseline - size * 0.18)
        if sup and t.strip() and MARKRE.match(t.strip()): continue
        out.append(t)
    tot = sum(len(s['text']) for s in big)
    bold = sum(len(s['text']) for s in big if (s['flags'] & 16) or 'Bold' in s['font'] or 'bold' in s['font'] or 'Semibold' in s['font']) > 0.6 * tot
    ital = sum(len(s['text']) for s in big if (s['flags'] & 2) or 'Italic' in s['font'] or 'Ital' in s['font']) > 0.6 * tot
    fc = collections.Counter()
    for s_ in big: fc[s_['font']] += len(s_['text'])
    font = fc.most_common(1)[0][0]
    mono = any(k in font for k in ('Mono', 'Courier', 'SourceCode', 'Consol', 'Code'))
    x0, y0, x1, y1 = line['bbox']
    return {'font': font, 'mono': mono, 't': ''.join(out), 'size': size, 'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1, 'bold': bold, 'ital': ital}

MERGE = {'gap': 8, 'tol': 1.6}
def get_lines(page):
    d = page.get_text('dict', flags=pymupdf.TEXT_PRESERVE_LIGATURES | pymupdf.TEXT_PRESERVE_WHITESPACE)
    lines = []
    for b in d['blocks']:
        if b.get('type') != 0: continue
        for l in b['lines']:
            if abs(l['dir'][1]) > 0.1: continue
            li = line_info(l)
            if li and li['t'].strip(): lines.append(li)
    lines.sort(key=lambda l: l['y1'])
    rows, cur = [], []
    for l in lines:
        if cur and abs(l['y1'] - cur[-1]['y1']) > 2.5: rows.append(cur); cur = []
        cur.append(l)
    if cur: rows.append(cur)
    lines = [l for r in rows for l in sorted(r, key=lambda z: z['x0'])]
    merged = []
    for l in lines:
        if merged and abs(merged[-1]['y1'] - l['y1']) < 2.5 and l['x0'] >= merged[-1]['x1'] - 3 and l['x0'] - merged[-1]['x1'] < MERGE['gap'] and abs(l['size'] - merged[-1]['size']) < MERGE['tol']:
            m = merged[-1]; gap = l['x0'] - m['x1']
            m['t'] = m['t'].rstrip() + ' ' + l['t'].lstrip() if gap > 1.0 else m['t'] + l['t']
            m['x1'] = max(m['x1'], l['x1'])
        else:
            merged.append(dict(l))
    return merged

BODYFONT = [None]
def body_size(doc, pages):
    cnt = collections.Counter(); fc = collections.Counter()
    for p in pages:
        for l in get_lines(doc[p]):
            cnt[l['size']] += len(l['t']); fc[l['font']] += len(l['t'])
    BODYFONT[0] = fc.most_common(1)[0][0] if fc else None
    return cnt.most_common(1)[0][0]

def rows_to_text(rows):
    hdr = rows[0]; out = []
    has_hdr = sum(bool(c) for c in hdr) >= len(hdr) - 1
    for r in (rows[1:] if has_hdr else rows):
        r = [c.rstrip('.;: ') for c in r]
        if not any(r): continue
        if has_hdr and len(r) == len(hdr):
            parts = []
            for i, c in enumerate(r):
                if not c: continue
                h = hdr[i].rstrip('.:; ')
                parts.append(f'{h}: {c}' if h and i > 0 else c)
            if not hdr[0] and r[0]: s = parts[0] + ('. ' + '; '.join(parts[1:]) if len(parts) > 1 else '')
            elif hdr[0] and r[0]: s = f'{hdr[0].rstrip(".:; ")}: ' + parts[0] + ('. ' + '; '.join(parts[1:]) if len(parts) > 1 else '')
            else: s = '; '.join(parts)
        else:
            s = '; '.join(c for c in r if c)
        s = s.strip()
        if s and s[-1] not in '.!?”': s += '.'
        out.append(s)
    return out

def is_pagenum(t):
    return bool(re.fullmatch(r'[\divxlcIVXLC]{1,6}|\[?\s*\d{1,4}\s*\]?|[-–—]\s*\d+\s*[-–—]|page\s+\d+', t.strip(), re.I))

class Builder:
    def __init__(s, cfg, body):
        s.cfg, s.body = cfg, body
        s.blocks, s.notes, s.back = [], [], []
        s.para = None; s.ptype = 'p'
    def flush(s):
        if s.para:
            t = clean(s.para)
            if t:
                blk = {'t': s.ptype, 'x': t}
                if s.ptype == 'cap': blk['pno'] = getattr(s, 'start_pno', None)
                s.target.append(blk)
        s.para = None
    def add_line(s, text, ptype, newpara):
        text = text.rstrip()
        if newpara or s.para is None or ptype != s.ptype:
            s.flush(); s.para = text.strip(); s.ptype = ptype; s.start_pno = getattr(s, 'cur_pno', None); return
        if s.para.endswith('\u00ad'):  # soft hyphen at line end
            s.para = s.para.rstrip('\u00ad') + text.strip()
        elif re.search(r'[A-Za-z]-$', s.para) and re.match(r'^[a-z]', text.strip()):
            s.para = join_hyphen(s.para, text.strip())
        elif s.para.endswith(('—', '–', '/')):
            s.para += text.strip()
        else:
            s.para += ' ' + text.strip()

def extract(path, cfg):
    doc = pymupdf.open(path)
    MERGE['gap'] = cfg.get('merge_gap', 8); MERGE['tol'] = cfg.get('size_tol', 1.6)
    secs = cfg['sections']
    allpages = [p - 1 for (a, b, k, t) in secs if k in ('chap', 'part', 'cont') for p in range(a, b + 1)]
    sample = allpages[::max(1, len(allpages) // 40)] or [0]
    body = cfg.get('body') or body_size(doc, sample)
    bfont = BODYFONT[0]
    bfam = re.split(r'[-,]', bfont or 'x')[0][:6]
    head_min = cfg.get('head_min', 1.15)
    top, bottom = cfg.get('top', 0.075), cfg.get('bottom', 0.07)
    drop_re = [re.compile(r) for r in cfg.get('drop_re', [])]
    refheads = set(REFHEADS) | set(x.lower() for x in cfg.get('refheads', []))
    tocmap = {re.sub(r'\W+', '', clean(e[1]).lower()): clean(e[1]) for e in doc.get_toc()}
    fixhead = lambda h: tocmap.get(re.sub(r'\W+', '', h.lower()), h)
    B = Builder(cfg, body); B.target = B.blocks
    for (a, b, kind, title) in secs:
        B.flush()
        cont = kind == 'cont'
        if cont: kind = 'chap'
        if kind in ('chap', 'part'):
            if not cont: B.blocks.append({'t': 'h1', 'x': title})
            B.target = B.blocks
            grp = {'h': title, 'items': []}
        elif kind == 'notes':
            grp = None; sec = {'h': title or 'Notes', 'items': []}; B.target = sec['items']
        elif kind == 'back':
            sec = {'h': title, 'items': []}; B.target = sec['items']
        in_reftail = False; force_new = False; first_page = not cont
        nb = body
        if kind in ('notes', 'back'):
            c = collections.Counter()
            for pno in range(a - 1, min(b, a + 3)):
                for l in get_lines(doc[pno]): c[l['size']] += len(l['t'])
            nb = c.most_common(1)[0][0] if c else body
        prev_line = None; fn_items = []
        for pno in range(a - 1, b):
            page = doc[pno]; B.cur_pno = pno + 1
            H, W = page.rect.height, page.rect.width
            lines = get_lines(page)
            if cfg.get('top_caps'):
                lines = [l for l in lines if not (l['y0'] < H * cfg['top_caps'] and any(c.isalpha() for c in l['t']) and l['t'].upper() == l['t'] and len(l['t'].strip()) < 60)]
            if cfg.get('ocr'):
                for l in lines:
                    if l['size'] < body * 1.35: l['size'] = body
                lines = [l for l in lines if len(l['t'].strip()) > 1 or l['t'].strip().isalnum()]
            keep = []
            for i, l in enumerate(lines):
                t = l['t'].strip()
                if any(r.search(t) for r in drop_re): continue
                if l['y0'] < H * top and (len(t) < 90 or is_pagenum(t)) and not (first_page and l['size'] > body * head_min): continue
                if l['y0'] > H * (1 - bottom) and (is_pagenum(t) or len(t) < 60) and l['size'] <= body * 1.05: continue
                if is_pagenum(t) and (i == 0 or i == len(lines) - 1): continue
                if len(t) < 80 and (l['y0'] > H * 0.84 or l['y1'] < H * 0.13) and re.search(r'^\s*\[?\s*[\divxlc]{1,4}\s*\]?\s+\S|\S\s+\[?\s*[\divxlc]{1,4}\s*\]?\s*$', t) and (i <= 1 or i >= len(lines) - 2) and not re.search(r'[.,;:]\s*$', t): continue
                keep.append(l)
            lines = keep
            # drop caps
            for d_ in [l for l in lines if re.fullmatch(r'[A-Z“"]', l['t'].strip()) and l['size'] > body * 1.5]:
                cands = [l for l in lines if l is not d_ and l['x0'] >= d_['x0'] + 0.4 * (d_['x1'] - d_['x0']) and d_['y0'] - body <= l['y0'] <= d_['y1'] and abs(l['size'] - body) < 1.5]
                if cands:
                    tgt = min(cands, key=lambda l: l['y0'])
                    L = d_['t'].strip(); nxt = tgt['t'].lstrip()
                    w = re.match(r"[A-Za-z’']*", nxt).group(0)
                    tgt['t'] = (L + ' ' + nxt) if (L in ('A', 'I') and w and (L + w).lower() not in DCWORDS) else L + nxt
                    lines.remove(d_)
            # side pull-quotes and beside-the-text captions
            side = set()
            for l in lines:
                if abs(l['size'] - body) < 0.6: continue
                for m in lines:
                    if abs(m['size'] - body) < 0.6 and len(m['t'].strip()) >= 15 and abs((m['y0'] + m['y1']) / 2 - (l['y0'] + l['y1']) / 2) < body * 1.2 and (m['x0'] > l['x1'] + 4 or m['x1'] < l['x0'] - 4):
                        side.add(id(l)); break
            if side: lines = [l for l in lines if id(l) not in side]
            # vector tables -> sentences
            if cfg.get('tables', True) and kind in ('chap', 'part'):
                tregions = []
                try:
                    if len(page.get_drawings()) >= 3:
                        words = page.get_text('words')
                        def celltext(bb):
                            if not bb: return ''
                            r = pymupdf.Rect(bb)
                            ws = sorted([w for w in words if r.x0 - 1 <= (w[0] + w[2]) / 2 <= r.x1 + 1 and r.y0 - 1 <= (w[1] + w[3]) / 2 <= r.y1 + 1], key=lambda w: (w[5], w[6], w[7]))
                            txt = ''
                            for w in ws:
                                txt = join_hyphen(txt, w[4]) if txt.endswith('-') and re.match(r'^[a-z]', w[4]) else txt + (' ' if txt else '') + w[4]
                            return clean(txt)
                        for tb in page.find_tables().tables:
                            rows = [r for r in [[celltext(c) for c in r.cells] for r in tb.rows] if any(r)]
                            if len(rows) >= 2 and max(len(r) for r in rows) >= 2: tregions.append((pymupdf.Rect(tb.bbox), rows))
                except Exception:
                    tregions = []
                if tregions:
                    kept = []; done = set()
                    for l in lines:
                        cx, cy = (l['x0'] + l['x1']) / 2, (l['y0'] + l['y1']) / 2
                        hit = next((ti for ti, (r, _) in enumerate(tregions) if r.x0 - 2 <= cx <= r.x1 + 2 and r.y0 - 2 <= cy <= r.y1 + 2), None)
                        if hit is None: kept.append(l); continue
                        if hit not in done: done.add(hit); kept.append(dict(l, t='\x00TABLE', _rows=tregions[hit][1]))
                    lines = kept
            # figure regions
            if cfg.get('fig_filter', True) and kind in ('chap', 'part'):
                regions = []; pa = W * H
                for im in page.get_image_info():
                    r = pymupdf.Rect(im['bbox'])
                    if pa * 0.03 < r.get_area() < pa * 0.6: regions.append(r)
                try:
                    dr = page.get_drawings()
                    if len(dr) > 12:
                        for c in page.cluster_drawings(drawings=dr):
                            if c.get_area() >= pa * 0.03 and sum(1 for x in dr if pymupdf.Rect(x['rect']).intersects(c)) > cfg.get('fig_min_paths', 15): regions.append(c)
                except Exception:
                    pass
                if regions:
                    lines = [l for l in lines if l['t'].startswith('\x00TABLE') or re.match(r'^(Figure|FIGURE|Fig\.|Table|TABLE)\s', l['t'].strip()) or not any(r.x0 - 2 <= (l['x0'] + l['x1']) / 2 <= r.x1 + 2 and r.y0 - 2 <= (l['y0'] + l['y1']) / 2 <= r.y1 + 2 for r in regions)]
            if not lines: continue
            bl = [l for l in lines if abs(l['size'] - body) < 0.6]
            if bl:
                lm = collections.Counter(round(l['x0']) for l in bl).most_common(1)[0][0]; rm = max(l['x1'] for l in bl)
            else:
                lm, rm = min(l['x0'] for l in lines), max(l['x1'] for l in lines)
            # footnotes
            fnstart = len(lines)
            if cfg.get('fn', True) and kind in ('chap', 'part'):
                j = len(lines) - 1
                while j >= 0 and lines[j]['size'] < body - cfg.get('fn_delta', 0.7) and lines[j]['y0'] > H * 0.45 and not lines[j]['t'].startswith('\x00'): j -= 1
                if j < len(lines) - 1:
                    c0 = lines[j + 1]['t']
                    if re.match(r'^\s*[\d*†‡§]+\.?\s*[A-Za-z“"‘(]', c0) and len(c0.strip()) > 6: fnstart = j + 1
            main, foot = lines[:fnstart], lines[fnstart:]
            # margin glosses (keep margin figure captions)
            margin_caps = []
            if cfg.get('margin_filter', True) and bl:
                keep2 = []; capmode = None
                for l in main:
                    if (l['x1'] < lm - 8 or l['x0'] > rm + 8) and l['size'] < body:
                        ts_ = l['t'].strip()
                        if re.match(r'^(Figure|FIGURE|Table|TABLE)\s+\d', ts_): margin_caps.append(ts_); capmode = l; continue
                        if capmode is not None and 0 <= l['y0'] - capmode['y1'] < l['size'] * 1.2 and abs(l['x1'] - capmode['x1']) < 30:
                            margin_caps[-1] += ' ' + ts_; capmode = l; continue
                        capmode = None; continue
                    keep2.append(l)
                main = keep2
            # chapter start: drop title lines
            if first_page and kind in ('chap', 'part'):
                tnorm = re.sub(r'\W+', '', title.lower())
                def titleish(x):
                    tx = x['t'].strip()
                    if tx.startswith('\x00'): return False
                    n = re.sub(r'\W+', '', tx.lower())
                    return (tx.isupper() and len(tx) < 80) or bool(re.match(r'^(\S\s){3,}', tx)) or (len(n) > 3 and n in tnorm) or bool(re.fullmatch(r'(appendix|chapter|part)\s+\w+', tx, re.I))
                k = 0
                while k < len(main) and not main[k]['t'].startswith('\x00') and (main[k]['size'] > body * head_min or titleish(main[k]) or re.fullmatch(r'(chapter|part)?\s*[\dIVXivx]+\.?|chapter\s+\w+|part\s+\w+', main[k]['t'].strip(), re.I) or (cfg.get('drop_first_caps') and main[k]['t'].strip().isupper())):
                    k += 1
                main = main[k:]
            for l in main:
                t = l['t']; ts = t.strip()
                if not ts: continue
                l['_pno'] = pno
                if kind in ('chap', 'part') and re.match(CAPRE, ts) and (l['bold'] or l['ital'] or l['size'] < body - 0.3 or l['font'] != bfont):
                    B.add_line(t, 'cap', True); prev_line = l; continue
                samepage = prev_line is not None and prev_line.get('_pno') == pno
                gap_above = (not samepage) or l['y0'] - prev_line['y1'] > body * 0.3 or prev_line.get('_head')
                caps_head = ts.isupper() and len(ts) < 80 and sum(c.isalpha() for c in ts) > 3 and not re.search(r'[,;]$', ts) and l['size'] >= body - 3 and gap_above
                if ts == '\x00TABLE':
                    B.flush()
                    for row_text in rows_to_text(l['_rows']): B.target.append({'t': 'p', 'x': row_text})
                    prev_line = None; continue
                if re.fullmatch(BULLETS, ts):
                    cy = (l['y0'] + l['y1']) / 2
                    if samepage and prev_line['y0'] - 2 <= cy <= prev_line['y1'] + 2: continue
                    force_new = True; prev_line = l; continue
                if re.fullmatch(r'\(?(continued|cont\.?|cont’d)\)?', ts, re.I): prev_line = l; continue
                if l.get('mono') and cfg.get('drop_mono', True) and kind in ('chap', 'part'): prev_line = l; continue
                centered = abs((l['x0'] - lm) - (rm - l['x1'])) < body * 1.2 and l['x0'] > lm + body * 2.5
                otherfont = cfg.get('font_heads', True) and not l['font'].startswith(bfam) and not l['ital'] and abs(l['size'] - body) < 2
                soft_head = len(ts) < 90 and gap_above and sum(c.isalpha() for c in ts) > 3 and not re.search(r'[.,;]$', ts) and not re.match(r'^[—–\-]', ts) and (centered or otherfont) and kind in ('chap', 'part') and not l['ital']
                is_head = soft_head or (l['size'] >= body * head_min and len(ts) < 150) or (l['bold'] and len(ts) < 90 and l['size'] >= body - 3 and not re.search(r'[,;]$', ts) and not re.match(r'^\d{1,3}[.\s]', ts) and gap_above) or caps_head
                if kind in ('notes', 'back'):
                    if is_head and clean(ts).lower() == (title or '').lower(): prev_line = l; continue
                    cen = l['x0'] > lm + 2.5 * l['size'] and l['x1'] < rm - 2.5 * l['size'] and len(ts) < 110
                    nhead = (l['size'] >= nb + 0.5 and len(ts) < 120) or (l['bold'] and len(ts) < 100 and not re.match(r'^\d{1,3}\.?\s', ts)) or caps_head or (cen and not re.match(r'^\d{1,3}\.\s', ts) and kind == 'notes')
                    if cfg.get('notes_head_re'):
                        if re.match(cfg['notes_head_re'], clean(ts)):
                            B.flush(); B.target.append({'t': 'h2', 'x': clean(ts)}); prev_line = l; continue
                        nhead = False
                    if nhead and (not re.match(r'^\d', ts) or (re.match(r'^\d{1,2}\.?\s+[A-Z][a-z]+(\s+[A-Za-z]+){0,12}$', ts) and l['size'] >= nb + 0.4)):
                        B.flush(); B.target.append({'t': 'h2', 'x': smart_title(clean(ts))}); prev_line = l; continue
                    if kind == 'notes': newp = bool(re.match(r'^\s*\d{1,3}[\.\s]', ts))
                    else: newp = l['x0'] <= lm + 1.5 if cfg.get('back_hanging', True) else prev_line is None
                    B.add_line(t, 'p', newp); prev_line = l; continue
                if is_head:
                    ht = fixhead(smart_title(clean(ts)))
                    if in_reftail and l['size'] >= body * head_min and ht.lower().strip(': ') not in refheads and not cfg.get('reftail_sticky'):
                        in_reftail = False; B.flush(); B.target = B.blocks
                    if ht.lower().strip(': ') in refheads:
                        in_reftail = True; B.flush(); B.target = grp['items']; prev_line = l; continue
                    B.flush()
                    if not in_reftail:
                        if B.target and B.target[-1]['t'] in ('h2', 'h3') and prev_line is not None and prev_line.get('_head') and l['y0'] - prev_line['y1'] < body * 1.2:
                            B.target[-1]['x'] += ' ' + ht
                        else:
                            B.target.append({'t': 'h2' if l['size'] >= body * head_min else 'h3', 'x': ht})
                    l['_head'] = True; prev_line = l; continue
                small = l['size'] < body - 0.6
                ptype = 'quote' if (small or (l['x0'] > lm + body * 2.2 and l['x1'] < rm - body * 1.5)) and not in_reftail else 'p'
                if in_reftail:
                    newp = bool(re.match(r'^\s*(\d{1,3}[\.\s]|[A-Z][\w’\'\-]+,)', ts)) or (l['x0'] <= lm + 1.5 and prev_line is not None and prev_line['x1'] < rm - body * 2)
                    B.add_line(t, 'p', newp); prev_line = l; continue
                if re.match(CAPRE, ts) and (l['size'] < body - 0.3 or l['ital'] or l['bold'] or not samepage or l['y0'] - prev_line['y1'] > body * 0.5):
                    B.add_line(t, 'cap', True); prev_line = l; continue
                if B.ptype == 'cap' and B.para and samepage and l['size'] < body - 0.3 and l['y0'] - prev_line['y1'] < body * 0.6:
                    B.add_line(t, 'cap', False); prev_line = l; continue
                indent = l['x0'] - lm
                gap = (l['y0'] - prev_line['y1']) if (samepage and prev_line['y1'] < l['y0'] + 1) else 0
                prev_short = prev_line is not None and prev_line['x1'] < rm - body * 2.0 and re.search(r'[.!?:”"’)]\s*$', prev_line['t'].strip())
                if samepage and prev_line['x0'] > lm + body * 0.6 and not prev_short and abs(l['x0'] - prev_line['x0']) < body * 0.6 and (l['y0'] - prev_line['y1']) < body * 0.5:
                    indent = 0
                newp = (body * 0.6 < indent < body * 4 and ptype == 'p') or gap > body * cfg.get('gap', 0.9) or prev_short or prev_line is None
                if ptype == 'quote' and B.ptype == 'quote' and gap < body * 0.9 and not prev_short: newp = False
                if ptype == 'quote' and not small and B.ptype == 'p' and B.para and samepage and gap < body * 0.5 and not prev_short and not re.search(r'[.!?:”"]$', B.para.strip()):
                    ptype = 'p'; newp = False
                if force_new:
                    newp = True; force_new = False
                    if not re.match(r'^[•\-–]', ts): t = '• ' + t.lstrip()
                B.add_line(t, ptype, newp)
                prev_line = l
            for mc in margin_caps:
                B.flush(); B.target.append({'t': 'cap', 'x': clean(mc), 'pno': pno + 1})
            for l in foot:
                ts = l['t'].strip()
                if re.match(r'^\s*[\d*†‡§]+\s*\S', ts) and not (fn_items and fn_items[-1].endswith('-')):
                    fn_items.append(ts)
                elif fn_items:
                    if fn_items[-1].endswith('\u00ad'): fn_items[-1] = fn_items[-1].rstrip('\u00ad') + ts
                    elif re.search(r'[A-Za-z]-$', fn_items[-1]) and re.match(r'^[a-z]', ts): fn_items[-1] = join_hyphen(fn_items[-1], ts)
                    else: fn_items[-1] += ' ' + ts
                else:
                    fn_items.append(ts)
            first_page = False
        B.flush()
        if kind in ('chap', 'part'):
            items = [clean(x['x']) if isinstance(x, dict) else clean(x) for x in grp['items']]
            grp['items'] = [clean(f) for f in fn_items] + [x for x in items if x]
            if grp['items']: B.notes.append(grp)
        elif kind == 'notes':
            for it in sec['items']:
                if isinstance(it, dict) and it['t'] == 'h2':
                    if B.notes and not B.notes[-1]['items'] and B.notes[-1]['h']: B.notes[-1]['h'] += ' ' + it['x']; continue
                    B.notes.append({'h': it['x'], 'items': []})
                else:
                    if not B.notes: B.notes.append({'h': '', 'items': []})
                    B.notes[-1]['items'].append(it['x'] if isinstance(it, dict) else it)
        elif kind == 'back':
            B.back.append(sec)
        B.target = B.blocks
    book = {'title': cfg['title'], 'author': cfg['author'], 'blocks': B.blocks, 'notes': B.notes, 'back': B.back, 'body': body}
    return post(book, cfg)

NOTE_INLINE = re.compile(r'(?:(?<=[a-z][.,;:!?])|(?<=[a-z][.,;:!?][’”"\)])|(?<=[a-z][’”"\)])|(?<=[a-z]{3}))(\d{1,3})(?=[\s,;:]|$)')

def post(book, cfg):
    for b in book['blocks']:
        x = b['x']
        if b['t'] in ('p', 'quote') and cfg.get('inline_marks', True): x = NOTE_INLINE.sub('', x)
        if b['t'] == 'p': x = fix_leadin_caps(x)
        if cfg.get('lig_repair'): x = lig_repair(x)
        x = clean(x)
        for a_, b_ in cfg.get('replace', []): x = x.replace(a_, b_)
        for a_, b_ in cfg.get('regex_replace', []): x = re.sub(a_, b_, x)
        b['x'] = x
    if cfg.get('lig_repair'):
        for g in book['notes']: g['items'] = [lig_repair(i) for i in g['items']]
        for sct in book['back']: sct['items'] = [dict(i, x=lig_repair(i['x'])) if isinstance(i, dict) else lig_repair(i) for i in sct['items']]
    # merge paragraphs split across pages (looking past captions)
    out = []
    for b in book['blocks']:
        k = len(out) - 1
        while k >= 0 and out[k]['t'] == 'cap' and b['t'] == 'p': k -= 1
        if b['t'] == 'p' and k >= 0 and out[k]['t'] == 'p' and not re.search(r'[.!?”"’)\]]$', out[k]['x']) and re.match(r'^[a-z(]', b['x']):
            out[k]['x'] = join_hyphen(out[k]['x'], b['x']) if re.search(r'[A-Za-z]-$', out[k]['x']) else out[k]['x'] + ' ' + b['x']
            continue
        out.append(b)
    if cfg.get('ocr'):
        from wordfreq import zipf_frequency as _zf
        def ok(t):
            ns = re.sub(r'\s', '', t)
            if sum(c.isalnum() for c in ns) < 4: return False
            if sum(c.isalpha() for c in ns) / max(1, len(ns)) < 0.75: return False
            toks = [w for w in re.findall(r'[A-Za-z]+', t) if len(w) >= 3]
            if not toks: return len(t) > 3 and t[-1] in '.:!?,'
            return sum(1 for w in toks if _zf(w.lower(), 'en') > 2.0) / len(toks) >= 0.7
        out = [b for b in out if b['t'] not in ('p', 'quote') or len(b['x']) > 250 or ok(b['x'])]
    out = [b for b in out if not (b['t'] in ('p', 'quote') and len(b['x']) < 60 and re.fullmatch(r'[\d\s.,%()\[\]–\-/:;+=$*∗·•#~]+', b['x']))]
    cur_h1 = ''; out3 = []
    for b in out:
        if b['t'] == 'h1': cur_h1 = re.sub(r'\W+', '', b['x'].lower())
        elif b['t'] in ('h2', 'h3'):
            n = re.sub(r'\W+', '', re.sub(r'\s*\d{1,2}$', '', b['x']).lower())
            if len(n) > 4 and n in cur_h1: continue
        out3.append(b)
    out = out3
    fd = cfg.get('figdesc', {})
    if fd:
        out2 = []
        for b in out:
            out2.append(b)
            if b['t'] == 'cap':
                for k, v in fd.items():
                    if b['x'].lower().startswith(k.lower()) and (len(b['x']) == len(k) or not b['x'][len(k)].isdigit()):
                        out2.append({'t': 'cap', 'x': 'Image description: ' + v}); break
        out = out2
    book['blocks'] = out
    return finalize(book)

def load_config(arg):
    """Accept a path to a config .py file, or a slug that resolves to cfg_<slug>.py."""
    import importlib, importlib.util
    if arg.endswith('.py') and os.path.exists(arg):
        spec = importlib.util.spec_from_file_location('book_cfg', arg)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
    return importlib.import_module('cfg_' + arg)

if __name__ == '__main__':
    mod = load_config(sys.argv[1])
    out = extract(mod.SRC, mod.CFG)
    json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
    print('body', out['body'], len(out['blocks']), 'blocks', sum(len(g['items']) for g in out['notes']), 'notes', [(s['h'], len(s['items'])) for s in out['back']])

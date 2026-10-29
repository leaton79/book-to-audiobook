"""Extract an EPUB into book JSON using a per-book config (cfg_<slug>.py with SRC and CFG).
CFG = {'title','author', 'files': [(spine_file_suffix, role, title)], 'cls': {css_class: role}, 'imgdesc': {img_basename: text}}
File roles: chap|part|notes|back|skip. Unlisted files are skipped. Class roles: drop|h2|h3|p|quote|cap|note|nh|skip.
"""
import os, re, json, sys, importlib, warnings
warnings.filterwarnings('ignore')
from ebooklib import epub
from bs4 import BeautifulSoup, Tag
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.getcwd())
from textclean import clean, smart_title, fix_leadin_caps

LEAF = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'figcaption', 'dt', 'dd', 'caption'}
NOTE_CONTAINERS = {'endnotes', 'rearnotes', 'footnotes', 'footnote', 'endnote', 'rearnote'}
MARK = re.compile(r'^\s*[\[\(]?[\d*†‡§]+[a-z]?[\]\)]?\s*$')

def text_of(el):
    for br in el.find_all('br'): br.replace_with(' ')
    return clean(el.get_text(''))

def strip_noterefs(el):
    for a in el.find_all('a'):
        t = a.get_text('')
        if (a.get('href') or a.get('role') == 'doc-noteref' or a.get('epub:type') == 'noteref') and MARK.match(t):
            a.decompose()
    for s in el.find_all('sup'):
        if MARK.match(s.get_text('')) or not s.get_text('').strip(): s.decompose()

def in_note_container(el):
    for p in el.parents:
        if not isinstance(p, Tag): continue
        et = (p.get('epub:type') or '') + ' ' + (p.get('role') or '')
        if any(k in et.replace('doc-', '') for k in NOTE_CONTAINERS): return True
    return False

def table_to_blocks(tbl):
    rows = []
    for tr in tbl.find_all('tr'):
        cells = [text_of(c) for c in tr.find_all(['td', 'th'])]
        if any(cells): rows.append(cells)
    if not rows: return []
    if len(rows) == 1 or max(len(r) for r in rows) == 1:
        return [{'t': 'p', 'x': ' '.join(c for r in rows for c in r if c)}]
    out = []
    hdr = rows[0]
    has_hdr = bool(tbl.find('th')) or (len(rows) > 2 and sum(bool(c) for c in hdr) >= len(hdr) - 1)
    for r in (rows[1:] if has_hdr else rows):
        r = [c.rstrip('.;: ') for c in r]
        if not any(r): continue
        if has_hdr and len(r) == len(hdr):
            parts = []
            for i, c in enumerate(r):
                if not c: continue
                h = hdr[i].rstrip('.:; ')
                if i == 0 and not h: parts.append(c)
                else: parts.append(f'{h}: {c}' if h else c)
            s = parts[0] + ('. ' + '; '.join(parts[1:]) if len(parts) > 1 else '') if not hdr[0] and r[0] else '; '.join(parts)
        else:
            s = '; '.join(c for c in r if c)
        s = s.strip()
        if s and s[-1] not in '.!?”': s += '.'
        out.append({'t': 'p', 'x': s})
    return out

def leaf_blocks(body):
    for el in body.descendants:
        if not isinstance(el, Tag): continue
        if el.name == 'table':
            if not el.find_parent('table'): yield el
            continue
        if el.find_parent('table'): continue
        if el.name in LEAF or (el.name in ('div', 'aside') and el.find(LEAF) is None and el.find('table') is None and el.get_text(strip=True)):
            if el.find(lambda t: isinstance(t, Tag) and t.name in LEAF) is None:
                yield el

def role_for(el, cls_map):
    for c in el.get('class') or []:
        if c in cls_map: return cls_map[c]
    for p in el.parents:
        if not isinstance(p, Tag): continue
        for c in p.get('class') or []:
            if c in cls_map and cls_map[c] in ('quote', 'skip', 'note', 'cap'): return cls_map[c]
    if el.name == 'h1': return 'drop'
    if el.name == 'h2': return 'h2'
    if el.name in ('h3', 'h4', 'h5', 'h6'): return 'h3'
    if el.name in ('figcaption', 'caption'): return 'cap'
    if el.find_parent('blockquote'): return 'quote'
    return 'p'

def extract(path, cfg):
    book = epub.read_epub(path)
    blocks, notes, back = [], [], []
    cls_map = cfg.get('cls', {})
    for idref, _ in book.spine:
        it = book.get_item_with_id(idref)
        name = it.get_name()
        spec = next((f for f in cfg['files'] if name.endswith(f[0]) or name.split('/')[-1] == f[0]), None)
        if not spec or spec[1] == 'skip': continue
        _, frole, ftitle = spec
        body = BeautifulSoup(it.get_content(), 'lxml').body
        if frole in ('chap', 'part'):
            blocks.append({'t': 'h1', 'x': ftitle})
            grp = {'h': ftitle, 'items': []}
            for el in list(leaf_blocks(body)):
                if el.name == 'table':
                    if role_for(el, cls_map) != 'skip': blocks.extend(table_to_blocks(el))
                    continue
                for im in el.find_all('img'):
                    k = (im.get('src') or '').split('/')[-1]
                    if k in cfg.get('imgdesc', {}):
                        blocks.append({'t': 'cap', 'x': 'Image description: ' + cfg['imgdesc'][k]})
                r = role_for(el, cls_map)
                if in_note_container(el) or r == 'note':
                    t = text_of(el)
                    if t and t.lower() not in ('notes', 'note'): grp['items'].append(t)
                    continue
                if r in ('drop', 'skip', 'nh'): continue
                strip_noterefs(el)
                t = text_of(el)
                if not t or re.fullmatch(r'[*\s•·]+', t): continue
                if r in ('h2', 'h3'):
                    t = smart_title(t)
                    if t.lower().strip(': ') in ('notes', 'references', 'note', 'works cited', 'endnotes'): continue
                else:
                    t = fix_leadin_caps(t)
                blocks.append({'t': r, 'x': t})
            if grp['items']: notes.append(grp)
        elif frole == 'notes':
            cur = None
            for el in leaf_blocks(body):
                if el.name == 'table': continue
                r = role_for(el, cls_map); t = text_of(el)
                if not t: continue
                if r in ('nh', 'h2', 'h3'):
                    cur = {'h': cfg.get('notes_map', {}).get(t, smart_title(t)), 'items': []}; notes.append(cur); continue
                if r in ('drop', 'skip'): continue
                if cur is None: cur = {'h': '', 'items': []}; notes.append(cur)
                cur['items'].append(t)
        elif frole == 'back':
            sec = {'h': ftitle, 'items': []}
            for el in leaf_blocks(body):
                if el.name == 'table': continue
                r = role_for(el, cls_map)
                if r in ('drop', 'skip'): continue
                t = text_of(el)
                if not t: continue
                sec['items'].append({'t': 'h2', 'x': smart_title(t)} if r in ('h2', 'h3', 'nh') else t)
            back.append(sec)
    from postproc import finalize
    return finalize({'title': cfg['title'], 'author': cfg['author'], 'blocks': blocks, 'notes': notes, 'back': back})

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
    print(len(out['blocks']), 'blocks', sum(len(g['items']) for g in out['notes']), 'notes', [(s['h'], len(s['items'])) for s in out['back']])

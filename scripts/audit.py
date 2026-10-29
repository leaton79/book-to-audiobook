"""Compare output length to source length to catch lost text (PDF sources).
usage: python audit.py config.py book.json [config2.py book2.json ...]
Body plus notes should land near 0.9 to 1.2 of the source. Lower means text was lost."""
import json, sys, os, collections, re, pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_extract import load_config
args = sys.argv[1:]
for cfgp, bookp in zip(args[::2], args[1::2]):
    mod = load_config(cfgp)
    b = json.load(open(bookp))
    doc = pymupdf.open(mod.SRC)
    src = sum(len(re.sub(r'\s', '', doc[p - 1].get_text())) for a, z, k, t in mod.CFG['sections'] if k in ('chap', 'part', 'cont') for p in range(a, z + 1))
    out = sum(len(re.sub(r'\s', '', x['x'])) for x in b['blocks'])
    notes = sum(len(re.sub(r'\s', '', i)) for g in b['notes'] for i in g['items'])
    c = collections.Counter(x['x'] for x in b['blocks'] if len(x['x']) < 80)
    rep = [(k, v) for k, v in c.most_common(4) if v > 2]
    marks = sum(len(re.findall(r'[a-z][.,;:\u201d"\u2019)]\d{1,3}(?=\s)', x['x'])) for x in b['blocks'])
    name = os.path.basename(bookp)
    print(f"{name:30s} body+notes/src={(out + notes) / max(1, src):.2f} body/src={out / max(1, src):.2f} blocks={len(b['blocks'])} notegrp={len(b['notes'])} stray_marks={marks} repeats={rep}")

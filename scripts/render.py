"""Render a cleaned book (JSON) into an audio-friendly PDF.
Book JSON: {title, author, blocks:[{t, x}], notes:[{h, items:[str]}], back:[{h, items:[str|{t,x}]}]}
Block types: h1, h2, h3, p, quote, cap. No running heads, no page numbers, no hyphenation. Bookmarks for h1.
"""
import json, sys
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

import os
# Font lookup: set BTA_FONT_DIR to a folder holding DejaVuSerif*.ttf, or rely on common install locations.
# Falls back to ReportLab's built-in Times (fine for English; limited for other scripts).
_CANDS = [os.environ.get('BTA_FONT_DIR', ''), '/usr/share/fonts/truetype/dejavu/', '/usr/share/fonts/dejavu/',
          '/Library/Fonts/', os.path.expanduser('~/Library/Fonts/'), 'C:/Windows/Fonts/']
FD = next((d for d in _CANDS if d and os.path.exists(os.path.join(d, 'DejaVuSerif.ttf'))), None)
if FD:
    pdfmetrics.registerFont(TTFont('Serif', os.path.join(FD, 'DejaVuSerif.ttf')))
    pdfmetrics.registerFont(TTFont('Serif-Bold', os.path.join(FD, 'DejaVuSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('Serif-Italic', os.path.join(FD, 'DejaVuSerif-Italic.ttf')))
    registerFontFamily('Serif', normal='Serif', bold='Serif-Bold', italic='Serif-Italic', boldItalic='Serif-Bold')
    F, FB, FI = 'Serif', 'Serif-Bold', 'Serif-Italic'
else:
    F, FB, FI = 'Times-Roman', 'Times-Bold', 'Times-Italic'

S = {
    'title': ParagraphStyle('title', fontName=FB, fontSize=24, leading=30, spaceAfter=18),
    'author': ParagraphStyle('author', fontName=F, fontSize=16, leading=22, spaceAfter=12),
    'h1': ParagraphStyle('h1', fontName=FB, fontSize=18, leading=24, spaceAfter=16),
    'h2': ParagraphStyle('h2', fontName=FB, fontSize=14, leading=19, spaceBefore=14, spaceAfter=8),
    'h3': ParagraphStyle('h3', fontName=FB, fontSize=12, leading=16, spaceBefore=10, spaceAfter=6),
    'p': ParagraphStyle('p', fontName=F, fontSize=12, leading=17, spaceAfter=9),
    'quote': ParagraphStyle('quote', fontName=F, fontSize=12, leading=17, spaceAfter=9, leftIndent=30, rightIndent=20),
    'cap': ParagraphStyle('cap', fontName=FI, fontSize=11, leading=15, spaceAfter=9, leftIndent=15),
    'note': ParagraphStyle('note', fontName=F, fontSize=11, leading=15, spaceAfter=6),
}

class Bookmark(Flowable):
    def __init__(self, title, key, level=0):
        super().__init__(); self.title, self.key, self.level = title, key, level
    def wrap(self, w, h): return (0, 0)
    def draw(self):
        self.canv.bookmarkPage(self.key)
        self.canv.addOutlineEntry(self.title, self.key, level=self.level, closed=True)

def para(text, style):
    return Paragraph(escape(text), S[style])

def build(book, out):
    doc = SimpleDocTemplate(out, pagesize=letter, leftMargin=1*inch, rightMargin=1*inch,
                            topMargin=0.9*inch, bottomMargin=0.9*inch,
                            title=book['title'], author=book.get('author', ''))
    fl = [para(book['title'], 'title')]
    if book.get('author'): fl.append(para(book['author'], 'author'))
    n = 0
    def h1(text):
        nonlocal n
        n += 1
        fl.append(PageBreak()); fl.append(Bookmark(text, f'b{n}')); fl.append(para(text, 'h1'))
    for b in book['blocks']:
        t, x = b['t'], b['x'].strip()
        if not x: continue
        if t == 'h1': h1(x)
        else: fl.append(para(x, t))
    if book.get('notes'):
        h1('Notes')
        for grp in book['notes']:
            if grp.get('h'): fl.append(para(grp['h'], 'h2'))
            for it in grp['items']: fl.append(para(it, 'note'))
    for sec in book.get('back', []) or []:
        h1(sec['h'])
        for it in sec['items']:
            fl.append(para(it['x'], it['t']) if isinstance(it, dict) else para(it, 'note'))
    doc.build(fl)

if __name__ == '__main__':
    build(json.load(open(sys.argv[1])), sys.argv[2])

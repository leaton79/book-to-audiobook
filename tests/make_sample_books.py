"""Generate small synthetic test books (original text, no copyrighted content).
usage: python tests/make_sample_books.py outdir
Creates sample.pdf (born-digital, running heads, page numbers, superscript note markers,
line-end hyphenation, page-bottom footnotes, a ruled table) and sample.epub."""
import os, sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUT = sys.argv[1] if len(sys.argv) > 1 else 'sample_books'
os.makedirs(OUT, exist_ok=True)
W, H = letter
LM, RM, BODY = 72, W - 72, 11

CH = [
    ('Chapter 1', 'Listening as Reading', [
        ["Readers who listen to books report that the experience feels different from silent reading, yet the evidence on compre-",
         "hension suggests the gap is smaller than many assume.^1 A listener still follows argument, tracks characters,",
         "and builds a mental model of the text. What changes is pacing, because the voice sets the tempo rather than the eye."],
        ["Running heads, page numbers, and note markers interrupt that tempo. A synthetic voice reads each one aloud,",
         "so a clean source matters more for listening than for print.^2 The well-known work of preparation is subtraction."]],
     ["1. Comprehension studies vary in design and population, so treat this as a general claim.",
      "2. Most text-to-speech readers announce digits and bracketed numbers verbatim."]),
    ('Chapter 2', 'What the Ear Needs', [
        ["The ear needs announced structure. A chapter heading read aloud orients the listener the way a title page orients",
         "the eye.^3 Tables need to become sentences, and figures need short descriptions when they carry information."],
        ["Notes belong at the end, grouped by chapter, so a curious listener can find them without breaking the main line of",
         "argument. That arrangement keeps the narrative continuous and the scholarly apparatus intact."]],
     ["3. Screen-reader conventions offer a useful model for spoken structure."]),
]

c = canvas.Canvas(os.path.join(OUT, 'sample.pdf'), pagesize=letter)
c.setTitle('Sample Book'); c.setAuthor('Test Author')
page = 1
def head_foot(title):
    c.setFont('Times-Italic', 9); c.drawString(LM, H - 40, title.upper())
    c.setFont('Times-Roman', 9); c.drawCentredString(W / 2, 36, str(page))
def draw_line(x, y, text):
    # '^n' renders as a superscript note marker
    parts = text.split('^')
    c.setFont('Times-Roman', BODY); c.drawString(x, y, parts[0]); x += c.stringWidth(parts[0], 'Times-Roman', BODY)
    for p in parts[1:]:
        num = ''.join(ch for ch in p if ch.isdigit()); rest = p[len(num):]
        c.setFont('Times-Roman', 7); c.drawString(x, y + 4, num); x += c.stringWidth(num, 'Times-Roman', 7)
        c.setFont('Times-Roman', BODY); c.drawString(x, y, rest); x += c.stringWidth(rest, 'Times-Roman', BODY)

# title page
c.setFont('Times-Bold', 24); c.drawCentredString(W / 2, H / 2, 'Sample Book'); c.showPage(); page += 1
for label, title, paras, notes in CH:
    c.setFont('Times-Bold', 20); c.drawString(LM, H - 150, label)
    c.setFont('Times-Bold', 20); c.drawString(LM, H - 178, title)
    y = H - 230
    for para in paras:
        for i, ln in enumerate(para):
            draw_line(LM + (18 if i == 0 else 0), y, ln); y -= 15
        y -= 4
    c.setFont('Times-Roman', 8)
    fy = 90
    for n in notes:
        c.drawString(LM, fy, n); fy -= 11
    c.setFont('Times-Roman', 9); c.drawCentredString(W / 2, 36, str(page))
    c.showPage(); page += 1
    # continuation page with running head and a ruled table
    head_foot(title)
    y = H - 100
    for ln in ["The same principle applies to the material that follows, which continues the chapter on a new page and",
               "should join cleanly with no page number or running head in between."]:
        draw_line(LM, y, ln); y -= 15
    if label == 'Chapter 2':
        y -= 20; rows = [['Element', 'Print', 'Audio'], ['Heading', 'Visible', 'Announced'], ['Footnote', 'Page bottom', 'End of book']]
        cw = 120
        for r, row in enumerate(rows):
            for k, cell in enumerate(row):
                c.setFont('Times-Bold' if r == 0 else 'Times-Roman', 10); c.drawString(LM + 6 + k * cw, y - 14, cell)
            for k in range(4): c.line(LM + k * cw, y, LM + k * cw, y - 20)
            c.line(LM, y, LM + 3 * cw, y); y -= 20
        c.line(LM, y, LM + 3 * cw, y)
    c.showPage(); page += 1
c.save()

# EPUB
from ebooklib import epub
b = epub.EpubBook(); b.set_identifier('sample-1'); b.set_title('Sample EPUB'); b.add_author('Test Author'); b.set_language('en')
items = []
for i, (label, title, paras, notes) in enumerate(CH, 1):
    body = f'<h1 class="cn">{label}</h1><h1 class="ct">{title}</h1>'
    for para in paras:
        txt = ' '.join(para).replace('compre- hension', 'comprehension')
        import re
        txt = re.sub(r'\^(\d+)', r'<sup><a href="#n\1" epub:type="noteref">\1</a></sup>', txt)
        body += f'<p>{txt}</p>'
    body += '<aside epub:type="footnotes">' + ''.join(f'<p id="n{n.split(".")[0]}">{n}</p>' for n in notes) + '</aside>'
    it = epub.EpubHtml(title=title, file_name=f'ch{i}.xhtml', content=f'<html><body>{body}</body></html>')
    b.add_item(it); items.append(it)
b.toc = items; b.spine = items; b.add_item(epub.EpubNcx()); b.add_item(epub.EpubNav())
epub.write_epub(os.path.join(OUT, 'sample.epub'), b)
print('wrote', os.listdir(OUT))

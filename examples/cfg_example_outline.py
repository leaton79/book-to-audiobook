# Sections built automatically from the PDF's bookmark outline.
import re
from tocsec import from_toc, chapnum, part_title

SRC = "books/Kirschner - How Learning Happens.pdf"

def rule(title, i):
    if title in ('Preface', 'Introduction'):
        return ('chap', title)
    if title.upper().startswith('PART'):
        return ('part', part_title(title))
    if re.match(r'^\d+\. ', title):
        n, rest = chapnum(title)
        return ('chap', f'Chapter {n}: {rest[0].upper() + rest[1:]}')
    return None  # skip everything else (front matter, index)

CFG = {
    'title': 'How Learning Happens',
    'author': 'Paul A. Kirschner and Carl Hendrick',
    'sections': from_toc(SRC, 2, rule, last_page=325),
    'head_min': 1.2,
    'font_heads': False,
}

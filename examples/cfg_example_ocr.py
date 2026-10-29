# Scanned book after re-OCR (see docs/configuration.md, section 6).
SRC = "books/ocr/Example Author - Scanned Book (ocr).pdf"
CFG = {
    'title': 'Scanned Book',
    'author': 'Example Author',
    'sections': [
        (9, 24, 'chap', 'Introduction'),
        (25, 58, 'chap', 'Chapter 1: Opening Chapter'),
        (59, 90, 'chap', 'Chapter 2: Second Chapter'),
        (291, 310, 'notes', 'Notes'),
    ],
    'ocr': True, 'merge_gap': 60, 'size_tol': 5, 'head_min': 1.6, 'fn': False,
    'font_heads': False, 'fig_filter': False, 'margin_filter': False, 'drop_first_caps': True,
    'top_caps': 0.16,
    'notes_head_re': r'^(Introduction|Chapter \d+)',
    # Fix OCR misreads of decorative chapter-opening capitals:
    'replace': [('Tuts book', 'This book'), ('Aurnoven', 'Although')],
}

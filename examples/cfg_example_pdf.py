# Born-digital PDF with a separate endnotes section, sections written by hand.
# Page numbers are PDF page indexes (1-based, inclusive), not the numbers printed on the page.
SRC = "books/Sarah A. Bell - Vox ex Machina.pdf"
CFG = {
    'title': 'Vox ex Machina: A Cultural History of Talking Machines',
    'author': 'Sarah A. Bell',
    'sections': [
        (12, 17, 'chap', 'Prologue'),
        (18, 35, 'chap', 'Introduction'),
        (36, 61, 'chap', 'Chapter 1: The Voder (1939)'),
        # ... remaining chapters ...
        (206, 213, 'chap', 'Epilogue: When Will Siri Laugh?'),
        (214, 247, 'notes', 'Notes'),
    ],
}

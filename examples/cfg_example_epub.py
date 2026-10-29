# EPUB: list the spine files to keep and map the book's CSS classes to roles.
# Run the survey snippet in docs/configuration.md first to find file names and classes.
SRC = "books/Example Author - Example Book.epub"
CFG = {
    'title': 'Example Book: A Subtitle',
    'author': 'Example Author',
    'files': [
        ('intro.xhtml', 'chap', 'Introduction'),
        ('ch01.xhtml', 'chap', 'Chapter 1: First Chapter Title'),
        ('ch02.xhtml', 'chap', 'Chapter 2: Second Chapter Title'),
        ('notes.xhtml', 'notes', 'Notes'),
        ('biblio.xhtml', 'back', 'Bibliography'),
    ],
    'cls': {
        'chapter-number': 'drop',   # the config supplies spoken titles
        'chapter-title': 'drop',
        'block-quote': 'quote',
        'figure-caption': 'cap',
        'notes-chapter-head': 'nh', # starts a note group in notes.xhtml
        'epigraph-source': 'skip',
    },
    'imgdesc': {
        'fig2-1.jpg': 'A line chart of enrollment from 2000 to 2020, rising steadily from about 2 million to 5 million.',
    },
}

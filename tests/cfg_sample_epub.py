import os
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'sample.epub')
CFG = {'title': 'Sample EPUB', 'author': 'Test Author',
       'files': [('ch1.xhtml', 'chap', 'Chapter 1: Listening as Reading'), ('ch2.xhtml', 'chap', 'Chapter 2: What the Ear Needs')],
       'cls': {'cn': 'drop', 'ct': 'drop'}}

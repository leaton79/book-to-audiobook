#!/bin/bash
# Smoke test: builds two synthetic books, runs both extractors, audits, and renders.
set -e
cd "$(dirname "$0")/.."
python3 tests/make_sample_books.py tests/out
python3 scripts/pdf_extract.py tests/cfg_sample_pdf.py tests/out/sample_pdf.json
python3 scripts/epub_extract.py tests/cfg_sample_epub.py tests/out/sample_epub.json
python3 scripts/audit.py tests/cfg_sample_pdf.py tests/out/sample_pdf.json
python3 scripts/render.py tests/out/sample_pdf.json "tests/out/Test Author - Sample Book.pdf"
python3 scripts/render.py tests/out/sample_epub.json "tests/out/Test Author - Sample EPUB.pdf"
python3 - <<'PY'
import json
b = json.load(open('tests/out/sample_pdf.json'))
text = ' '.join(x['x'] for x in b['blocks'])
assert 'aloud, so' in text and 'well-known' in text, 'line joining or hyphen handling failed'
assert not any(x['x'].strip().isdigit() for x in b['blocks']), 'page number survived'
assert sum(len(g['items']) for g in b['notes']) == 3, 'footnotes not collected'
print('All checks passed. Outputs are in tests/out/')
PY

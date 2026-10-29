# Configuration and Workflow Reference

Each book gets a small Python config file that tells the extractor where chapters begin and how to treat the book's layout. Configs define two names: `SRC` (path to the book) and `CFG` (a dictionary). Pass the config path to an extractor:

```bash
python scripts/pdf_extract.py my_configs/cfg_bell.py work/bell.json
python scripts/render.py work/bell.json "Audio Edition/Bell - Vox ex Machina.pdf"
```

See `examples/` for complete configs.

## 1. Inventory

- For each PDF, record page count, extractable characters in the first 40 pages, and the Producer field (`pymupdf.open(f).metadata`). Scanner and OCR producers include Paper Capture, LuraDocument, iText scans, and pdf-lib.
- Measure text quality by sampling pages and computing the share of tokens that are real words (`wordfreq.zipf_frequency(word, 'en') > 2.5`). A share below about 0.96, or visibly scrambled text, means the book needs OCR (section 6).
- Check `pymupdf.open(f).get_toc()`. Most publisher PDFs have a usable outline, which makes section mapping nearly automatic.

## 2. PDF configs

### Sections

`CFG['sections']` is a list of `(start_page, end_page, kind, title)`. Pages are 1-based PDF page indexes (the viewer's page count, ignoring printed page numbers), inclusive.

| kind | Meaning |
|---|---|
| `chap` | A chapter or similar section; `title` becomes its spoken heading |
| `part` | A part divider |
| `cont` | Continues the previous chapter after an excluded insert, such as a photo essay |
| `notes` | An endnotes section; headings inside it start new note groups |
| `back` | Bibliography or references |

Any page range you leave out is skipped, which is how front matter and the index get cut.

**From the outline:** `tocsec.from_toc(path, level, rule, last_page=None)` builds sections from the PDF bookmarks. `rule(title, index)` returns `(kind, spoken_title)` or `None` to skip. Helpers `chapnum()` and `part_title()` normalize "3. Title" and "PART II" forms. See `examples/cfg_example_outline.py`.

**Without an outline:** run `python scripts/pagemap.py book.pdf` to list pages with large-font text (likely chapter openings), compare against the printed contents page, and write the ranges by hand. `python scripts/probe.py book.pdf 12 13` prints line positions, sizes, and bold or italic flags for calibration.

### Heading conventions

- `Chapter N: Title` (add "Chapter" even when the book prints only a numeral)
- `Part One: Title`, `Introduction`, `Preface`, `Foreword, by Name`, `Appendix A: Title`, `Epilogue`, `Conclusion`
- Edited volumes: `Chapter N: Title, by Author`

### What the PDF extractor does automatically

- Drops running heads and page numbers in the top and bottom zones, including `[ 12 ]`, `12 Title`, and `Title 12`.
- Removes superscript note markers (by font flag, or by smaller size plus raised baseline); a regex catches OCR'd markers stuck to words.
- Collects page-bottom footnotes into the chapter's notes.
- Treats in-chapter headings such as References, Notes, Works Cited, or Select Bibliography as the start of a reference tail and moves it to the notes.
- Detects headings by size, bold, ALL CAPS, centering, or font family, and drops headings that repeat the chapter title.
- Rebuilds paragraphs, including across pages, from indents, gaps, and short last lines.
- Dehyphenates with a word-frequency check, keeping "full-time" and joining "integra-tion".
- Rejoins drop caps ("I am" and "A few" keep their space).
- Converts ruled (vector) tables into sentences.
- Drops text inside figure regions, margin glosses, side pull quotes, monospace code, bullet-glyph lines, and "(Continued)". Margin captions are kept.

### PDF config keys

| Key | Default | Use |
|---|---|---|
| `top`, `bottom` | 0.075, 0.07 | Header and footer zone heights as fractions of the page. Raise `top` to 0.1 if running heads survive. |
| `head_min` | 1.15 | Font-size ratio (to body text) that counts as a heading. |
| `font_heads` | True | Treat a different font family as a heading signal. Set False when body text mixes fonts. |
| `fn` | True | Detect page-bottom footnotes. Set False when the book has none or sidebars are being caught as footnotes. |
| `fn_delta` | 0.7 | How much smaller than body text a footnote line must be. |
| `drop_re` | [] | Regexes for lines to drop (for example a recurring publisher footer). |
| `replace`, `regex_replace` | [] | Block-level text fixes applied after cleaning: `[('Tuts book', 'This book')]`. |
| `notes_head_re` | None | In a notes section, only lines matching this regex start a new note group. Useful for OCR'd notes. |
| `figdesc` | {} | Maps a caption prefix ("Figure 3.1") to an image description inserted after that caption. |
| `lig_repair` | False | Repairs dropped "Th" and "ft" ligatures ("Te" to "The", "draf" to "draft"). Fix leftovers with `replace`. |
| `reftail_sticky` | False | Keep everything after a reference heading in the notes, even if later headings appear. |
| `tables` | True | Convert ruled tables to sentences. |
| `fig_filter`, `margin_filter` | True | Drop figure-region text and margin glosses. |
| `drop_mono` | True | Drop monospace (code output) lines. |
| `inline_marks` | True | Strip digit markers stuck to word endings. |
| `gap` | 0.9 | Vertical gap (in body-size units) that starts a new paragraph. |

### OCR'd sources

Start with:

```python
'ocr': True, 'merge_gap': 60, 'size_tol': 5, 'head_min': 1.6, 'fn': False, 'font_heads': False,
'fig_filter': False, 'margin_filter': False, 'drop_first_caps': True,
```

Add `'top_caps': 0.16` to drop ALL-CAPS running heads near the top of the page. Then fix chapter-opening drop caps by hand with `replace` (OCR often reads a decorative initial badly, for example "Tuts book" for "This book").

## 3. EPUB configs

Survey the book first:

```python
import sys, collections, ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
b = epub.read_epub(sys.argv[1])
for idref, _ in b.spine:
    it = b.get_item_with_id(idref); s = BeautifulSoup(it.get_content(), 'lxml')
    print(it.get_name(), len(s.get_text(' ', strip=True)), [h.get_text(' ', strip=True)[:60] for h in s.find_all(['h1','h2','h3'])][:3], s.get_text(' ', strip=True)[:80])
cnt = collections.Counter(); ex = {}
for idref, _ in b.spine:
    s = BeautifulSoup(b.get_item_with_id(idref).get_content(), 'lxml')
    for el in s.find_all(['p','h1','h2','h3','div','li','aside','table']):
        k = (el.name, ' '.join(el.get('class') or [])); cnt[k] += 1; ex.setdefault(k, el.get_text(' ', strip=True)[:70])
for k, v in cnt.most_common(60): print(v, k, ex[k])
```

Then write `CFG = {title, author, files, cls, imgdesc}`:

- `files`: list of `(spine_file, role, spoken_title)`. Roles: `chap`, `part`, `notes` (a separate notes file), `back` (bibliography), `skip`. Unlisted files are skipped.
- `cls`: maps CSS classes to roles: `drop` (chapter number and title lines, since the config supplies titles), `h2`, `h3`, `quote`, `cap`, `note` (in-chapter footnotes), `nh` (note-group heading in a notes file), `skip`.
- `imgdesc`: maps an image file name to a description inserted after it.
- `notes_map`: optional mapping from note-group headings in the notes file to spoken chapter titles.

The EPUB extractor removes note-reference links and superscripts automatically, collects notes inside `epub:type` footnote, endnote, or rearnote containers, and turns tables into one sentence per row.

## 4. Figures

- `python scripts/figsheet.py book.json` lists captions with their source pages.
- `python scripts/pagesheet.py book.pdf tag 80 41,57,90 figs/` renders 2x2 contact sheets of those pages.
- Write descriptions for informational figures only (chart axes, trends, key values; diagram boxes and arrows; tables saved as images). Skip photos and portraits. Add them to `CFG['figdesc']` and re-run.

## 5. Quality checks (do these for every book)

- `python scripts/qa.py book.json` shows the first two blocks after each chapter heading, random samples, and very short paragraphs that may be junk.
- `python scripts/audit.py cfg.py book.json` compares output to source. Body plus notes should land between about 0.9 and 1.2 of the source; lower means lost text. It also flags repeated short blocks (surviving running heads) and stray note markers.
- Search the JSON for `word- word` splits and lines like `12 Title`.
- Run `pdftotext` on a middle page of the rendered PDF to see exactly what the voice will read.

### Known failure modes

| Symptom | Cause | Fix |
|---|---|---|
| A chapter comes out nearly empty | A full-page scan image was treated as a figure region | Set `'fig_filter': False` |
| Chapter text lands in the notes | A reference-tail heading matched too broadly, or sidebars were read as footnotes | Set `'fn': False`; check `refheads` |
| Running heads survive | Header zone too small | Raise `top` to 0.1 or add a `drop_re` pattern |
| Paragraph fragments | A side column interleaved with the body | Usually handled; otherwise add `drop_re` for the sidebar text |
| "Te" and "draf" throughout | Ligature dropout in the source PDF | `'lig_repair': True` |

## 6. Re-OCR for scanned books

`scripts/ocr1.sh` OCRs one page with Tesseract. Run it in parallel over all pages:

```bash
mkdir -p ocr_pages
seq 1 312 | xargs -P 4 -I{} scripts/ocr1.sh "Book.pdf" ocr_pages {}
qpdf --empty --pages ocr_pages/p*.pdf -- book_ocr.pdf   # page files are zero-padded, so they sort correctly
```

- The script skips pages already done, so re-run it after any interruption.
- Check pages with `qpdf --check`; delete and re-run any that fail.
- Optional: strip the page images to get a small text-only PDF (`page.delete_image(xref)` in PyMuPDF, then `doc.save(out, garbage=4)`).
- Requires `tesseract`, `poppler` (pdftoppm), and `qpdf`. On macOS: `brew install tesseract poppler qpdf`.

## 7. Large files and uploads to AI tools

Many AI chat tools reject uploads over roughly 30 to 50 MB. Split first, upload the chunks, and rejoin:

```bash
qpdf --split-pages=60 big.pdf chunk-%d.pdf
qpdf --empty --pages $(ls chunk-*.pdf | sort -V) -- rejoined.pdf
```

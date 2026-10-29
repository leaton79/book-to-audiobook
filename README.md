# Book to Audio Edition

Turn a PDF or EPUB book into a clean, text-only edition for listening with ElevenLabs Reader, Speechify, Voice Dream, a screen reader, or any other text-to-speech tool.

Text-to-speech tools read everything on the page. In a typical academic book that means running heads every page, page numbers, superscript note markers in the middle of sentences, words split by line-end hyphens, and tables read as a stream of disconnected cells. This project strips those artifacts out, announces each chapter clearly, turns tables into spoken sentences, and moves all the notes to the end, grouped by chapter, so the book reads straight through.

## What it does

**Before** (what a text-to-speech voice reads from a typical PDF page):

> LISTENING AS READING ... so a clean source matters more for listening than for print. two The work of prep- aration is mostly subtraction. 14

**After:**

> Chapter 1: Listening as Reading.
> ... so a clean source matters more for listening than for print. The work of preparation is mostly subtraction.

Every output follows the same conventions:

- A title page, then each section on a new page with a spoken heading: "Chapter 3: Title", "Part One: Title", "Introduction", "Foreword, by Name".
- 12 pt serif body text with no running heads, page numbers, or hyphenation.
- Note markers removed from the text; all notes collected at the end under "Notes", grouped by chapter.
- Tables rewritten as sentences ("Footnote. Print: Page bottom; Audio: End of book.").
- Optional short image descriptions for informational charts and diagrams.
- PDF bookmarks on every chapter for navigation.
- Your original files are never modified.

## Choose your path

| Path | You need | Best for |
|---|---|---|
| **1. Chat prompt** | Any AI chat tool (Claude, ChatGPT, Gemini, Copilot) | One or a few books; no software to install |
| **2. AI with code execution** | An AI tool that runs Python on uploaded files (Claude, ChatGPT with data analysis, Claude Code) | Longer books, scanned books, batches |
| **3. Run the scripts yourself** | Python 3.10 or later | Full control, many books, no uploads to third parties |

Path 1 suits most readers. Path 3 keeps the books entirely on your own computer.

### Path 1: Chat prompt

1. Open [`prompts/chat-only-prompt.md`](prompts/chat-only-prompt.md) and copy the prompt inside the box.
2. Paste it into a new chat. The AI asks a few numbered setup questions (what to do with notes, front matter, figures).
3. Send the book a chapter at a time. For each chunk, the AI returns clean text, that chunk's notes, and a short check listing the first and last words so you can confirm nothing was dropped.
4. Type "finish" to get the assembled Notes section, then paste everything into a document and export as PDF or DOCX.

Chat tools work from the text you give them, so this path depends on copyable text. Scanned books with garbled text need OCR first (Path 2 or 3).

### Path 2: AI with code execution

1. Download this repository as a ZIP (green **Code** button, then **Download ZIP**).
2. Upload the ZIP and your book files to an AI tool that can run code.
3. Paste the prompt from [`prompts/code-assistant-prompt.md`](prompts/code-assistant-prompt.md).

The AI installs the scripts, inventories your books, asks a few questions, writes a config for each book, runs quality checks, and returns finished PDFs.

### Path 3: Run the scripts yourself

```bash
git clone https://github.com/leaton79/book-to-audiobook.git
cd book-to-audiobook
pip install -r requirements.txt
./tests/run_tests.sh          # confirms everything works; writes sample outputs to tests/out/
```

For each book:

1. **Write a config** describing where chapters start. Copy the closest file in [`examples/`](examples/) and edit it. PDFs with a bookmark outline can build their chapter list automatically ([`examples/cfg_example_outline.py`](examples/cfg_example_outline.py)).
2. **Extract:**
   ```bash
   python scripts/pdf_extract.py my_configs/cfg_mybook.py work/mybook.json
   # or, for EPUB:
   python scripts/epub_extract.py my_configs/cfg_mybook.py work/mybook.json
   ```
3. **Check quality:**
   ```bash
   python scripts/qa.py work/mybook.json
   python scripts/audit.py my_configs/cfg_mybook.py work/mybook.json   # PDFs: ratio near 0.9 to 1.2 means nothing was lost
   ```
4. **Render:**
   ```bash
   python scripts/render.py work/mybook.json "Audio Edition/Author - Short Title.pdf"
   ```

[`docs/configuration.md`](docs/configuration.md) covers every config option, OCR for scanned books, figure descriptions, and fixes for common problems.

Scanned books also need [Tesseract](https://github.com/tesseract-ocr/tesseract), poppler, and qpdf (macOS: `brew install tesseract poppler qpdf`).

## Responsible use

- **Use books you own or are licensed to use, for your own listening.** Converting a book you own into a format you can listen to is a common personal and accessibility practice, but copyright rules vary by country and by license. This project offers no legal advice. Do not share or post the converted files.
- **Library and publisher ebooks carry license terms.** Many prohibit uploading content to third-party services, including AI tools. Read the terms before using Path 1 or 2 with a licensed ebook.
- **DRM-protected files are out of scope.** These tools work only on files you can already open and copy text from. They contain nothing for removing copy protection.
- **Check your institution's data policy** before uploading books or other materials to an AI service. Path 3 keeps everything on your own computer.
- **Accessibility needs come first.** If you have a print disability, your campus disability services office or a service such as Bookshare may already provide accessible versions of the books you need.

## Limitations

- **OCR introduces errors.** Books converted from scans will contain some misread words. Listen to a chapter before relying on a passage for citation, and check quotes against the original.
- **Complex layouts lose some content by design.** Margin glosses, pull quotes, sidebars, and photos are dropped; captions remain. Textbooks with heavy sidebars may need config tuning.
- **Figure descriptions are written per book.** The scripts insert descriptions you (or an AI) write; they do not generate them.
- **Language.** The cleaning heuristics (dehyphenation, OCR checks) use English word frequencies. Other languages work for basic cleanup with weaker hyphen handling.
- **Chat-based conversion (Path 1) can occasionally drop or condense text** when replies run long. The prompt's built-in end-of-chunk check is there to catch it; smaller chunks reduce the risk.

## Repository contents

```
prompts/
  chat-only-prompt.md        Path 1: paste-in prompt for any AI chat tool
  code-assistant-prompt.md   Path 2: prompt for AI tools that run code
scripts/
  pdf_extract.py             PDF to cleaned book JSON (line-level, font-aware)
  epub_extract.py            EPUB to cleaned book JSON
  render.py                  Book JSON to audio-ready PDF with bookmarks
  textclean.py, postproc.py  Shared cleaning: ligatures, dehyphenation, captions, notes
  tocsec.py                  Build chapter sections from a PDF outline
  pagemap.py, probe.py       Find chapter starts and calibrate layout settings
  qa.py, audit.py            Quality checks
  figsheet.py, pagesheet.py  Locate figures and render contact sheets for describing them
  ocr1.sh                    One-page OCR helper for scanned books
examples/                    Sample configs: hand-mapped PDF, outline-based PDF, EPUB, OCR
docs/configuration.md        Full reference: config keys, OCR, figures, troubleshooting
tests/                       Synthetic sample books and a smoke test
```

## Background

This workflow began as a set of instructions and scripts developed with Claude (Anthropic) to convert a personal library of academic books for listening, then refined across a range of born-digital and scanned titles. It is shared here so others can adapt it.

## Contributing

Issues and pull requests are welcome, especially example configs for tricky layouts, fixes for languages other than English, and reports of artifacts that survive cleaning. When reporting a problem, describe the layout or share a page from a public-domain book, and keep copyrighted pages out of issues.

## License

Code and documentation are released under the [MIT License](LICENSE).

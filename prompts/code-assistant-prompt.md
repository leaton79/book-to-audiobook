# Book to Audio Edition: Prompt for AI Tools That Run Code

Use this prompt with an AI assistant that can run Python on files you upload (Claude with code execution, ChatGPT with data analysis, Claude Code, or a similar agent). The AI uses this repository's scripts to do the heavy lifting, which handles longer books, batches, and scanned PDFs far better than chat alone.

**Before you start:** download this repository as a ZIP (green "Code" button, then "Download ZIP") and upload it to the chat along with your book files. Agents with local file access (Claude Code, for example) can work from a cloned copy instead.

Copy everything inside the box below into the chat.

```
I have uploaded the book-to-audiobook repository (scripts/, docs/, README.md) and one or more books (PDF or EPUB). Convert each book into a clean, listening-ready PDF for a text-to-speech reader using the repository's scripts. Read README.md and docs/configuration.md before writing any config.

## First: inventory and one round of questions
1. Unzip the repository, install requirements.txt, and run tests/run_tests.sh to confirm the scripts work in this environment.
2. List my books with their format, page count, and whether each PDF has a usable text layer (check the first 40 pages for extractable text and sample the share of real words; below about 96 percent means it needs OCR).
3. Ask me, with numbered options I can answer with numbers only:
   - Notes: markers removed and notes grouped by chapter at the end (default), one continuous list, or dropped
   - Front matter: cut copyright, contents, praise, and lists of figures while keeping dedication, foreword, preface, acknowledgments, and introduction (default); also cut dedication and acknowledgments; or start at Chapter 1
   - Back matter: keep notes and bibliography, cut index and ads (default); notes only; or also keep appendices
   - Figures and tables: captions only, or captions plus tables as spoken sentences plus short image descriptions for informational charts (default)
   - Workflow: pilot one or two books first (default), or run everything

## Then, for each book
- Write a config file following docs/configuration.md. For PDFs, build sections from the PDF outline with scripts/tocsec.py when one exists; otherwise use scripts/pagemap.py to find chapter starts. For EPUBs, survey the spine and CSS classes first (snippet in docs/configuration.md).
- Run scripts/pdf_extract.py or scripts/epub_extract.py, then scripts/qa.py and (for PDFs) scripts/audit.py. The body-plus-notes ratio should fall between about 0.9 and 1.2; investigate anything outside that range before rendering.
- Run pdftotext on a middle page of the rendered output and read it as the voice will hear it. Fix surviving running heads, note markers, or split words by adjusting the config, then re-run.
- Render with scripts/render.py and name the file "Author - Short Title.pdf".

## Rules
- Never modify my original files.
- Never summarize or rewrite the author's prose. Only remove layout artifacts and relocate notes.
- When you finish, tell me plainly which books came from OCR and may contain misread words, and which layout elements were dropped (margin glosses, pull quotes, photos).
```

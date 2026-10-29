import sys, pymupdf
from PIL import Image, ImageDraw
# usage: python pagesheet.py source.pdf tag dpi 12,13,40 [outdir]
import os
src, tag, dpi = sys.argv[1], sys.argv[2], int(sys.argv[3]); pages = [int(x) for x in sys.argv[4].split(',')]
outdir = sys.argv[5] if len(sys.argv) > 5 else 'figs'; os.makedirs(outdir, exist_ok=True)
doc = pymupdf.open(src)
for i in range(0, len(pages), 4):
    ims = []
    for p in pages[i:i + 4]:
        pix = doc[p - 1].get_pixmap(dpi=dpi); ims.append((p, Image.frombytes('RGB', (pix.width, pix.height), pix.samples)))
    w = max(im.width for _, im in ims); h = max(im.height for _, im in ims) + 18
    S = Image.new('RGB', (w * 2, h * ((len(ims) + 1) // 2)), 'white'); d = ImageDraw.Draw(S)
    for j, (p, im) in enumerate(ims):
        x, y = (j % 2) * w, (j // 2) * h
        d.text((x + 5, y + 2), f'p{p}', fill='red'); S.paste(im, (x, y + 18))
    out = os.path.join(outdir, f'{tag}_{i // 4:02d}.png'); S.save(out); print(out)

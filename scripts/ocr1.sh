#!/bin/bash
# usage: ocr1.sh input.pdf outdir page [dpi]
IN="$1"; OUT="$2"; p=$3; DPI=${4:-300}
pp=$(printf "%04d" $p)
[ -f "$OUT/p$pp.pdf" ] && exit 0
mkdir -p $HOME/ocrtmp
pdftoppm -f $p -l $p -r $DPI -gray -png "$IN" "$HOME/ocrtmp/img$pp-$RANDOM" >/dev/null 2>&1
img=$(ls $HOME/ocrtmp/img$pp-*.png | head -1)
OMP_THREAD_LIMIT=1 tesseract "$img" "$OUT/p$pp" -l eng --psm 3 pdf >/dev/null 2>&1
rm -f $HOME/ocrtmp/img$pp-*
# driver: timeout 160 bash -c "seq 1 N | xargs -P 4 -I{} $HOME/ocr1.sh 'Book.pdf' 'ocr_dir' {}"

#!/usr/bin/env python3
"""Recorta uma região de uma página de PDF em alta resolução.

Uso: python3 -I recortar_pagina.py MATERIAL.pdf PAGINA X0 Y0 X1 Y1 SAIDA.png [--dpi 250]

X0 Y0 X1 Y1 são pixels da imagem da página em paginas/, renderizada a 100 dpi.
"""
import os
import shutil
import subprocess
import sys
import tempfile

try:
    from PIL import Image
except ImportError:
    sys.exit('Falta o Pillow. Instale com: pip install Pillow')

Image.MAX_IMAGE_PIXELS = 400_000_000
args = sys.argv[1:]
dpi = 250
if '--dpi' in args:
    i = args.index('--dpi')
    dpi = int(args[i + 1])
    del args[i:i + 2]
if len(args) != 7:
    sys.exit(__doc__)
if not shutil.which('pdftoppm'):
    sys.exit('Falta o pdftoppm. Instale o poppler-utils.')
pdf, pagina, saida = args[0], int(args[1]), args[6]
x0, y0, x1, y1 = (float(v) for v in args[2:6])
if x1 <= x0 or y1 <= y0:
    sys.exit('A região precisa ter X1 > X0 e Y1 > Y0.')
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(['pdftoppm', '-r', str(dpi), '-f', str(pagina), '-l', str(pagina), '-png', '-singlefile', pdf, os.path.join(tmp, 'p')], check=True)
    with Image.open(os.path.join(tmp, 'p.png')) as im:
        k = dpi / 100
        caixa = tuple(round(v * k) for v in (x0, y0, x1, y1))
        caixa = (max(0, caixa[0]), max(0, caixa[1]), min(im.width, caixa[2]), min(im.height, caixa[3]))
        im.crop(caixa).save(saida)
        print(f'{saida} · {caixa[2] - caixa[0]} × {caixa[3] - caixa[1]} px')

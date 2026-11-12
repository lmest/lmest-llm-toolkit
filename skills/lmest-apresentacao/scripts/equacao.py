#!/usr/bin/env python3
"""Desenha uma equação LaTeX como imagem, para usar em qualquer saída.

Uso: python3 equacao.py 'LATEX' PASTA/imagens/eq-nome [--px 44] [--cor #1b2b3a]

Gera eq-nome.svg (texto convertido em curvas: não depende de fonte instalada) e
eq-nome.png (4× a resolução, usado no PPTX). Imprime a largura e a altura em px do
palco para o <img>, com o corpo da fórmula na altura de --px (padrão 44).
O LaTeX é o do mathtext do matplotlib (frações, índices, letras gregas, raízes,
somatórios, integrais, acentos); ambientes como align ou matrix não são aceitos:
quebre em várias equações ou use \\begin…\\end só se o mathtext aceitar.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # funciona também com python3 -I
import lmest_comum  # noqa: F401  (ajusta o caminho de pacotes)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit('Falta o matplotlib. Instale com: pip install matplotlib')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('latex')
    ap.add_argument('base')
    ap.add_argument('--px', type=float, default=44)
    ap.add_argument('--cor', default='#1b2b3a')
    a = ap.parse_args()
    plt.rcParams.update({'mathtext.fontset': 'cm', 'svg.fonttype': 'path'})
    tex = a.latex.strip()
    if not tex.startswith('$'):
        tex = f'${tex}$'
    pt = a.px * 0.75  # 1 px de tela = 0,75 pt a 96 dpi
    fig = plt.figure()
    fig.text(0, 0, tex, fontsize=pt, color=a.cor)
    os.makedirs(os.path.dirname(os.path.abspath(a.base)) or '.', exist_ok=True)
    try:
        fig.savefig(a.base + '.svg', bbox_inches='tight', pad_inches=0.02, transparent=True)
        fig.savefig(a.base + '.png', bbox_inches='tight', pad_inches=0.02, transparent=True, dpi=96 * 4)
    except ValueError as e:
        sys.exit(f'LaTeX não aceito pelo mathtext: {e}')
    from PIL import Image
    w, h = Image.open(a.base + '.png').size
    print(f'{os.path.basename(a.base)}.svg: width:{round(w / 4)}px; height:{round(h / 4)}px')


if __name__ == '__main__':
    main()

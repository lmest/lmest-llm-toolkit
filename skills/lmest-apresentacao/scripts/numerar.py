#!/usr/bin/env python3
"""Numera os slides e aplica (ou retira) a barra de progresso em todo o deck.

Uso: python3 numerar.py PASTA

Para cada id de deck.json > order:
  - O número de página é a posição no deck (a capa é 1). Fica em top:1000px; left:1631px.
  - Capa, agradecimento, resumo, divisórias (ids "sec-...") e os ids de projeto.json >
    sem_numero ficam sem número e sem barra.
  - A barra só existe se projeto.json > barra_progresso for true. Largura =
    round(posição × 1920 / total), com o trilho cinza por baixo.
  - Números e barras antigos são sempre removidos antes, para nunca ficarem duplicados.
  - Garante data-transition="fade" na <section>.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # funciona também com python3 -I
from lmest_comum import FONTE, Projeto, gravar, ler

RE_NUMERO = re.compile(r'[ \t]*<p\b(?=[^>]*\btop:\s*1000(?:\.0+)?px)(?=[^>]*\bleft:\s*1631(?:\.0+)?px)[^>]*>.*?</p>[ \t]*\n?', re.S | re.I)
RE_BARRA = re.compile(r'[ \t]*<div\b(?=[^>]*\btop:\s*1073(?:\.0+)?px)[^>]*>\s*</div>[ \t]*\n?', re.S | re.I)
RE_SECTION = re.compile(r'<section\b[^>]*>', re.I)


def numero_html(n):
    return (f'  <p style="position:absolute; top:1000px; left:1631px; width:200px; font-family:{FONTE}; '
            f'font-size:24px; font-weight:700; line-height:1.2; text-align:right; color:#1e88c7">{n}</p>\n')


def barra_html(largura):
    return ('  <div style="position:absolute; top:1073px; left:0; width:1920px; height:7px; background:#d6dee6"></div>\n'
            f'  <div style="position:absolute; top:1073px; left:0; width:{largura}px; height:7px; background:#1e88c7"></div>\n')


def fade(tag):
    if re.search(r'data-transition\s*=', tag):
        return re.sub(r'data-transition\s*=\s*"[^"]*"', 'data-transition="fade"', tag)
    return tag.replace('<section', '<section data-transition="fade"', 1)


def inserir(html, trecho):
    """Antes do <aside> (as notas são sempre o último filho) ou do </section>."""
    i = html.rfind('<aside')
    if i < 0:
        i = html.rfind('</section>')
    while i > 0 and html[i - 1] in ' \t':
        i -= 1
    return html[:i] + trecho + html[i:]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    prj = Projeto(sys.argv[1])
    ordem = prj.ordem()
    total = len(ordem)
    barra = bool(prj.proj.get('barra_progresso'))
    for pos, sid in enumerate(ordem, 1):
        caminho = prj.arquivo(sid)
        try:
            html = ler(caminho)
        except FileNotFoundError:
            print(f'AVISO: slide {sid} está em order, mas slides/{sid}.html não existe.')
            continue
        html = RE_NUMERO.sub('', html)
        html = RE_BARRA.sub('', html)
        html = RE_SECTION.sub(lambda m: fade(m.group(0)), html, count=1)
        if prj.tem_numero(sid):
            trecho = numero_html(pos)
            if barra:
                trecho += barra_html(round(pos * 1920 / total))
            html = inserir(html, trecho)
        gravar(caminho, html)
    print(f'{total} slides numerados; barra de progresso {"aplicada" if barra else "ausente"}.')


if __name__ == '__main__':
    main()

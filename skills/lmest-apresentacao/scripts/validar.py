#!/usr/bin/env python3
"""Confere o projeto antes de gerar qualquer saída.

Uso: python3 validar.py PASTA

ERRO impede a geração e precisa ser corrigido. AVISO é uma estimativa, que deve ser
conferida no slide citado (estouro de texto, título longo etc.). Sai com código 1 se houver ERRO.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # funciona também com python3 -I
from lmest_comum import Projeto, estilo, ler, linhas_texto, px

try:
    from bs4 import BeautifulSoup, NavigableString, Tag
except ImportError:
    sys.exit('Falta o BeautifulSoup. Instale com: pip install beautifulsoup4')

TEXTO = {'h1', 'h2', 'h3', 'p', 'ul', 'ol'}
PERMITIDAS = TEXTO | {'div', 'img', 'table', 'svg', 'hr', 'x-embed', 'aside'}
INLINE = {'b', 'i', 'u', 'a', 'span', 'br', 'li', 'ul', 'ol', 'strong', 'em', 'tr', 'td', 'th', 'tbody', 'thead'}
PROIBIDO_CSS = re.compile(r'(?<![-\w])(margin|z-index|float)\s*:|\d(em|rem|vw|vh)\b|var\(', re.I)


class Relato:
    def __init__(self):
        self.erros, self.avisos = [], []

    def erro(self, sid, msg):
        self.erros.append(f'ERRO  [{sid}] {msg}')

    def aviso(self, sid, msg):
        self.avisos.append(f'AVISO [{sid}] {msg}')


def texto_de(el):
    partes = []
    for d in el.descendants:
        if isinstance(d, NavigableString):
            partes.append(str(d))
        elif isinstance(d, Tag) and d.name in ('br', 'li'):
            partes.append('\n')
    return re.sub(r'[ \t]+', ' ', ''.join(partes)).strip()


ESPACO_MIN = 16  # px entre caixas vizinhas (o padrão é 22 a 40)


def checar_espacos(sid, filhos, r):
    """Caixas pintadas lado a lado ou empilhadas devem ter um respiro; uma dentro da outra é permitido."""
    caixas = []
    for el in filhos:
        if el.name not in ('div', 'x-embed'):
            continue
        st = estilo(el.get('style'))
        l, t, w, h = (px(st.get(k), b) for k, b in (('left', 1920), ('top', 1080), ('width', 1920), ('height', 1080)))
        if None in (l, t, w, h) or w >= 1900 or st.get('border-radius') == '17px' or h < 20 or w < 20:
            continue
        if el.name == 'div' and not (st.get('background') or st.get('border') or st.get('box-shadow')):
            continue
        caixas.append((l, t, l + w, t + h))
    for i in range(len(caixas)):
        for j in range(i + 1, len(caixas)):
            a, b = caixas[i], caixas[j]
            dentro = lambda x, y: x[0] >= y[0] - 1 and x[1] >= y[1] - 1 and x[2] <= y[2] + 1 and x[3] <= y[3] + 1
            if dentro(a, b) or dentro(b, a):
                continue
            sobrepoe_x = min(a[2], b[2]) - max(a[0], b[0]) > 0
            sobrepoe_y = min(a[3], b[3]) - max(a[1], b[1]) > 0
            vao_y = max(a[1], b[1]) - min(a[3], b[3])
            vao_x = max(a[0], b[0]) - min(a[2], b[2])
            if (sobrepoe_x and vao_y < ESPACO_MIN) or (sobrepoe_y and vao_x < ESPACO_MIN):
                r.erro(sid, f'caixas coladas ou sobrepostas em y≈{round(min(a[3], b[3]))} / x≈{round(min(a[2], b[2]))}: '
                            f'deixe de 22 a 40 px entre cartões (regras-de-slide.md §4).')
                return


def checar_slide(prj, sid, html, r, pptx):
    artefato = bool(prj.proj.get('origem_artefato'))
    fluxo = r.aviso if artefato else r.erro
    if len(re.findall(r'<section\b', html, re.I)) != 1:
        r.erro(sid, 'o arquivo deve ter exatamente uma <section>.')
        return
    sopa = BeautifulSoup(html, 'html.parser')
    sec = sopa.find('section')
    if sec.get('id') != sid:
        r.erro(sid, f'id da <section> ({sec.get("id")}) difere do nome do arquivo.')
    if sec.get('data-transition') != 'fade':
        r.erro(sid, 'a <section> precisa de data-transition="fade" (rode numerar.py).')
    if 'data-build-in' in html or 'data-build-out' in html:
        r.erro(sid, 'data-build-in/out não é usado: anime com uma <x-embed>.')
    filhos = [c for c in sec.children if isinstance(c, Tag)]
    if not filhos or filhos[-1].name != 'aside' or not texto_de(filhos[-1]):
        r.erro(sid, 'faltam as notas do apresentador: um <aside> não vazio como último filho.')
    embeds = [c for c in filhos if c.name == 'x-embed']
    if sopa.find_all('x-embed') != embeds:
        r.erro(sid, '<x-embed> deve ser filho direto da <section>.')
    if len(embeds) > 8:
        r.erro(sid, 'mais de 8 <x-embed> no slide.')
    if embeds and pptx:
        r.erro(sid, 'há animação (<x-embed>), mas a saída PPTX foi pedida: PPTX não leva animações.')
    for e in embeds:
        conteudo = e.decode_contents()
        if len(conteudo.encode()) > 16 * 1024:
            r.erro(sid, f'<x-embed> com {len(conteudo.encode()) // 1024} KB (máximo 16 KB).')
        if re.search(r'/_blob/|https?://|src="lmest/|src="imagens/', conteudo):
            r.erro(sid, '<x-embed> não carrega arquivos: use SVG inline ou data: WebP pequeno.')
        if 'IntersectionObserver' not in conteudo:
            r.aviso(sid, '<x-embed> sem IntersectionObserver: a animação não recomeça ao voltar ao slide.')
    # Tamanho mínimo de fonte, inclusive dentro das minipáginas.
    for m in re.finditer(r'font-size\s*:\s*([\d.]+)(px|pt)?', html):
        v = float(m.group(1)) * (4 / 3 if m.group(2) == 'pt' else 1)
        if v < 24:
            r.erro(sid, f'font-size de {m.group(1)}{m.group(2) or "px"}: o mínimo é 24 px.')
            break
    for tag in sopa.find_all(['x-icon', 'x-shape', 'x-connector']):
        (r.erro if pptx else r.aviso)(sid, f'<{tag.name}> não é convertido para PPTX nem para o HTML offline: use ícones PNG do Design System, <div> ou <svg>.')
    numeros = 0
    for el in filhos:
        if el.name == 'aside':
            continue
        if el.name not in PERMITIDAS:
            r.erro(sid, f'elemento <{el.name}> fora do formato.')
            continue
        st = estilo(el.get('style'))
        if el.name != 'x-embed' and PROIBIDO_CSS.search(el.get('style') or ''):
            r.erro(sid, f'CSS fora do formato em <{el.name}> (margin, z-index, float, em/rem/vw/vh ou var()).')
        if el.name == 'svg':
            sv = str(el)
            if 'fill="none"' in sv and 'stroke' in sv and (px(el.get('width'), padrao=999) or 999) <= 64:
                r.aviso(sid, 'seta de traço fino: use a seta cheia de 80 × 32 px (layouts.md §5).')
            continue
        if el.name in TEXTO and texto_de(el) in ('→', '➜', '⟶', '->'):
            r.aviso(sid, 'seta como caractere: use a seta cheia de 80 × 32 px (layouts.md §5).')
        if st.get('position') != 'absolute':
            fluxo(sid, f'<{el.name}> "{texto_de(el)[:40]}" não está fixado: todo elemento visível usa position:absolute.')
            continue
        left = px(st.get('left'), 1920)
        top = px(st.get('top'), 1080)
        w = px(st.get('width'), 1920)
        h = px(st.get('height'), 1080)
        if left is None or top is None or w is None:
            r.erro(sid, f'<{el.name}> "{texto_de(el)[:40]}" sem left, top e width em px.')
            continue
        if 'translatex(-50%)' in (st.get('transform') or '').replace(' ', '').lower():
            left -= w / 2
        if el.name in ('div', 'img', 'x-embed', 'table') and h is None and el.name != 'table':
            r.erro(sid, f'<{el.name}> sem height.')
        if left < -1 or left + w > 1921 or top < -1 or (h is not None and top + h > 1081):
            r.erro(sid, f'<{el.name}> "{texto_de(el)[:40]}" sai do palco de 1920×1080.')
        borda = re.search(r'(?<![-\w])border\s*:\s*([\d.]+)px\s+solid', el.get('style') or '')
        if el.name == 'div' and borda and float(borda.group(1)) >= 2:
            r.erro(sid, f'cartão com contorno de {borda.group(1)} px: use 1 px #d6dee6 com a sombra shadow-card (regras-de-slide.md §4).')
        fundo = (st.get('background') or '').lower()
        if el.name == 'div' and fundo in ('#ffffff', '#fff', 'white') and (w or 0) < 1900 and 'box-shadow' not in st and 'border-radius' in st and st.get('border-radius') != '17px':
            r.aviso(sid, 'cartão branco sem a sombra shadow-card (box-shadow:0 2px 10px rgba(0,0,0,0.07)).')
        if el.name == 'div' and any(isinstance(c, Tag) and c.name != 'br' for c in el.children):
            r.aviso(sid, '<div> com filhos: no PPTX só a caixa é desenhada. Fixe cada texto e imagem como filho da <section>.')
        if el.name == 'img':
            src = el.get('src', '')
            if src.startswith('/_blob/') and artefato:
                pass
            elif src.startswith(('http:', 'https:', 'data:', '/_blob/')):
                r.erro(sid, f'imagem com src "{src[:40]}": use um arquivo da pasta (lmest/ ou imagens/).')
            elif not os.path.isfile(os.path.join(prj.pasta, src)):
                r.erro(sid, f'imagem não encontrada: {src}')
            elif src.lower().endswith('.svg') and not os.path.isfile(os.path.join(prj.pasta, src[:-4] + '.png')):
                r.aviso(sid, f'{src} não tem um .png de mesmo nome ao lado: o PPTX tentará converter o SVG.')
        if el.name in TEXTO | {'table'}:
            for d in el.find_all(True):
                if d.name not in INLINE:
                    r.erro(sid, f'<{d.name}> dentro de texto não é aceito: use <b>, <i>, <u>, <a>, <span style="color">, <br> ou caracteres Unicode (ωₙ, x², 10⁻⁴).')
                    break
        if el.name in TEXTO:
            t = texto_de(el)
            if top == 1000 and left == 1631:
                numeros += 1
                continue
            fs = px(st.get('font-size'), padrao=None)
            if fs is None:
                r.erro(sid, f'texto "{t[:40]}" sem font-size.')
                continue
            lh = float(st.get('line-height', '1.2')) if re.fullmatch(r'[\d.]+', st.get('line-height', '1.2')) else 1.2
            negrito = st.get('font-weight', '400') in ('700', 'bold', '600', '800', '900') or el.name in ('h1', 'h2', 'h3')
            caixa = st.get('text-transform') == 'uppercase'
            pad = [px(x, padrao=0) for x in (st.get('padding') or '0').split()]
            pad_h = (pad[1] if len(pad) > 1 else pad[0]) * 2 if pad else 0
            pad_v = pad[0] * 2 if pad else 0
            n = linhas_texto(t, w - pad_h, fs, negrito, caixa, px(st.get('letter-spacing'), padrao=0) or 0)
            altura = n * fs * lh + pad_v
            if h is not None and altura > h + 4:
                r.aviso(sid, f'texto "{t[:40]}" deve ocupar ~{n} linha(s) ({altura:.0f} px) numa caixa de {h:.0f} px.')
            if top < 144 and el.name in ('h1', 'h2') and n > 1:
                r.aviso(sid, f'título com ~{n} linhas: no cabeçalho cabe uma linha (até ~50 caracteres a 56 px).')
            if top + altura > 1000 and not (top >= 1000):
                r.aviso(sid, f'texto "{t[:40]}" deve terminar em y≈{top + altura:.0f}, abaixo da base do conteúdo (1000).')
    checar_espacos(sid, filhos, r)
    if numeros > 1:
        r.erro(sid, 'mais de um número de página (rode numerar.py).')
    if prj.tem_numero(sid) and numeros == 0:
        r.erro(sid, 'falta o número de página (rode numerar.py).')
    if not prj.tem_numero(sid) and (numeros or re.search(r'top:\s*1073px', html)):
        r.erro(sid, 'slide sem número não leva número nem barra (rode numerar.py).')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    prj = Projeto(sys.argv[1])
    r = Relato()
    pptx = 'pptx' in [s.lower() for s in prj.proj.get('saidas', [])]
    ordem = prj.ordem()
    if len(set(ordem)) != len(ordem):
        r.erro('deck', 'ids repetidos em order.')
    if not prj.proj.get('origem_artefato') and (not ordem or ordem[0] != 'capa' or ordem[-1] != 'agradecimento'):
        r.erro('deck', 'order deve começar em "capa" e terminar em "agradecimento" (rode montar_fixos.py).')
    existentes = {f[:-5] for f in os.listdir(prj.slides_dir) if f.endswith('.html')}
    for sid in sorted(existentes - set(ordem)):
        r.aviso(sid, 'arquivo em slides/ que não está em order (será ignorado; apague ou inclua).')
    for sid in ordem:
        caminho = prj.arquivo(sid)
        if not os.path.exists(caminho):
            r.erro(sid, 'está em order, mas o arquivo não existe.')
            continue
        checar_slide(prj, sid, ler(caminho), r, pptx)
    for linha in r.erros + r.avisos:
        print(linha)
    print(f'{len(ordem)} slides · {len(r.erros)} erro(s) · {len(r.avisos)} aviso(s)')
    sys.exit(1 if r.erros else 0)


if __name__ == '__main__':
    main()

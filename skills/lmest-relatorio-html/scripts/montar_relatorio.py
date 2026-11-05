#!/usr/bin/env python3
"""Monta o relatório HTML em arquivo único a partir de um conteudo.html.

Uso: python3 -I montar_relatorio.py CONTEUDO.html SAIDA.html

Marcações próprias aceitas no conteúdo (ver references/componentes.md):
  <relatorio titulo="" sobretitulo="" subtitulo="" logos="ufu,lmest" rodape="">
  <section id="x" data-nav="Nome no índice"> ... </section>
  <fig src="" cap="" [id=""] [alt=""] [largura="2400"] [classe="narrow"]></fig>
  <abas-fig rotulo="" cap=""><aba rotulo="" src="" [alt=""]></aba>...</abas-fig>
  <barras unidade="" [casas="4"] [destaque="rótulo"]><barra rotulo="" valor="0.5" [texto="1,1 mil"]></barra>...</barras>
  <eq>LaTeX</eq> em bloco e <eqi>LaTeX</eqi> na linha
  [[fig:id]] vira o número da figura com esse id
"""
import base64
import html as H
import io
import os
import re
import shutil
import subprocess
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit('Falta o Pillow. Instale com: pip install Pillow')

Image.MAX_IMAGE_PIXELS = 400_000_000
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')
ATTR = re.compile(r'([\w-]+)="([^"]*)"')
sem_tags = lambda s: re.sub(r'<[^>]+>', '', s)


def attrs(s):
    return {k: H.unescape(v) for k, v in ATTR.findall(s)}


def attr_html(s):
    return H.escape(sem_tags(s), quote=True)


def b64(dados):
    return base64.b64encode(dados).decode()


def img_uri(caminho, largura=2400):
    with Image.open(caminho) as im:
        animado = getattr(im, 'n_frames', 1) > 1
        temp = im.convert('RGBA')
    # GIF animado segue como está, porque a animação pode ser a informação da figura.
    if animado and caminho.lower().endswith('.gif') and os.path.getsize(caminho) <= 4_000_000:
        with open(caminho, 'rb') as f:
            return 'data:image/gif;base64,' + b64(f.read())
    fundo = Image.new('RGBA', temp.size, 'white')
    fundo.alpha_composite(temp)
    im = fundo.convert('RGB')
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'WEBP', quality=88, method=6)
    return 'data:image/webp;base64,' + b64(buf.getvalue())


def logo_uri(nome):
    caminho = os.path.join(ASSETS, 'logos', f'{nome}.png')
    if not os.path.isfile(caminho):
        sys.exit(f'Logo desconhecido: {nome}. Disponíveis: ufu, lmest, inct.')
    im = Image.open(caminho).convert('RGBA')
    # Placa da capa com 44 px de altura: 2x para telas de alta densidade.
    im.thumbnail((400, 120), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + b64(buf.getvalue())


def font_faces():
    css = []
    for f, peso, estilo in [('Regular', 400, 'normal'), ('Italic', 400, 'italic'), ('Bold', 700, 'normal'), ('BoldItalic', 700, 'italic')]:
        with open(os.path.join(ASSETS, 'fonts', f'Carlito-{f}.woff2'), 'rb') as a:
            css.append(f'@font-face{{font-family:Carlito;font-weight:{peso};font-style:{estilo};font-display:swap;src:url(data:font/woff2;base64,{b64(a.read())}) format("woff2")}}')
    return '\n'.join(css)


def mathml(tex, bloco=True):
    if not shutil.which('pandoc'):
        sys.exit('Falta o pandoc, usado para converter equações. Instale com: sudo apt install pandoc')
    d = '$$' if bloco else '$'
    r = subprocess.run(['pandoc', '-f', 'markdown', '-t', 'html', '--mathml'], input=f'{d}{tex.strip()}{d}', capture_output=True, text=True, check=True).stdout
    achado = re.search(r'<math.*</math>', r, re.S)
    if not achado:
        sys.exit(f'Equação não convertida: {tex}')
    # Sem isto, o MathML trata a vírgula decimal como separador e abre um espaço depois dela.
    return re.sub(r'<mn>(\d+)</mn>\s*(?:<mrow>)?\s*<mo[^>]*>,</mo>\s*(?:</mrow>)?\s*<mn>(\d+)</mn>', r'<mn>\1,\2</mn>', achado.group(0))


def equacao(tex, bloco=True):
    """KaTeX renderiza o LaTeX na abertura, na fonte Computer Modern do design system.
    O MathML do pandoc fica dentro como reserva, se o script não rodar."""
    tex = tex.strip()
    tag = 'div' if bloco else 'span'
    # \azul{} e \vermelho{} são macros do KaTeX; o pandoc não as conhece, então a reserva sai sem cor.
    reserva = re.sub(r'\\(?:azul|vermelho)(?![A-Za-z])', '', tex)
    return f'<{tag} class="tex" data-display="{1 if bloco else 0}" data-tex="{H.escape(tex, quote=True)}">{mathml(reserva, bloco)}</{tag}>'


class Montador:
    def __init__(self, raiz):
        self.raiz = raiz
        self.n = 0
        self.ids = {}
        self.cache = {}

    def uri(self, src, largura):
        if re.match(r'[a-z]+:', src):
            sys.exit(f'Imagem externa não é permitida, porque o relatório precisa abrir offline: {src}')
        caminho = os.path.normpath(os.path.join(self.raiz, src))
        if not os.path.isfile(caminho):
            sys.exit(f'Imagem não encontrada: {src}')
        chave = (caminho, largura)
        if chave not in self.cache:
            self.cache[chave] = img_uri(caminho, largura)
        return self.cache[chave]

    def numero(self, a):
        self.n += 1
        if a.get('id'):
            self.ids[a['id']] = self.n
        return self.n

    def fig(self, m):
        a = attrs(m.group(1))
        n = self.numero(a)
        cap = a.get('cap', '')
        if not cap:
            sys.exit(f'Figura sem legenda: {a.get("src")}')
        largura = int(a.get('largura', 2400))
        return (f'<figure class="fig {a.get("classe", "")}"><button class="zoom" type="button" aria-label="Ampliar figura {n}">'
                f'<img loading="lazy" src="{self.uri(a["src"], largura)}" alt="{attr_html(a.get("alt", cap))}"></button>'
                f'<figcaption><b>Figura {n}</b> · {cap}</figcaption></figure>')

    def abas(self, m):
        a = attrs(m.group(1))
        n = self.numero(a)
        abas = [attrs(x) for x in re.findall(r'<aba\b([^>]*)>\s*</aba>', m.group(2))]
        if len(abas) < 2:
            sys.exit('<abas-fig> precisa de pelo menos duas <aba>.')
        tabs, panes = '', ''
        for i, x in enumerate(abas):
            on = i == 0
            rot = H.escape(x['rotulo'])
            tabs += f'<button type="button" class="lm-tab chip{" lm-tab--on" if on else ""}" data-t="{i}" aria-pressed="{"true" if on else "false"}">{rot}</button>'
            panes += (f'<button class="zoom pane" type="button" data-p="{i}" aria-label="Ampliar a figura {n} com {attr_html(x["rotulo"])}"{"" if on else " hidden"}>'
                      f'<img loading="lazy" src="{self.uri(x["src"], int(x.get("largura", 2400)))}" alt="{attr_html(x.get("alt", a.get("cap", "") + " " + x["rotulo"]))}"></button>')
        return (f'<figure class="fig fig-abas"><div class="lm-tabs" role="group" aria-label="{attr_html(a.get("rotulo", "Variante"))}">{tabs}</div>{panes}'
                f'<figcaption><b>Figura {n}</b> · {a.get("cap", "")}</figcaption></figure>')

    @staticmethod
    def barras(m):
        a = attrs(m.group(1))
        itens = [attrs(x) for x in re.findall(r'<barra\b([^>]*)>\s*</barra>', m.group(2))]
        vals = [float(x['valor']) for x in itens]
        if not vals or min(vals) < 0:
            sys.exit('<barras> precisa de valores não negativos.')
        maior = max(vals) or 1
        casas = int(a.get('casas', 4))
        saida = ''
        for x, v in zip(itens, vals):
            rot = H.escape(x['rotulo'])
            dest = x['rotulo'] == a.get('destaque')
            cls_r = ' class="r"' if dest else ''
            txt = x.get('texto') or f'{v:,.{casas}f}'.replace(',', ' ').replace('.', ',').replace(' ', '.') + (f' {a["unidade"]}' if a.get('unidade') else '')
            saida += (f'<div class="bl">{rot}</div><div class="lm-track" title="{rot}: {txt}"><i{cls_r} style="width:{v / maior * 100:.1f}%"></i></div>'
                      f'<div class="bv{" r" if dest else ""}">{txt}</div>')
        return f'<div class="bars">{saida}</div>'


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    entrada, saida = sys.argv[1:3]
    with open(entrada, encoding='utf-8') as f:
        c = f.read()

    cab = re.search(r'<relatorio\b([^>]*)>(?:\s*</relatorio>)?', c)
    if not cab:
        sys.exit('Falta a marcação <relatorio titulo="..."> no início do conteúdo.')
    meta = attrs(cab.group(1))
    if not meta.get('titulo'):
        sys.exit('A marcação <relatorio> precisa do atributo titulo.')
    c = c.replace(cab.group(0), '', 1)

    mont = Montador(os.path.dirname(os.path.abspath(entrada)))
    c = re.sub(r'<eq>(.*?)</eq>', lambda m: equacao(H.unescape(m.group(1))), c, flags=re.S)
    c = re.sub(r'<eqi>(.*?)</eqi>', lambda m: equacao(H.unescape(m.group(1)), False), c, flags=re.S)
    n_eq = c.count('class="tex"')
    c = re.sub(r'<barras\b([^>]*)>(.*?)</barras>', Montador.barras, c, flags=re.S)
    # Figuras e abas passam juntas, para a numeração seguir a ordem de leitura.
    padrao = re.compile(r'<fig\b([^>]*)>\s*</fig>|<abas-fig\b([^>]*)>(.*?)</abas-fig>', re.S)

    def figuras(m):
        if m.group(3) is not None:
            return mont.abas(re.match(r'<abas-fig\b([^>]*)>(.*?)</abas-fig>', m.group(0), re.S))
        return mont.fig(m)

    c = padrao.sub(figuras, c)
    faltando = []

    def ref(m):
        if m.group(1) not in mont.ids:
            faltando.append(m.group(1))
            return m.group(0)
        return str(mont.ids[m.group(1)])

    c = re.sub(r'\[\[fig:([^\]]+)\]\]', ref, c)
    if faltando:
        sys.exit(f'Referência a figura inexistente: {", ".join(faltando)}')

    secoes = re.findall(r'<section\b([^>]*)>', c)
    nav = ''
    for s in secoes:
        a = attrs(s)
        if a.get('id') and a.get('data-nav'):
            nav += f'<a href="#{H.escape(a["id"])}">{H.escape(a["data-nav"])}</a>'
    if not nav:
        print('AVISO: nenhuma seção com id e data-nav; o índice lateral ficou vazio.')

    def asset_txt(nome):
        with open(os.path.join(ASSETS, nome), encoding='utf-8') as f:
            return f.read()

    with open(os.path.join(ASSETS, 'fundo-institucional.jpg'), 'rb') as f:
        fundo = 'data:image/jpeg;base64,' + b64(f.read())
    logos = ''.join(f'<img src="{logo_uri(n.strip())}" alt="{n.strip().upper() if n.strip() != "lmest" else "LMEst"}">' for n in meta.get('logos', 'ufu,lmest').split(','))
    rodape = meta.get('rodape', 'LMEst-UFU · Laboratório de Mecânica de Estruturas “Prof. José Eduardo Tannús Reis” · Universidade Federal de Uberlândia')
    sobre = f'<p class="eyebrow">{H.escape(meta["sobretitulo"])}</p>' if meta.get('sobretitulo') else ''
    sub = f'<p class="sub">{H.escape(meta["subtitulo"])}</p>' if meta.get('subtitulo') else ''
    titulo = H.escape(meta['titulo'])
    # KaTeX (CSS com as fontes embutidas e JS) só entra quando há equações, para não pesar à toa.
    katex_css = f'<style>{asset_txt("katex/katex.css")}</style>' if n_eq else ''
    katex_js = f'<script>{asset_txt("katex/katex.min.js")}</script>' if n_eq else ''

    pagina = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo} · LMEst-UFU</title>
{katex_css}<style>{font_faces()}
{asset_txt('report.css')}</style></head><body>
<header class="cover" style="background-image:url({fundo})">
<div class="plate">{logos}</div>
{sobre}
<h1>{titulo}</h1>
{sub}
</header>
<div class="layout"><nav aria-label="Seções do relatório">{nav}</nav><main>{c}</main></div>
<footer>{H.escape(rodape)}</footer>
<dialog aria-label="Figura ampliada"><img alt=""></dialog>
{katex_js}<script>{asset_txt('report.js')}</script></body></html>'''
    with open(saida, 'w', encoding='utf-8') as f:
        f.write(pagina)
    externos = re.findall(r'(?:src|href)="(https?://[^"]+)"', re.sub(r'<a\b[^>]*>', '', pagina))
    print(f'{os.path.abspath(saida)} · {len(pagina) / 1e6:.1f} MB · {mont.n} figuras · {n_eq} equações · {nav.count("<a ")} seções')
    if externos:
        print('AVISO: recursos externos encontrados:', externos[:5])


if __name__ == '__main__':
    main()

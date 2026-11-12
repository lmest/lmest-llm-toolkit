#!/usr/bin/env python3
"""Gera a apresentação em PPTX editável (16:9), com o texto em caixas de texto.

Uso: python3 gerar_pptx.py PASTA [SAIDA.pptx]

Converte cada filho fixado (position:absolute) da <section>:
  <div> pintada -> retângulo (arredondado se tiver border-radius)
  <h1-h3>, <p>, <ul>, <ol> -> caixa de texto (Carlito vira Calibri), com negrito, itálico,
                              cor, links, espaçamento de letras e caixa alta
  <img> -> imagem (object-fit contain/cover respeitado; SVG usa o .png de mesmo nome,
           ou é convertido com rsvg-convert ou inkscape)
  <svg> inline -> imagem convertida por rsvg-convert ou inkscape
  <table> -> tabela nativa
  <hr> -> linha
  <aside> -> notas do apresentador
<x-embed> (animação) não existe em PPTX: o script para com erro.
1 px do palco = 0,5 pt (1920 px = 13,333 pol).
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # funciona também com python3 -I
from lmest_comum import slug_arquivo, Projeto, estilo, ler, px

try:
    from bs4 import BeautifulSoup, NavigableString, Tag
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.dml import MSO_LINE
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
    from pptx.oxml.ns import qn
    from pptx.util import Emu, Pt
    from PIL import Image
except ImportError as e:
    sys.exit(f'Falta um pacote ({e.name}). Instale com: pip install python-pptx beautifulsoup4 Pillow')

EMU = 6350  # por px
TEXTO = {'h1', 'h2', 'h3', 'p', 'ul', 'ol'}
NOMES = {'white': 'ffffff', 'black': '000000', 'red': 'ff0000', 'blue': '0000ff', 'transparent': None}


def e(v):
    return Emu(int(round(v * EMU)))


def cor(v):
    """'#abc', '#aabbcc', '#aabbccdd', 'rgb(…)', 'rgba(…)' -> ('aabbcc', alfa 0-1) ou (None, 0)."""
    if not v:
        return None, 0
    v = v.strip().lower()
    if v in NOMES:
        return NOMES[v], (1 if NOMES[v] else 0)
    m = re.fullmatch(r'#([0-9a-f]{3,8})', v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = ''.join(c * 2 for c in h)
        alfa = int(h[6:8], 16) / 255 if len(h) == 8 else 1
        return h[:6], alfa
    m = re.fullmatch(r'rgba?\(([^)]*)\)', v)
    if m:
        p = [x.strip() for x in re.split(r'[,\s/]+', m.group(1)) if x.strip()]
        rgb = ''.join(f'{int(float(x)):02x}' for x in p[:3])
        alfa = float(p[3].rstrip('%')) / (100 if p[3].endswith('%') else 1) if len(p) > 3 else 1
        return rgb, alfa
    return None, 0


def preencher(fill, valor):
    h, alfa = cor(valor)
    if not h or alfa == 0:
        fill.background()
        return
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string(h.upper())
    if alfa < 1:
        srgb = fill._xPr.find(qn('a:solidFill')).find(qn('a:srgbClr'))
        a = srgb.makeelement(qn('a:alpha'), {'val': str(int(alfa * 100000))})
        srgb.append(a)


def borda(st):
    b = st.get('border')
    if not b or b.strip() == 'none':
        return None
    larg = re.search(r'([\d.]+)px', b)
    c = re.search(r'(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))', b)
    return (float(larg.group(1)) if larg else 1.0, c.group(1) if c else '#000000')


def caixa(st, W=1920, H=1080):
    left = px(st.get('left'), W)
    top = px(st.get('top'), H)
    w = px(st.get('width'), W)
    h = px(st.get('height'), H)
    if left is None and st.get('right') is not None and w is not None:
        left = W - px(st.get('right'), W) - w
    if top is None and st.get('bottom') is not None and h is not None:
        top = H - px(st.get('bottom'), H) - h
    if 'translatex(-50%)' in (st.get('transform') or '').replace(' ', '').lower() and left is not None and w:
        left -= w / 2
    return left, top, w, h


def raio(st, w, h):
    r = px((st.get('border-radius') or '0').split()[0], min(w, h), 0) or 0
    return min(r / min(w, h), 0.5) if r and min(w, h) > 0 else 0


def forma(slide, left, top, w, h, st):
    r = raio(st, w, h)
    tipo = MSO_SHAPE.ROUNDED_RECTANGLE if r else MSO_SHAPE.RECTANGLE
    if st.get('border-radius', '').strip() == '50%' and abs(w - h) < 1:
        tipo, r = MSO_SHAPE.OVAL, 0
    s = slide.shapes.add_shape(tipo, e(left), e(top), e(w), e(h))
    if r:
        s.adjustments[0] = r
    preencher(s.fill, st.get('background') or st.get('background-color'))
    b = borda(st)
    if b:
        s.line.width = Pt(b[0] * 0.5)
        hb, _ = cor(b[1])
        s.line.color.rgb = RGBColor.from_string((hb or '000000').upper())
        tipo_borda = (st.get('border') or '')
        if 'dashed' in tipo_borda:
            s.line.dash_style = MSO_LINE.DASH
        elif 'dotted' in tipo_borda:
            s.line.dash_style = MSO_LINE.ROUND_DOT
    else:
        s.line.fill.background()
    estilo_xml = s._element.find(qn('p:style'))
    if estilo_xml is not None:  # sem o estilo padrão: nada de sombra nem cor de tema
        s._element.remove(estilo_xml)
    sombra(s, st.get('box-shadow'))
    op = st.get('opacity')
    if op and float(op) < 1 and s.fill.type is not None:
        try:
            srgb = s.fill._xPr.find(qn('a:solidFill')).find(qn('a:srgbClr'))
            srgb.append(srgb.makeelement(qn('a:alpha'), {'val': str(int(float(op) * 100000))}))
        except AttributeError:
            pass
    return s


def sombra(s, valor):
    """box-shadow 'X Y BLUR COR' -> sombra externa do PowerPoint (a:outerShdw)."""
    if not valor or 'inset' in valor:
        return
    m = re.match(r'\s*(-?[\d.]+)(?:px)?\s+(-?[\d.]+)(?:px)?\s+([\d.]+)(?:px)?(?:\s+-?[\d.]+px)?\s+(.+)$', valor)
    if not m:
        return
    import math
    x, y, blur = float(m.group(1)), float(m.group(2)), float(m.group(3))
    h, alfa = cor(m.group(4))
    if not h or not alfa:
        return
    spPr = s._element.spPr
    velho = spPr.find(qn('a:effectLst'))
    if velho is not None:
        spPr.remove(velho)
    efeitos = spPr.makeelement(qn('a:effectLst'), {})
    dist = math.hypot(x, y)
    direcao = int((math.degrees(math.atan2(y, x)) % 360) * 60000)
    shd = efeitos.makeelement(qn('a:outerShdw'), {'blurRad': str(int(blur * EMU)), 'dist': str(int(dist * EMU)),
                                                 'dir': str(direcao), 'algn': 't', 'rotWithShape': '0'})
    clr = shd.makeelement(qn('a:srgbClr'), {'val': h.upper()})
    clr.append(clr.makeelement(qn('a:alpha'), {'val': str(int(alfa * 100000))}))
    shd.append(clr)
    efeitos.append(shd)
    # effectLst vem depois de fill e ln no spPr
    ln = spPr.find(qn('a:ln'))
    if ln is not None:
        ln.addnext(efeitos)
    else:
        spPr.append(efeitos)


# ---------- texto ----------

def run_props(run, fmt):
    f = run.font
    f.name = 'Calibri'
    f.size = Pt(fmt['fs'] * 0.5)
    f.bold = fmt['bold']
    f.italic = fmt['italic']
    if fmt.get('underline'):
        f.underline = True
    h, _ = cor(fmt['color'])
    if h:
        f.color.rgb = RGBColor.from_string(h.upper())
    if fmt.get('spc'):
        run._r.get_or_add_rPr().set('spc', str(int(fmt['spc'] * 50)))  # px -> centésimos de pt
    if fmt.get('href'):
        run.hyperlink.address = fmt['href']


def coletar_runs(no, fmt, saida, caixa_alta):
    """Lista de parágrafos; cada um, lista de (texto, fmt)."""
    for filho in no.children:
        if isinstance(filho, NavigableString):
            t = re.sub(r'\s+', ' ', str(filho))
            if caixa_alta:
                t = t.upper()
            if t:
                saida[-1].append((t, fmt))
            continue
        if not isinstance(filho, Tag):
            continue
        n = filho.name
        if n == 'br':
            saida.append([])
            continue
        f2 = dict(fmt)
        st = estilo(filho.get('style'))
        if n in ('b', 'strong'):
            f2['bold'] = True
        elif n in ('i', 'em'):
            f2['italic'] = True
        elif n == 'u':
            f2['underline'] = True
        elif n == 'a':
            f2['href'] = filho.get('href')
            f2['underline'] = True
            f2['color'] = st.get('color', '#17689b')
        if st.get('color'):
            f2['color'] = st['color']
        if st.get('font-weight') in ('600', '700', '800', '900', 'bold'):
            f2['bold'] = True
        if st.get('font-style') == 'italic':
            f2['italic'] = True
        coletar_runs(filho, f2, saida, caixa_alta)


def texto(slide, el, st):
    left, top, w, h = caixa(st)
    fs = px(st.get('font-size'), padrao=32 if el.name == 'p' else {'h1': 96, 'h2': 64, 'h3': 44}.get(el.name, 32))
    lh_txt = st.get('line-height', '')
    if re.fullmatch(r'[\d.]+', lh_txt):
        lh = float(lh_txt)
    elif lh_txt.endswith('px'):
        lh = px(lh_txt) / fs
    else:
        lh = {'h1': 1.1, 'h2': 1.15, 'h3': 1.2}.get(el.name, 1.2 if el.name == 'p' and fs >= 40 else 1.3)
    negrito = el.name in ('h1', 'h2', 'h3') or st.get('font-weight') in ('600', '700', '800', '900', 'bold')
    fmt = {'fs': fs, 'bold': negrito, 'italic': st.get('font-style') == 'italic',
           'color': st.get('color', '#1b2b3a'), 'spc': px(st.get('letter-spacing'), padrao=0) or 0}
    caixa_alta = st.get('text-transform') == 'uppercase'
    paragrafos = []  # (runs, nível de lista ou None, marcador)
    if el.name in ('ul', 'ol'):
        for k, li in enumerate(el.find_all('li', recursive=False), 1):
            pars = [[]]
            coletar_runs(li, fmt, pars, caixa_alta)
            for j, runs in enumerate(pars):
                paragrafos.append((runs, '•' if el.name == 'ul' else f'{k}.', j == 0))
    else:
        pars = [[]]
        coletar_runs(el, fmt, pars, caixa_alta)
        paragrafos = [(r, None, False) for r in pars]
    if h is None:
        n = sum(max(1, int(sum(len(t) for t, _ in r) * fs * 0.5 / max(w, 1)) + 1) for r, _, _ in paragrafos)
        h = n * fs * lh
    p = [px(x, padrao=0) or 0 for x in (st.get('padding') or '0').split()][:4]
    pad = {1: lambda a: [a[0]] * 4, 2: lambda a: a * 2, 3: lambda a: a + [a[1]], 4: lambda a: a}[len(p)](p)
    fundo = st.get('background') or st.get('background-color')
    if fundo or borda(st):
        s = forma(slide, left, top, w, h, st)
    else:
        s = slide.shapes.add_textbox(e(left), e(top), e(w), e(h))
    tf = s.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE if (fundo and st.get('height')) else MSO_ANCHOR.TOP
    tf.margin_top, tf.margin_right, tf.margin_bottom, tf.margin_left = (e(pad[0]), e(pad[1]), e(pad[2]), e(pad[3]))
    alinh = {'center': PP_ALIGN.CENTER, 'right': PP_ALIGN.RIGHT, 'justify': PP_ALIGN.JUSTIFY}.get(st.get('text-align'), PP_ALIGN.LEFT)
    primeiro = True
    for runs, marcador, inicio in paragrafos:
        par = tf.paragraphs[0] if primeiro else tf.add_paragraph()
        primeiro = False
        par.alignment = alinh
        par.line_spacing = round(lh / 1.2, 2)  # 1,0 no PowerPoint ≈ 1,2 da fonte
        if marcador:
            pPr = par._p.get_or_add_pPr()
            ind = int(fs * 1.1 * EMU)
            pPr.set('marL', str(ind))
            pPr.set('indent', str(-ind if inicio else 0))
            if inicio:
                bu = pPr.makeelement(qn('a:buChar') if marcador == '•' else qn('a:buAutoNum'),
                                     {'char': '•'} if marcador == '•' else {'type': 'arabicPeriod'})
                pPr.append(bu)
            else:
                pPr.append(pPr.makeelement(qn('a:buNone'), {}))
            par.space_before = Pt(fs * 0.25)
        if not runs:
            r = par.add_run()
            r.text = ''
            run_props(r, fmt)
        for t, f in runs:
            r = par.add_run()
            r.text = t
            run_props(r, f)
    # Tira espaços nas pontas de cada parágrafo.
    for par in tf.paragraphs:
        if par.runs:
            par.runs[0].text = par.runs[0].text.lstrip()
            par.runs[-1].text = par.runs[-1].text.rstrip()


# ---------- imagens ----------

def svg_para_png(svg_bytes, largura):
    for prog in ('rsvg-convert', 'inkscape'):
        if shutil.which(prog):
            with tempfile.TemporaryDirectory() as tmp:
                a, b = os.path.join(tmp, 'a.svg'), os.path.join(tmp, 'b.png')
                with open(a, 'wb') as f:
                    f.write(svg_bytes)
                largura = str(int(max(largura, 64) * 2))
                cmd = ([prog, '-w', largura, '-o', b, a] if prog == 'rsvg-convert'
                       else [prog, a, '--export-type=png', f'--export-filename={b}', '-w', largura])
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with open(b, 'rb') as f:
                    return f.read()
    sys.exit('Para converter SVG em PPTX é preciso rsvg-convert (librsvg) ou inkscape, '
             'ou um .png de mesmo nome ao lado de cada .svg.')


def imagem(slide, dados, left, top, w, h, ajuste):
    im = Image.open(io.BytesIO(dados))
    iw, ih = im.size
    if ajuste == 'contain':
        k = min(w / iw, h / ih)
        nw, nh = iw * k, ih * k
        return slide.shapes.add_picture(io.BytesIO(dados), e(left + (w - nw) / 2), e(top + (h - nh) / 2), e(nw), e(nh))
    pic = slide.shapes.add_picture(io.BytesIO(dados), e(left), e(top), e(w), e(h))
    if ajuste == 'cover':
        k = max(w / iw, h / ih)
        sobra_x = (iw * k - w) / (iw * k) / 2
        sobra_y = (ih * k - h) / (ih * k) / 2
        pic.crop_left = pic.crop_right = sobra_x
        pic.crop_top = pic.crop_bottom = sobra_y
    return pic


def bordas_celula(cel, cabecalho):
    """Filetes do Design System: horizontais #CBCBCB (cabeçalho com base #192631), sem verticais."""
    tcPr = cel._tc.get_or_add_tcPr()
    for lado in ('a:lnL', 'a:lnR', 'a:lnT', 'a:lnB'):
        velho = tcPr.find(qn(lado))
        if velho is not None:
            tcPr.remove(velho)
    for lado, cor_hex, larg in (('a:lnL', None, 0), ('a:lnR', None, 0), ('a:lnT', 'CBCBCB', 1),
                                ('a:lnB', '192631' if cabecalho else 'CBCBCB', 2 if cabecalho else 1)):
        ln = tcPr.makeelement(qn(lado), {'w': str(int(larg * EMU))})
        if cor_hex:
            sf = ln.makeelement(qn('a:solidFill'), {})
            sf.append(sf.makeelement(qn('a:srgbClr'), {'val': cor_hex}))
            ln.append(sf)
        else:
            ln.append(ln.makeelement(qn('a:noFill'), {}))
        tcPr.append(ln)
    # a ordem exigida pelo esquema: lnL, lnR, lnT, lnB antes do preenchimento
    for filho in [f for f in tcPr if f.tag not in (qn('a:lnL'), qn('a:lnR'), qn('a:lnT'), qn('a:lnB'))]:
        tcPr.remove(filho)
        tcPr.append(filho)


def tabela(slide, el, st):
    left, top, w, _ = caixa(st)
    linhas = el.find_all('tr')
    if not linhas:
        return
    ncol = max(len(tr.find_all(['td', 'th'])) for tr in linhas)
    fs = px(st.get('font-size'), padrao=26)
    altura = len(linhas) * fs * 2.1
    gt = slide.shapes.add_table(len(linhas), ncol, e(left), e(top), e(w), e(altura))
    tb = gt.table
    tbl_pr = gt._element.graphic.graphicData.tbl.tblPr
    for attr in ('bandRow', 'firstRow'):
        tbl_pr.set(attr, '0')
    estilo_id = tbl_pr.find(qn('a:tableStyleId'))
    if estilo_id is not None:
        estilo_id.text = '{5940675A-B579-460E-94D1-54222C63F5DA}'  # "Sem estilo, grade da tabela"
    primeira = linhas[0].find_all(['td', 'th'])
    for j, c in enumerate(primeira):
        pct = px(estilo(c.get('style')).get('width'), 100)
        if pct:
            tb.columns[j].width = e(w * pct / 100)
    for i, tr in enumerate(linhas):
        fundo_linha = estilo(tr.get('style')).get('background')
        tb.rows[i].height = e(fs * 2.1)
        for j, c in enumerate(tr.find_all(['td', 'th'])):
            cel = tb.cell(i, j)
            sc = estilo(c.get('style'))
            if fundo_linha:
                preencher(cel.fill, fundo_linha)
            else:
                cel.fill.background()
            fmt = {'fs': px(sc.get('font-size'), padrao=fs), 'bold': c.name == 'th' or sc.get('font-weight') in ('700', 'bold'),
                   'italic': False, 'color': sc.get('color') or st.get('color', '#1b2b3a')}
            pars = [[]]
            coletar_runs(c, fmt, pars, False)
            tf = cel.text_frame
            tf.word_wrap = True
            alinh = {'center': PP_ALIGN.CENTER, 'right': PP_ALIGN.RIGHT}.get(sc.get('text-align'), PP_ALIGN.LEFT)
            for k, runs in enumerate(pars):
                par = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
                par.alignment = alinh
                for t, f in runs:
                    r = par.add_run()
                    r.text = t.strip() if len(runs) == 1 else t
                    run_props(r, f)
            bordas_celula(cel, i == 0 and c.name == 'th')
            cel.vertical_anchor = MSO_ANCHOR.MIDDLE
            cel.margin_left = cel.margin_right = e(fs * 0.6)
            cel.margin_top = cel.margin_bottom = e(fs * 0.35)


def converter_slide(prs, prj, sid, html, avisos):
    sopa = BeautifulSoup(html, 'html.parser')
    sec = sopa.find('section')
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    preencher(slide.background.fill, estilo(sec.get('style')).get('background') or '#ffffff')
    for el in sec.children:
        if not isinstance(el, Tag):
            continue
        st = estilo(el.get('style'))
        if el.name == 'aside':
            slide.notes_slide.notes_text_frame.text = re.sub(r'\s+', ' ', el.get_text()).strip()
            continue
        if el.name == 'x-embed':
            sys.exit(f'[{sid}] tem animação (<x-embed>): PPTX não leva animações. Gere sem animações.')
        if el.name == 'svg':
            ws = px(el.get('width'), padrao=None) or px(st.get('width'))
            hs = px(el.get('height'), padrao=None) or px(st.get('height'))
            left, top, w, h = caixa(st)
            if None in (left, top):
                avisos.append(f'[{sid}] <svg> sem left/top: ignorado.')
                continue
            dados = svg_para_png(str(el).encode(), w or ws)
            imagem(slide, dados, left, top, w or ws, h or hs, 'contain')
            continue
        left, top, w, h = caixa(st)
        if left is None or top is None or w is None:
            avisos.append(f'[{sid}] <{el.name}> sem posição fixa: ignorado no PPTX.')
            continue
        if el.name == 'img':
            src = el.get('src', '')
            caminho = os.path.join(prj.pasta, src)
            if src.lower().endswith('.svg'):
                png = caminho[:-4] + '.png'
                if os.path.isfile(png):
                    dados = open(png, 'rb').read()
                else:
                    dados = svg_para_png(open(caminho, 'rb').read(), w)
            elif os.path.isfile(caminho):
                dados = open(caminho, 'rb').read()
            else:
                avisos.append(f'[{sid}] imagem não encontrada: {src}')
                continue
            pic = imagem(slide, dados, left, top, w, h or w, st.get('object-fit', 'fill'))
            r = raio(st, w, h or w)
            if r:
                avisos.append(f'[{sid}] cantos arredondados de imagem não são aplicados no PPTX.')
            del pic
        elif el.name == 'div':
            if h is None:
                avisos.append(f'[{sid}] <div> sem height: ignorada.')
                continue
            if st.get('background') or st.get('background-color') or borda(st):
                forma(slide, left, top, w, h, st)
            if any(isinstance(c, Tag) for c in el.children):
                avisos.append(f'[{sid}] <div> com filhos: o conteúdo interno não foi convertido. Fixe cada filho na <section>.')
        elif el.name in TEXTO:
            texto(slide, el, st)
        elif el.name == 'table':
            tabela(slide, el, st)
        elif el.name == 'hr':
            b = borda({'border': st.get('border-top', st.get('border', '2px solid #d6dee6'))}) or (2, '#d6dee6')
            ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, e(left), e(top), e(left + w), e(top))
            ln.line.width = Pt(b[0] * 0.5)
            ln.line.color.rgb = RGBColor.from_string((cor(b[1])[0] or 'd6dee6').upper())
        else:
            avisos.append(f'[{sid}] <{el.name}> não convertido.')


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    prj = Projeto(sys.argv[1])
    saida = os.path.abspath(sys.argv[2]) if len(sys.argv) == 3 else os.path.join(
        prj.pasta, 'saida', slug_arquivo(prj.deck.get('title')) + '.pptx')
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    avisos = []
    for sid in prj.ordem():
        converter_slide(prs, prj, sid, ler(prj.arquivo(sid)), avisos)
    prs.core_properties.title = prj.deck.get('title', '')
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    prs.save(saida)
    for a in avisos:
        print('AVISO', a)
    print(f'PPTX gerado: {saida} ({len(prj.ordem())} slides)')


if __name__ == '__main__':
    main()

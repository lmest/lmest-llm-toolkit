#!/usr/bin/env python3
"""Gera (ou regenera) a capa e o agradecimento a partir de projeto.json.

Uso: python3 montar_fixos.py PASTA

Escreve slides/capa.html e slides/agradecimento.html e garante que "capa" seja o
primeiro id de order e "agradecimento" o último. As notas do apresentador que já
existirem nos dois slides são mantidas. Os textos vazios em projeto.json são omitidos.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # funciona também com python3 -I
from lmest_comum import FONTE, Projeto, esc, gravar, ler, linhas_texto

FUNDO = 'lmest/fundos/fundo-institucional.jpg'

# Logos do agradecimento: posição e tamanho em px no palco de 1920×1080 (modelo slide_final.pptx).
LOGOS_FIM = [
    ('parceiros/petrobras.png', 'Petrobras', 904, 250, 216, 42),
    ('parceiros/aneel.png', 'ANEEL', 1161, 241, 211, 59),
    ('parceiros/cpfl.png', 'CPFL Energia', 1412, 222, 130, 96),
    ('parceiros/ceran.png', 'Ceran', 1582, 234, 172, 73),
    ('parceiros/enercan.png', 'Enercan', 905, 378, 173, 61),
    ('parceiros/baesa.png', 'BAESA', 1119, 365, 120, 88),
    ('parceiros/foz-do-chapeco.png', 'Foz do Chapecó', 1280, 386, 216, 45),
    ('parceiros/embraer.png', 'Embraer', 1537, 386, 216, 45),
    ('parceiros/bayer.png', 'Bayer', 982, 497, 100, 100),
    ('parceiros/csc.png', 'CSC Energia', 1200, 514, 151, 66),
    ('parceiros/dynamic.png', 'Dynamic Services', 1469, 523, 208, 48),
    ('logos/cnpq.png', 'CNPq', 951, 649, 171, 73),
    ('logos/fapemig.png', 'FAPEMIG', 1210, 635, 124, 101),
    ('logos/capes.png', 'CAPES', 1422, 634, 122, 102),
    ('logos/inct.png', 'INCT', 1632, 628, 75, 114),
    ('logos/ufu-preto.png', 'UFU', 928, 770, 108, 107),
    ('logos/femec.png', 'FEMEC', 1099, 790, 171, 67),
    ('logos/pos-graduacao.png', 'Pós-Graduação em Engenharia Mecânica', 1334, 804, 216, 38),
    ('logos/lmest-grade.png', 'LMEst', 1614, 774, 117, 98),
]


def inline(t):
    """Escapa o texto e converte *termo* em itálico (termos estrangeiros na capa e no agradecimento)."""
    return re.sub(r'\*([^*]+)\*', r'<i>\1</i>', esc(t))


def notas(caminho, padrao):
    if os.path.exists(caminho):
        m = re.search(r'<aside>(.*?)</aside>', ler(caminho), re.S)
        if m and m.group(1).strip():
            return m.group(1).strip()
    return esc(padrao)


def p(top, left, width, fs, cor, texto, extra=''):
    return (f'  <p style="position:absolute; top:{round(top)}px; left:{left}px; width:{width}px; '
            f'font-family:{FONTE}; font-size:{fs}px; {extra}color:{cor}">{texto}</p>\n')


def capa(proj, nota):
    pal = proj.get('palestrante', {})
    blocos = []  # (altura, html_factory)

    def bloco(texto, fs, lh, largura, cor, extra='', negrito=False, caixa=False, gap=0, tag='p'):
        if not texto:
            return
        n = linhas_texto(texto.replace('*', ''), largura, fs, negrito, caixa, 6 if caixa else 0)
        altura = n * fs * lh
        blocos.append((altura, gap, lambda top: (
            f'  <{tag} style="position:absolute; top:{round(top)}px; left:89px; width:{largura}px; '
            f'font-family:{FONTE}; font-size:{fs}px; line-height:{lh}; {extra}color:{cor}">{inline(texto)}</{tag}>\n')))

    bloco(proj.get('sobretitulo'), 26, 1.2, 1300, '#49a9e1',
          'font-weight:700; letter-spacing:6px; text-transform:uppercase; ', True, True)
    bloco(proj.get('titulo'), 88, 1.1, 1300, '#ffffff', 'font-weight:700; ', True, gap=32, tag='h1')
    bloco(proj.get('subtitulo'), 32, 1.4, 1200, '#b4d0dc', gap=32)
    bloco(pal.get('nome'), 34, 1.2, 1300, '#ffffff', 'font-weight:700; ', True, gap=48)
    bloco(pal.get('cargo'), 26, 1.3, 1500, '#b4d0dc', gap=8)
    bloco(pal.get('afiliacao'), 26, 1.3, 1600, '#b4d0dc', gap=4)
    bloco(proj.get('data_local'), 26, 1.3, 1500, '#b4d0dc', gap=8)

    total = sum(a + (g if i else 0) for i, (a, g, _) in enumerate(blocos))
    top = max(272, 144 + (960 - 144 - total) / 2)
    corpo = ''
    for i, (altura, gap, fazer) in enumerate(blocos):
        if i:
            top += gap
        corpo += fazer(top)
        top += altura
    return (
        '<section id="capa" data-transition="fade" style="background:#152536">\n'
        f'  <img src="{FUNDO}" alt="" style="position:absolute; top:0; left:0; width:1920px; height:1080px; object-fit:cover">\n'
        '  <div style="position:absolute; top:72px; left:1451px; width:380px; height:152px; background:#ffffff; border-radius:17px"></div>\n'
        '  <img src="lmest/logos/ufu.png" alt="UFU" style="position:absolute; top:102px; left:1476px; width:92px; height:92px; object-fit:contain">\n'
        '  <img src="lmest/logos/lmest.png" alt="LMEst" style="position:absolute; top:104px; left:1592px; width:113px; height:88px; object-fit:contain">\n'
        '  <img src="lmest/logos/inct.png" alt="INCT" style="position:absolute; top:92px; left:1729px; width:76px; height:112px; object-fit:contain">\n'
        f'{corpo}'
        f'  <aside>{nota}</aside>\n'
        '</section>\n')


def agradecimento(proj, nota):
    pal = proj.get('palestrante', {})
    h = [
        '<section id="agradecimento" data-transition="fade" style="background:#152536">\n',
        f'  <img src="{FUNDO}" alt="" style="position:absolute; top:0; left:0; width:1920px; height:1080px; object-fit:cover">\n',
        p(187, 89, 720, 26, '#49a9e1', 'Agradecimentos', 'font-weight:700; letter-spacing:6px; text-transform:uppercase; line-height:1.2; '),
        p(245, 89, 720, 96, '#ffffff', 'Obrigado', 'font-weight:700; line-height:1.2; '),
        p(400, 89, 720, 38, '#ffffff', inline(pal.get('nome', '')), 'font-weight:700; line-height:1.2; '),
    ]
    if pal.get('cargo'):
        h.append(p(455, 89, 720, 28, '#b4d0dc', inline(pal['cargo']), 'line-height:1.2; '))
    linhas = []
    if pal.get('telefone'):
        linhas.append(('lmest/icones/whatsapp.png', 'WhatsApp', pal['telefone']))
    for e in pal.get('emails', []) or []:
        if e:
            linhas.append(('lmest/icones/email-nevoa.png', 'E-mail', e))
    y = 556
    for icone, alt, texto in linhas[:4]:
        h.append(f'  <img src="{icone}" alt="{alt}" style="position:absolute; top:{y + 3}px; left:89px; width:37px; height:37px; object-fit:contain">\n')
        h.append(p(y, 150, 662, 29, '#ffffff', esc(texto), 'line-height:1.3; '))
        y += 63
    y += 18
    h.append(f'  <img src="lmest/icones/instagram.png" alt="Instagram" style="position:absolute; top:{y}px; left:89px; width:34px; height:34px; object-fit:contain">\n')
    h.append(f'  <img src="lmest/icones/linkedin.png" alt="LinkedIn" style="position:absolute; top:{y}px; left:133px; width:34px; height:34px; object-fit:contain">\n')
    h.append(p(y + 1, 183, 300, 24, '#b4d0dc', '@lmest.ufu', 'font-style:italic; line-height:1.3; '))
    h.append('  <div style="position:absolute; top:187px; left:828px; width:1002px; height:720px; background:#ffffff; border-radius:17px"></div>\n')
    for arq, alt, x, yy, w, hh in LOGOS_FIM:
        h.append(f'  <img src="lmest/{arq}" alt="{alt}" style="position:absolute; top:{yy}px; left:{x}px; width:{w}px; height:{hh}px; object-fit:contain">\n')
    h.append(f'  <aside>{nota}</aside>\n</section>\n')
    return ''.join(h)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    prj = Projeto(sys.argv[1])
    a_capa, a_fim = prj.arquivo('capa'), prj.arquivo('agradecimento')
    gravar(a_capa, capa(prj.proj, notas(a_capa, 'Apresente-se e diga em uma frase o que o público vai levar desta apresentação.')))
    gravar(a_fim, agradecimento(prj.proj, notas(a_fim, 'Agradeça, retome em uma frase a mensagem principal e abra para perguntas.')))
    ordem = [s for s in prj.ordem() if s not in ('capa', 'agradecimento')]
    prj.deck['order'] = ['capa'] + ordem + ['agradecimento']
    prj.deck['cover'] = 'capa'
    prj.salvar_deck()
    print('Capa e agradecimento gerados. Rode numerar.py depois de mexer na ordem dos slides.')


if __name__ == '__main__':
    main()

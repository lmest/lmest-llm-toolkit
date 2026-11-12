#!/usr/bin/env python3
"""Gera a apresentação em um único arquivo HTML, que abre offline.

Uso: python3 gerar_html.py PASTA [SAIDA.html]

Imagens e a fonte Carlito vão embutidas. Cada <x-embed> vira um <iframe> isolado.
Teclas: → ↓ espaço PageDown avançam; ← ↑ PageUp voltam; Home e End; F tela cheia;
N abre as notas do apresentador em outra janela. A URL #12 abre o slide 12.
Imprimir (Ctrl+P) gera um slide por página, com as animações no estado final.
"""
import base64
import mimetypes
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # funciona também com python3 -I
from lmest_comum import slug_arquivo, ASSETS, Projeto, esc, ler, gravar

FONTES = [('Carlito-Regular', 400, 'normal'), ('Carlito-Italic', 400, 'italic'),
          ('Carlito-Bold', 700, 'normal'), ('Carlito-BoldItalic', 700, 'italic')]

# Injetado em cada minipágina: no modo de impressão, leva a animação ao estado final.
FINAL_JS = ("<script>addEventListener('message',function(e){if(e.data!=='lm-final')return;"
            "try{if(window.lmFinal){window.lmFinal();}else{var c=document.getElementById('c')||document.body.firstElementChild;"
            "c&&c.classList.add('on');}}catch(x){}setTimeout(function(){document.getAnimations().forEach(function(a){try{a.finish()}catch(x){}})},60);});</script>")

CSS = """
html,body{margin:0;height:100%;background:#0b131c;overflow:hidden}
#palco{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0}
section{position:absolute;left:0;top:0;width:1920px;height:1080px;overflow:hidden;display:none;
  font-family:Carlito,Calibri,sans-serif;color:#1b2b3a}
section.ativo{display:block;animation:lmfade .45s ease}
@keyframes lmfade{from{opacity:0}to{opacity:1}}
section aside{display:none}
section h1,section h2,section h3,section p,section ul,section ol{margin:0}
section h1,section h2,section h3{font-weight:700}
section ul,section ol{padding-left:1.1em}
section a{color:#17689b;text-decoration:underline}
section iframe{border:0;background:transparent}
section table{border-collapse:collapse}
section th,section td{padding:.35em .6em;text-align:left;border-bottom:1px solid #cbcbcb;vertical-align:middle}
section th{font-weight:700}
section img{display:block}
#contador{position:fixed;right:12px;bottom:8px;font:14px Carlito,Calibri,sans-serif;color:#7d8b99;opacity:.0;transition:opacity .3s}
body:hover #contador{opacity:.8}
@media print{
  @page{size:1920px 1080px;margin:0}
  html,body{height:auto;overflow:visible;background:#fff}
  #palco{position:static;transform:none!important;width:1920px;height:auto}
  section{display:block!important;position:relative;page-break-after:always;break-after:page;animation:none}
  #contador{display:none}
}
"""

JS = """
(function(){
var S=[].slice.call(document.querySelectorAll('#palco>section')),i=0,notas=null;
function ajustar(){var p=document.getElementById('palco'),k=Math.min(innerWidth/1920,innerHeight/1080);
  p.style.transform='translate('+((innerWidth-1920*k)/2)+'px,'+((innerHeight-1080*k)/2)+'px) scale('+k+')';}
function ir(n){n=Math.max(0,Math.min(S.length-1,n));if(S[i])S[i].classList.remove('ativo');i=n;S[i].classList.add('ativo');
  history.replaceState(null,'','#'+(i+1));document.getElementById('contador').textContent=(i+1)+' / '+S.length;atualizarNotas();}
function atualizarNotas(){if(!notas||notas.closed)return;var a=S[i].querySelector('aside'),t=S[i].getAttribute('data-titulo')||'';
  notas.document.body.innerHTML='<p style="color:#5b6b7c">Slide '+(i+1)+' de '+S.length+'</p><h2>'+t+'</h2><p>'+(a?a.innerHTML:'')+'</p>'+
  (S[i+1]?'<p style="color:#5b6b7c">A seguir: '+(S[i+1].getAttribute('data-titulo')||'')+'</p>':'');}
function abrirNotas(){notas=open('','lmnotas','width=760,height=520');if(!notas)return;
  notas.document.title='Notas do apresentador';notas.document.body.style.cssText='font:26px/1.45 Carlito,Calibri,sans-serif;margin:32px;color:#1b2b3a';atualizarNotas();}
addEventListener('keydown',function(e){var k=e.key;
  if(k==='ArrowRight'||k==='ArrowDown'||k===' '||k==='PageDown'){ir(i+1);e.preventDefault();}
  else if(k==='ArrowLeft'||k==='ArrowUp'||k==='PageUp'){ir(i-1);e.preventDefault();}
  else if(k==='Home')ir(0);else if(k==='End')ir(S.length-1);
  else if(k==='f'||k==='F'){if(document.fullscreenElement)document.exitFullscreen();else document.documentElement.requestFullscreen();}
  else if(k==='n'||k==='N')abrirNotas();});
addEventListener('click',function(e){if(e.clientX>innerWidth*0.25)ir(i+1);else ir(i-1);});
addEventListener('resize',ajustar);
addEventListener('hashchange',function(){var n=parseInt(location.hash.slice(1),10);if(!isNaN(n)&&n-1!==i)ir(n-1);});
addEventListener('beforeprint',function(){document.querySelectorAll('iframe').forEach(function(f){try{f.contentWindow.postMessage('lm-final','*')}catch(x){}});});
ajustar();var h=parseInt((location.hash||'#1').slice(1),10);ir(isNaN(h)?0:h-1);
})();
"""


def data_uri(caminho):
    tipo = mimetypes.guess_type(caminho)[0] or 'application/octet-stream'
    with open(caminho, 'rb') as f:
        return f'data:{tipo};base64,' + base64.b64encode(f.read()).decode()


def converter_slide(prj, sid, html, cache):
    html = html.strip()
    # <x-embed style="...">conteúdo</x-embed> -> <iframe sandbox srcdoc>
    def embed(m):
        st, conteudo = m.group(1), m.group(2)
        doc = conteudo + FINAL_JS
        return (f'<iframe sandbox="allow-scripts" style="{st}; border:0" '
                f'srcdoc="{esc(doc)}"></iframe>')
    html = re.sub(r'<x-embed\s+style="([^"]*)"\s*>(.*?)</x-embed>', embed, html, flags=re.S)

    def img(m):
        src = m.group(2)
        if src.startswith(('data:', 'http')):
            return m.group(0)
        caminho = os.path.join(prj.pasta, src)
        if not os.path.isfile(caminho):
            print(f'AVISO [{sid}] imagem não encontrada: {src}')
            return m.group(0)
        if caminho not in cache:
            cache[caminho] = data_uri(caminho)
        return f'{m.group(1)}{cache[caminho]}{m.group(3)}'
    html = re.sub(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', img, html)
    titulo = ''
    m = re.search(r'<h[12]\b[^>]*>(.*?)</h[12]>', html, re.S)
    if m:
        titulo = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    html = re.sub(r'<section\b', f'<section data-titulo="{esc(titulo)}"', html, count=1)
    html = re.sub(r'\s+hidden(?=[\s>])', '', html[:html.find('>') + 1]) + html[html.find('>') + 1:]
    return html


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    prj = Projeto(sys.argv[1])
    saida = os.path.abspath(sys.argv[2]) if len(sys.argv) == 3 else os.path.join(
        prj.pasta, 'saida', slug_arquivo(prj.deck.get('title')) + '.html')
    fontes = ''
    for nome, peso, estilo in FONTES:
        arq = os.path.join(ASSETS, 'fontes', nome + '.woff2')
        fontes += (f"@font-face{{font-family:'Carlito';src:url({data_uri(arq)}) format('woff2');"
                   f"font-weight:{peso};font-style:{estilo}}}\n")
    cache, slides = {}, []
    for sid in prj.ordem():
        caminho = prj.arquivo(sid)
        if not os.path.exists(caminho):
            sys.exit(f'Falta o slide {sid}. Rode validar.py.')
        slides.append(converter_slide(prj, sid, ler(caminho), cache))
    doc = ('<!DOCTYPE html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           f'<title>{esc(prj.deck.get("title", "Apresentação"))}</title>\n'
           f'<style>\n{fontes}{CSS}</style>\n</head>\n<body>\n<div id="palco">\n'
           + '\n'.join(slides) +
           f'\n</div>\n<div id="contador"></div>\n<script>{JS}</script>\n</body>\n</html>\n')
    gravar(saida, doc)
    print(f'HTML gerado: {saida} ({os.path.getsize(saida) / 1e6:.1f} MB, {len(slides)} slides)')


if __name__ == '__main__':
    main()

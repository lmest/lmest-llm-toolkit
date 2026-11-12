#!/usr/bin/env python3
"""Converte o material de entrada em uma pasta de trabalho pronta para leitura.

Uso: python3 -I extrair_material.py ENTRADA PASTA_DE_TRABALHO

ENTRADA pode ser .md, .docx, .zip, .pdf, .pptx ou uma pasta com esses arquivos.

Gera na pasta de trabalho:
  fonte.md          texto do material, com as figuras citadas no ponto em que aparecem
  figuras/          imagens originais, com nomes sem espaços (usadas no relatório)
  miniaturas/       cópias de até 1100 px, para ler sem gastar contexto
  paginas/          PDF, PPTX e DOCX: imagem de cada página ou slide, a 100 dpi, e material.pdf
  manifesto.json    lista de figuras, com tamanho, origem e miniatura
"""
import hashlib
import json
import os
import re
import shutil
import site
import subprocess
import sys
import tempfile
import unicodedata
import zipfile

try:
    from PIL import Image
except ImportError:
    sys.exit('Falta o Pillow. Instale com: pip install Pillow')

Image.MAX_IMAGE_PIXELS = 400_000_000
EXT_IMG = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff'}
EXT_DOC = {'.md', '.markdown', '.pdf', '.pptx', '.docx'}
MIN_LADO = 120  # imagens menores costumam ser ícones e marcadores
DPI_PAGINA = 100


def exigir(prog, dica):
    if not shutil.which(prog):
        sys.exit(f'Falta o programa "{prog}". {dica}')


def slug(nome):
    base, ext = os.path.splitext(os.path.basename(nome))
    base = unicodedata.normalize('NFKD', base).encode('ascii', 'ignore').decode().lower()
    base = re.sub(r'[^a-z0-9]+', '-', base).strip('-') or 'figura'
    if len(base) > 60:
        base = base[:48].rstrip('-') + '-' + hashlib.md5(base.encode()).hexdigest()[:8]
    return base, ext.lower()


class Trabalho:
    def __init__(self, pasta):
        self.pasta = pasta
        self.figuras = os.path.join(pasta, 'figuras')
        self.miniaturas = os.path.join(pasta, 'miniaturas')
        self.paginas = os.path.join(pasta, 'paginas')
        for d in (pasta, self.figuras, self.miniaturas):
            os.makedirs(d, exist_ok=True)
        self.manifesto = []
        self.por_hash = {}
        self.avisos = []

    def adicionar_figura(self, dados, nome, origem):
        """Grava a imagem e devolve o caminho relativo. Imagens iguais viram um só arquivo."""
        h = hashlib.md5(dados).hexdigest()
        if h in self.por_hash:
            item = self.por_hash[h]
            item['usos'].append(origem)
            return item['arquivo']
        base, ext = slug(nome)
        destino = f'{base}{ext}'
        n = 2
        while os.path.exists(os.path.join(self.figuras, destino)):
            destino = f'{base}-{n}{ext}'
            n += 1
        caminho = os.path.join(self.figuras, destino)
        with open(caminho, 'wb') as f:
            f.write(dados)
        item = {'arquivo': f'figuras/{destino}', 'nome_original': os.path.basename(nome), 'usos': [origem]}
        try:
            with Image.open(caminho) as im:
                item['largura'], item['altura'] = im.size
                mini = im.convert('RGBA')
                fundo = Image.new('RGBA', mini.size, 'white')
                fundo.alpha_composite(mini)
                fundo = fundo.convert('RGB')
                fundo.thumbnail((1100, 1100), Image.LANCZOS)
                nome_mini = os.path.splitext(destino)[0] + '.jpg'
                fundo.save(os.path.join(self.miniaturas, nome_mini), quality=85)
                item['miniatura'] = f'miniaturas/{nome_mini}'
        except Exception as e:  # formato vetorial ou arquivo corrompido
            item['erro'] = f'não foi possível abrir: {e}'
            self.avisos.append(f'{destino}: {item["erro"]}')
        self.manifesto.append(item)
        self.por_hash[h] = item
        return item['arquivo']

    def renderizar_pdf(self, pdf, prefixo):
        exigir('pdftoppm', 'Instale o poppler-utils.')
        os.makedirs(self.paginas, exist_ok=True)
        subprocess.run(['pdftoppm', '-r', str(DPI_PAGINA), '-jpeg', pdf, os.path.join(self.paginas, prefixo)], check=True)


def uniforme(im):
    """Fundos e retângulos de cor única, que o PDF guarda como imagem."""
    from PIL import ImageStat
    amostra = im.convert('RGB')
    amostra.thumbnail((200, 200))
    return max(ImageStat.Stat(amostra).stddev) < 4


def extrair_markdown(caminho, trab):
    raiz = os.path.dirname(os.path.abspath(caminho))
    with open(caminho, encoding='utf-8', errors='replace') as f:
        texto = f.read()
    indice = {}
    for d, _, arqs in os.walk(raiz):
        for a in arqs:
            if os.path.splitext(a)[1].lower() in EXT_IMG:
                indice.setdefault(a, os.path.join(d, a))

    def incluir(alvo):
        alvo = alvo.split('|')[0].strip()
        achado = indice.get(alvo) or indice.get(os.path.basename(alvo))
        rel = os.path.normpath(os.path.join(raiz, alvo))
        if not achado and rel.startswith(raiz + os.sep) and os.path.isfile(rel):
            achado = rel
        if not achado:
            trab.avisos.append(f'imagem citada e não encontrada: {alvo}')
            return f'[IMAGEM NÃO ENCONTRADA: {alvo}]'
        with open(achado, 'rb') as f:
            return f'![{os.path.basename(alvo)}]({trab.adicionar_figura(f.read(), achado, os.path.basename(caminho))})'

    def md_img(m):
        alvo = m.group(2).split(' ')[0]
        return m.group(0) if re.match(r'[a-z]+://', alvo) else incluir(alvo)

    # Nesta ordem: os links gerados para o Obsidian já apontam para figuras/ e não devem ser reprocessados.
    texto = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', md_img, texto)
    texto = re.sub(r'!\[\[([^\]]+)\]\]', lambda m: incluir(m.group(1)), texto)  # Obsidian
    return texto


def forma_para_md(forma, trab, origem, repetidas, saida):
    from pptx.enum.shapes import MSO_SHAPE_TYPE  # já disponível: extrair_pptx ajusta o caminho antes
    if forma.shape_type == MSO_SHAPE_TYPE.GROUP:
        for f in forma.shapes:
            forma_para_md(f, trab, origem, repetidas, saida)
        return
    if getattr(forma, 'has_table', False) and forma.has_table:
        linhas = [[c.text.replace('\n', ' ').replace('|', '/').strip() for c in l.cells] for l in forma.table.rows]
        if linhas:
            saida.append('| ' + ' | '.join(linhas[0]) + ' |')
            saida.append('|' + ' --- |' * len(linhas[0]))
            saida.extend('| ' + ' | '.join(l) + ' |' for l in linhas[1:])
            saida.append('')
        return
    if forma.shape_type == MSO_SHAPE_TYPE.PICTURE:
        try:
            dados, ext = forma.image.blob, forma.image.ext
            w, h = forma.image.size
        except Exception:
            return
        if max(w, h) < MIN_LADO or hashlib.md5(dados).hexdigest() in repetidas:
            return
        saida.append(f'![{forma.name}]({trab.adicionar_figura(dados, f"{origem}-{forma.name}.{ext}", origem)})')
        saida.append('')
        return
    if getattr(forma, 'has_text_frame', False) and forma.has_text_frame:
        for p in forma.text_frame.paragraphs:
            t = ''.join(r.text for r in p.runs).strip()
            if t:
                saida.append(('  ' * p.level + '- ' if p.level else '') + t)
        saida.append('')


def extrair_pptx(caminho, trab):
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError:
        # python3 -I ignora os pacotes do usuário, que é onde o pip costuma instalar.
        site.addsitedir(site.getusersitepackages())
        try:
            from pptx import Presentation
            from pptx.enum.shapes import MSO_SHAPE_TYPE
        except ImportError:
            sys.exit('Falta o python-pptx. Instale com: pip install python-pptx')
    apresentacao = Presentation(caminho)

    # Imagens presentes em muitos slides costumam ser logos e fundos do modelo.
    contagem = {}

    def contar(formas, vistos):
        for f in formas:
            if f.shape_type == MSO_SHAPE_TYPE.GROUP:
                contar(f.shapes, vistos)
            elif f.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    vistos.add(hashlib.md5(f.image.blob).hexdigest())
                except Exception:
                    pass

    for s in apresentacao.slides:
        vistos = set()
        contar(s.shapes, vistos)
        for h in vistos:
            contagem[h] = contagem.get(h, 0) + 1
    repetidas = {h for h, n in contagem.items() if n >= 3}

    partes = [f'# {os.path.basename(caminho)}', '']
    for i, s in enumerate(apresentacao.slides, 1):
        origem = f'slide-{i:02d}'
        partes += [f'## Slide {i}', '']
        # Ordem visual (de cima para baixo, da esquerda para a direita), não a ordem do XML.
        formas = sorted(s.shapes, key=lambda f: (round((f.top or 0) / 228600), f.left or 0))
        for forma in formas:
            forma_para_md(forma, trab, origem, repetidas, partes)
        if s.has_notes_slide and s.notes_slide.notes_text_frame and s.notes_slide.notes_text_frame.text.strip():
            partes += ['> Notas do apresentador: ' + s.notes_slide.notes_text_frame.text.strip().replace('\n', ' '), '']

    if shutil.which('soffice'):
        with tempfile.TemporaryDirectory() as tmp:
            # Perfil próprio: duas execuções do LibreOffice com o mesmo perfil travam.
            cmd = ['soffice', f'-env:UserInstallation=file://{tmp}/perfil', '--headless', '--convert-to', 'pdf', '--outdir', tmp, caminho]
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=600)
                pdf = os.path.join(tmp, os.path.splitext(os.path.basename(caminho))[0] + '.pdf')
                trab.renderizar_pdf(pdf, 'slide')
                shutil.copy(pdf, os.path.join(trab.paginas, 'material.pdf'))
            except Exception as e:
                trab.avisos.append(f'slides não renderizados: {e}')
    else:
        trab.avisos.append('LibreOffice ausente: slides não renderizados, apenas texto e imagens extraídos.')
    return '\n'.join(partes)


def extrair_pdf(caminho, trab):
    exigir('pdftotext', 'Instale o poppler-utils.')
    exigir('pdfimages', 'Instale o poppler-utils.')
    info = subprocess.run(['pdfinfo', caminho], capture_output=True, text=True).stdout
    m = re.search(r'Pages:\s+(\d+)', info)
    paginas = int(m.group(1)) if m else 0
    partes = [f'# {os.path.basename(caminho)}', '']
    total = 0
    for p in range(1, paginas + 1):
        t = subprocess.run(['pdftotext', '-layout', '-f', str(p), '-l', str(p), caminho, '-'], capture_output=True, text=True).stdout.strip()
        total += len(t)
        partes += [f'## Página {p}', '', t, '']
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['pdfimages', '-png', caminho, os.path.join(tmp, 'img')], check=True)
        # Máscaras de transparência saem como arquivos à parte, logo depois da imagem a que pertencem.
        # Aplicá-las evita logos com fundo preto; depois, não viram figuras próprias.
        lista = [l.split() for l in subprocess.run(['pdfimages', '-list', caminho], capture_output=True, text=True).stdout.splitlines()[2:]]
        mascara_de, mascaras, anterior = {}, set(), None
        for l in lista:
            if len(l) < 3:
                continue
            num, tipo = int(l[1]), l[2]
            if tipo in ('smask', 'mask', 'stencil'):
                mascaras.add(num)
                if tipo == 'smask' and anterior is not None:
                    mascara_de[anterior] = num
            else:
                anterior = num
        arquivos = {int(re.search(r'-(\d+)\.', n).group(1)): os.path.join(tmp, n) for n in os.listdir(tmp) if re.search(r'-(\d+)\.', n)}
        for num in sorted(arquivos):
            if num in mascaras:
                continue
            cam = arquivos[num]
            with Image.open(cam) as im:
                if max(im.size) < MIN_LADO or uniforme(im):
                    continue
                if num in mascara_de and mascara_de[num] in arquivos:
                    with Image.open(arquivos[mascara_de[num]]) as mk:
                        rgba = im.convert('RGBA')
                        rgba.putalpha(mk.convert('L').resize(im.size))
                    rgba.save(cam)
            with open(cam, 'rb') as f:
                trab.adicionar_figura(f.read(), f'pdf-{os.path.basename(cam)}', os.path.basename(caminho))
    trab.renderizar_pdf(caminho, 'pagina')
    shutil.copy(caminho, os.path.join(trab.paginas, 'material.pdf'))
    if paginas and total / paginas < 80:
        trab.avisos.append('Pouco texto por página: o PDF parece digitalizado. Leia as imagens em paginas/.')
    return '\n'.join(partes)


def extrair_docx(caminho, trab):
    """Word: texto e figuras pelo pandoc; imagens das páginas pelo LibreOffice, quando houver."""
    exigir('pandoc', 'Instale o pandoc (https://pandoc.org).')
    with tempfile.TemporaryDirectory() as tmp:
        md = os.path.join(tmp, 'documento.md')
        subprocess.run(['pandoc', caminho, '-t', 'gfm-raw_html', '--wrap=none', '--extract-media', tmp, '-o', md], check=True)
        texto = extrair_markdown(md, trab)
        office = shutil.which('soffice') or shutil.which('libreoffice')
        if office:
            subprocess.run([office, '--headless', '--convert-to', 'pdf', '--outdir', tmp, caminho],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pdf = os.path.join(tmp, os.path.splitext(os.path.basename(caminho))[0] + '.pdf')
            if os.path.exists(pdf):
                trab.renderizar_pdf(pdf, 'pagina')
                shutil.copy(pdf, os.path.join(trab.paginas, 'material.pdf'))
        else:
            trab.avisos.append('LibreOffice ausente: sem imagens das páginas do Word.')
    return texto


def extrair_doc(caminho, trab):
    ext = os.path.splitext(caminho)[1].lower()
    if ext in ('.md', '.markdown'):
        return extrair_markdown(caminho, trab)
    if ext == '.docx':
        return extrair_docx(caminho, trab)
    if ext == '.pptx':
        return extrair_pptx(caminho, trab)
    return extrair_pdf(caminho, trab)


def descompactar(zip_path, destino):
    raiz = os.path.realpath(destino)
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            alvo = os.path.realpath(os.path.join(destino, info.filename))
            if not (alvo == raiz or alvo.startswith(raiz + os.sep)):
                raise SystemExit(f'Zip recusado: caminho fora da pasta ({info.filename})')
        z.extractall(destino)


def documentos_em(pasta):
    docs = []
    for d, sub, arqs in os.walk(pasta):
        sub[:] = [s for s in sub if s != '__MACOSX' and not s.startswith('.')]
        docs += [os.path.join(d, a) for a in arqs if os.path.splitext(a)[1].lower() in EXT_DOC and not a.startswith('.')]
    return sorted(docs)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    entrada, pasta = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    if not os.path.exists(entrada):
        sys.exit(f'Entrada não encontrada: {entrada}')
    trab = Trabalho(pasta)
    with tempfile.TemporaryDirectory() as tmp:
        if entrada.lower().endswith('.zip'):
            descompactar(entrada, tmp)
            docs = documentos_em(tmp)
        elif os.path.isdir(entrada):
            docs = documentos_em(entrada)
        else:
            docs = [entrada]
        docs = [d for d in docs if os.path.splitext(d)[1].lower() in EXT_DOC]
        if not docs:
            sys.exit('Nenhum documento .md, .docx, .pdf ou .pptx encontrado na entrada.')
        textos = []
        for d in docs:
            if len(docs) > 1:
                textos.append(f'<!-- Documento: {os.path.basename(d)} -->')
            textos.append(extrair_doc(d, trab))
    with open(os.path.join(pasta, 'fonte.md'), 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(textos))
    with open(os.path.join(pasta, 'manifesto.json'), 'w', encoding='utf-8') as f:
        json.dump({'documentos': [os.path.basename(d) for d in docs], 'figuras': trab.manifesto, 'avisos': trab.avisos}, f, ensure_ascii=False, indent=1)
    pags = len([a for a in os.listdir(trab.paginas) if a.endswith('.jpg')]) if os.path.isdir(trab.paginas) else 0
    print(f'{len(docs)} documento(s), {len(trab.manifesto)} figura(s), {pags} página(s) renderizada(s) em {pasta}')
    for a in trab.avisos:
        print('AVISO:', a)


if __name__ == '__main__':
    main()

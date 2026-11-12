#!/usr/bin/env python3
"""Prepara a pasta de envio para um artefato do tipo Slides do claude.ai.

Uso:
  python3 preparar_artefato.py PASTA listar
      Lista as imagens usadas nos slides que ainda não estão em saida/artefato/blobs.json.
      Suba cada uma com upload_asset e registre o resultado em blobs.json:
      {"lmest/logos/ufu.png": "/_blob/<id>", ...}
  python3 preparar_artefato.py PASTA montar
      Cria saida/artefato/project/deck.json e saida/artefato/project/slides/<id>.html,
      com cada src trocado pelo /_blob/ registrado. Para se faltar alguma imagem.

O deck.json enviado é o do projeto. A instalação do Design System no deck (tokens.json
e o registro em designSystems) segue as instruções do próprio tipo Slides: ver
references/saida-artefato.md.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # funciona também com python3 -I
from lmest_comum import Projeto, gravar, gravar_json, ler, ler_json

RE_IMG = re.compile(r'(<img\b[^>]*?\bsrc=")([^"]+)(")')


def imagens(prj):
    usadas = []
    for sid in prj.ordem():
        for m in RE_IMG.finditer(ler(prj.arquivo(sid))):
            if m.group(2) not in usadas and not m.group(2).startswith('/_blob/'):
                usadas.append(m.group(2))
    return usadas


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ('listar', 'montar'):
        sys.exit(__doc__)
    prj = Projeto(sys.argv[1])
    base = os.path.join(prj.pasta, 'saida', 'artefato')
    blobs_path = os.path.join(base, 'blobs.json')
    os.makedirs(base, exist_ok=True)
    blobs = ler_json(blobs_path, {})
    faltam = [s for s in imagens(prj) if s not in blobs]
    if sys.argv[2] == 'listar':
        if not os.path.exists(blobs_path):
            gravar_json(blobs_path, {})
        for s in faltam:
            print(os.path.join(prj.pasta, s))
        print(f'{len(faltam)} imagem(ns) a subir; registre cada /_blob/ em {blobs_path}')
        return
    if faltam:
        sys.exit('Faltam em blobs.json:\n' + '\n'.join(faltam))
    for sid in prj.ordem():
        html = RE_IMG.sub(lambda m: m.group(1) + blobs.get(m.group(2), m.group(2)) + m.group(3), ler(prj.arquivo(sid)))
        gravar(os.path.join(base, 'project', 'slides', f'{sid}.html'), html)
    gravar_json(os.path.join(base, 'project', 'deck.json'), prj.deck)
    print(f'Pasta pronta: {os.path.join(base, "project")} ({len(prj.ordem())} slides)')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Cria a pasta de uma apresentação nova.

Uso: python3 novo_projeto.py PASTA "Título da apresentação"

Cria PASTA com:
  deck.json      índice no formato do tipo Slides (order, sections, cover, title)
  projeto.json   dados da capa, do palestrante e opções (saídas, barra, animações)
  slides/        um arquivo <id>.html por slide
  lmest/         cópia dos assets do Design System (logos, parceiros, ícones, fundos)
  imagens/       figuras do material usadas nos slides
  saida/         arquivos gerados (HTML, PPTX, pasta do artefato)
Depois, rode montar_fixos.py para gerar a capa e o agradecimento.
"""
import datetime
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # funciona também com python3 -I
from lmest_comum import ASSETS, Projeto, gravar_json

PROJETO_PADRAO = {
    'titulo': '',
    'sobretitulo': 'LMEst-UFU',
    'subtitulo': '',
    'data_local': '',
    'palestrante': {
        'nome': 'Nome do apresentador',
        'cargo': '',
        'afiliacao': 'Laboratório de Mecânica de Estruturas “Prof. José Eduardo Tannús Reis” · '
                     'Faculdade de Engenharia Mecânica · Universidade Federal de Uberlândia',
        'telefone': '',
        'emails': ['e-mail do apresentador'],
    },
    'saidas': [],
    'barra_progresso': False,
    'animacoes': False,
    'sem_numero': [],
}


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pasta, titulo = os.path.abspath(sys.argv[1]), sys.argv[2]
    # A pasta pode já existir com o roteiro.md aprovado; só não pode já ser um projeto.
    if os.path.exists(os.path.join(pasta, 'deck.json')):
        sys.exit(f'Já existe um projeto em {pasta}. Edite-o em vez de recriar.')
    for sub in ('slides', 'imagens', 'saida'):
        os.makedirs(os.path.join(pasta, sub), exist_ok=True)
    destino = os.path.join(pasta, 'lmest')
    for grupo in ('logos', 'parceiros', 'icones', 'fundos'):
        shutil.copytree(os.path.join(ASSETS, grupo), os.path.join(destino, grupo), dirs_exist_ok=True)
    agora = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    gravar_json(os.path.join(pasta, 'deck.json'), {
        'v': 4,
        'createdOnFiles': {'v': 1, 'at': agora},
        'lists': 'css',
        'title': titulo,
        'cover': 'capa',
        'order': ['capa', 'agradecimento'],
        'sections': {},
        'faces': {'carlito': {'family': 'Carlito',
                              'href': 'https://fonts.googleapis.com/css2?family=Carlito:ital,wght@0,400;0,700;1,400;1,700&display=swap'}},
        'designSystems': [],
    })
    proj = dict(PROJETO_PADRAO, titulo=titulo)
    gravar_json(os.path.join(pasta, 'projeto.json'), proj)
    Projeto(pasta)  # valida o que foi escrito
    print(f'Projeto criado em {pasta}. Preencha projeto.json e rode montar_fixos.py.')


if __name__ == '__main__':
    main()

# lmest-apresentacao

Skill que transforma um material (PPTX, PDF, Word ou Markdown) em uma apresentação com a identidade visual do LMEst-UFU, seguindo o Design System do laboratório e os padrões aprovados nas apresentações do minicurso de IA.

## O que ela faz

- Lê o material e propõe um **roteiro** (slides, títulos, layouts e figuras) para você aprovar antes de montar.
- Monta o deck inteiro com:
  - capa institucional;
  - slides de conteúdo com a faixa azul-marinho e o filete vermelho;
  - divisórias de parte;
  - agradecimento com as logos dos parceiros.
- Gera a saída que você escolher:
  - **HTML** offline em um único arquivo (F para tela cheia, N para as notas, Ctrl+P para PDF);
  - **PPTX** editável, com as notas do apresentador;
  - **artefato Slides** do claude.ai.
- Edita decks já criados: inserir, remover ou mover slides, renumerar, aplicar a barra de progresso e animar slides.

São opcionais e só entram se você pedir:
- a barra de progresso;
- as animações (só no HTML e no artefato);
- o resumo "O que vimos hoje".

## Como usar

Peça ao agente, anexando o material:

> Crie uma apresentação de 20 minutos a partir deste PDF.

A skill responde com o roteiro e algumas perguntas: saída, dados do palestrante, capa, duração e opcionais. Depois da sua aprovação, ela monta tudo numa pasta `apresentacao-<nome>/`, ao lado do material, e entrega os arquivos em `saida/`.

Para ajustar depois, basta pedir:

> No deck apresentacao-rotores, insira um slide sobre o ensaio depois do slide 5.

Os números de página são refeitos automaticamente.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `SKILL.md` | Instruções que o agente segue |
| `references/` | Design System, regras de slide, catálogo de layouts, animações, roteiro e publicação como artefato |
| `scripts/` | Extração do material, montagem da capa e do agradecimento, numeração, validação e geração de HTML e PPTX |
| `assets/` | Logos, parceiros, ícones, fundo institucional e fonte Carlito |

## Requisitos

- **Sempre:** Python 3 com Pillow, BeautifulSoup, python-pptx, PyMuPDF e matplotlib. Se faltar algum pacote, o script mostra o comando de instalação.
- **Material em Word:** pandoc.
- **Imagens das páginas** (PDF, PPTX e Word): poppler (`pdftoppm`) e LibreOffice.

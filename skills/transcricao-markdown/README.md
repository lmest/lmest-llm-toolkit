# Transcrição de documentos para Markdown

Skill do Claude Code que transcreve o PDF de um documento técnico ou científico (artigo, tese, relatório, livro etc.) para Markdown fiel: texto na língua original, equações em LaTeX, tabelas em Markdown e todas as figuras recortadas em imagens.

## Como usar

Peça ao Claude, indicando o PDF:

> Transcreva o artigo `caminho/do/artigo.pdf` para Markdown.

A skill é acionada sozinha. O resultado é criado ao lado do PDF, numa pasta com o título do documento:

```text
Título do Documento/
├── Título do Documento.md   # transcrição
└── images/               # uma imagem por figura
```

As regras completas estão em [SKILL.md](SKILL.md).

## Exemplos

- Artigo original: [meder_2026.pdf](../../exemplos/transcricao-markdown/meder_2026/meder_2026.pdf)
- Transcrição: [Reinforcement Learning for Online Gain Scheduling in LQR.md](<../../exemplos/transcricao-markdown/meder_2026/Reinforcement Learning for Online Gain Scheduling in LQR/Reinforcement Learning for Online Gain Scheduling in LQR.md>)
- Figuras recortadas: [images/](<../../exemplos/transcricao-markdown/meder_2026/Reinforcement Learning for Online Gain Scheduling in LQR/images/>)
- Modelo de `crops.json`: [crops.example.json](references/crops.example.json), com regiões de leitura para páginas em duas colunas e uma região de figura. Ele serve para planejar recortes de leitura quando o layout exige (ver [SKILL.md](SKILL.md)).

## Requisitos

Python 3 com PyMuPDF (1.24.3 ou superior) e Pillow:

```bash
python -m pip install -r requirements.txt
```

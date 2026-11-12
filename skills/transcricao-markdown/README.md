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

## Exemplo

- Artigo original: [meder_2026.pdf](examples/meder_2026/meder_2026.pdf)
- Transcrição: [Reinforcement Learning for Online Gain Scheduling in LQR - Application to the Cart-Pole.md](<examples/meder_2026/Reinforcement Learning for Online Gain Scheduling in LQR - Application to the Cart-Pole/Reinforcement Learning for Online Gain Scheduling in LQR - Application to the Cart-Pole.md>)
- Figuras recortadas: [images/](<examples/meder_2026/Reinforcement Learning for Online Gain Scheduling in LQR - Application to the Cart-Pole/images/>)

## Requisitos

Python 3 com PyMuPDF (1.24.3 ou superior) e Pillow:

```bash
python -m pip install -r requirements.txt
```

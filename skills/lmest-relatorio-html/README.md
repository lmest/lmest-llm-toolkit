# lmest-relatorio-html

Skill do Claude Code que transforma um material técnico (nota em Markdown/Obsidian, zip com anexos, PDF ou PPTX) em um relatório HTML único e offline, com a identidade visual do LMEst-UFU: capa institucional, índice lateral, figuras ampliáveis e equações em LaTeX.

## Como usar

1. Baixe a pasta da skill (`lmest-relatorio-html`).
2. Coloque-a em `~/.claude/skills/`, de modo que exista `~/.claude/skills/lmest-relatorio-html/SKILL.md`. Em um projeto, ela também pode ficar em `.claude/skills/` dentro da pasta do projeto.
3. Abra o Claude Code, envie (ou indique o caminho do) material de referência e peça o relatório. Exemplo:

   ```text
   Crie um relatório HTML do LMEst com base neste material: ~/Documentos/relatorio_2026-10-29.zip
   ```

   Ou, com um PDF ou PPTX:

   ```text
   Gere um relatório HTML do LMEst a partir de ~/Documentos/apresentacao.pptx
   ```

4. Peça ajustes, se precisar. Por exemplo:
   - Coloque as duas figuras de espectro lado a lado.
   - Destaque a equação da força em um painel.
   - Troque o título da seção de resultados.

O relatório é salvo ao lado do material (ou onde você pedir), e o Claude informa os pontos a confirmar.

## Exemplo

O relatório [relatorio_2026-10-29.html](examples/relatorio_2026-10-29.html), na pasta [examples/](examples/), mostra o formato que a skill gera. É o relatório "Processamento dos dados coletados pelo robô", com índice lateral, equações em LaTeX e figuras. Por ser um arquivo único, ele abre no navegador sem depender de internet.

## Requisitos

- Sempre: Python 3 com Pillow e pandoc.
- Para PPTX: python-pptx e LibreOffice.
- Para PDF: poppler-utils.

```bash
pip install Pillow python-pptx
sudo apt install pandoc libreoffice poppler-utils
```

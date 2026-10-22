#!/usr/bin/env python3
"""Converte um PDF em um RASCUNHO de Markdown + imagens para revisão.

    python3 scripts/pdf_to_markdown.py conteudo.pdf work/pdf_rascunho work/pdf_paginas

Normalmente é chamado por ``prepare_input_bundle.py`` (entrada .pdf). Gera:

- ``<rascunho>/apresentacao.md``: um bloco por página, separado por ``---``,
  com título provável (maior fonte no topo), texto e imagens extraídas. Cada
  bloco traz ``<!-- origem: pagina N -->`` e, quando for o caso,
  ``<!-- conferir: ... -->``. Não há front matter: os dados da capa são só
  sugeridos no relatório e precisam ser confirmados pelo usuário;
- ``<rascunho>/imagens/pNNN_imgK.png``: imagens raster recortadas da página;
- ``<paginas>/pagina-NNN.png``: render de cada página para inspeção visual.

Limitações (por isso Markdown + imagens é a entrada preferida):
- equações viram texto quebrado ou somem; precisam ser transcritas em LaTeX;
- gráficos vetoriais não são extraídos como imagem (só aparecem no render da página);
- a ordem de leitura em layouts com colunas pode sair embaralhada;
- PDFs escaneados não têm texto: o conteúdo precisa ser lido no render.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from pathlib import Path

RENDER_DPI = 110          # render das páginas para inspeção
CROP_DPI = 220            # resolução dos recortes de imagem
MIN_IMG_PT = 40           # ignora ícones/marcadores menores que isso
MATH_FONT_RE = re.compile(r"(CMMI|CMSY|CMEX|MSBM|LMMath|LatinModernMath|CambriaMath|Cambria-Math|STIX|Symbol|MathJax|XITSMath)", re.I)
BULLET_RE = re.compile(r"^\s*[•▪◦●■▶►▸‣\-–\u2022\u25aa\u25cf]\s+")
MATH_TEXT_RE = re.compile(r"[∑∫∂∇√∞∈∀∃⇒]|(^|\s)[A-Za-zα-ωΑ-Ω]\s*=\s*[A-Za-zα-ωΑ-Ω\\(]")
# acentos "soltos" de PDFs LaTeX sem fontenc T1 (magn´eticos, For¸ca, frequˆencia)
SPACING_ACCENTS = {"´": "\u0301", "`": "\u0300", "ˆ": "\u0302", "˜": "\u0303", "¨": "\u0308",
                   "¸": "\u0327", "˚": "\u030a", "ˇ": "\u030c"}
ACCENT_RE = re.compile("([" + "".join(SPACING_ACCENTS) + "])\\s?([A-Za-zıȷ])")


def fix_accents(text: str) -> str:
    def repl(m):
        base = {"ı": "i", "ȷ": "j"}.get(m.group(2), m.group(2))
        return unicodedata.normalize("NFC", base + SPACING_ACCENTS[m.group(1)])
    return unicodedata.normalize("NFC", ACCENT_RE.sub(repl, text))


def has_vector_figure(page) -> bool:
    area = page.width * page.height
    big = [o for o in list(page.curves) + list(page.rects)
           if 0.02 * area < (o["x1"] - o["x0"]) * (o["bottom"] - o["top"]) < 0.5 * area]  # ignora fundos
    return sum((o["x1"] - o["x0"]) * (o["bottom"] - o["top"]) for o in big) > 0.08 * area and len(page.curves) > 3
THANKS_RE = re.compile(r"\b(obrigad[oa]s?|agradecimentos?|thank you|perguntas\??)\b", re.I)


def _lines(page) -> list[dict]:
    words = page.extract_words(keep_blank_chars=False, use_text_flow=True, extra_attrs=["size", "fontname"])
    lines: list[dict] = []
    for w in words:
        if lines and abs(w["top"] - lines[-1]["top"]) < max(2.0, w["size"] * 0.35) and w["x0"] >= lines[-1]["x1"] - 2:
            ln = lines[-1]
            ln["text"] += " " + w["text"]
            ln["x1"] = w["x1"]
            ln["size"] = max(ln["size"], w["size"])
        else:
            lines.append({"text": w["text"], "top": w["top"], "x0": w["x0"], "x1": w["x1"], "size": w["size"]})
    for ln in lines:
        ln["text"] = fix_accents(ln["text"])
    return lines


def _title(lines: list[dict], page_h: float) -> tuple[str, int | None]:
    """Título: faixa de topo, se houver; senão a linha mais alta entre as de maior corpo."""
    cands = [i for i, l in enumerate(lines) if len(l["text"].strip()) > 1 and not re.fullmatch(r"[\d\s.,+%–-]+", l["text"])]
    if not cands:
        return "", None
    biggest = max(lines[i]["size"] for i in cands)
    header = [i for i in cands if lines[i]["top"] < page_h * 0.15 and lines[i]["size"] >= 0.6 * biggest]
    if header:  # faixa de título no topo (decks com cabeçalho) vence números grandes no corpo
        biggest = max(lines[i]["size"] for i in header)
        cands = header
    best = min((i for i in cands if lines[i]["size"] >= 0.85 * biggest), key=lambda i: lines[i]["top"])
    text = lines[best]["text"]
    j = best + 1  # título quebrado em duas linhas (mesmo corpo, logo abaixo)
    while j < len(lines) and abs(lines[j]["size"] - lines[best]["size"]) < 0.5 and 0 < lines[j]["top"] - lines[j - 1]["top"] < lines[best]["size"] * 1.6:
        text += " " + lines[j]["text"]
        j += 1
    return text.strip(), best


def _images(page, pno: int, out_dir: Path) -> list[str]:
    saved = []
    area = page.width * page.height
    boxes = []
    for im in page.images:
        x0, top, x1, bottom = max(0, im["x0"]), max(0, im["top"]), min(page.width, im["x1"]), min(page.height, im["bottom"])
        w, h = x1 - x0, bottom - top
        if w < MIN_IMG_PT or h < MIN_IMG_PT or w * h > 0.9 * area:  # ícone ou fundo de página
            continue
        if any(abs(x0 - b[0]) < 2 and abs(top - b[1]) < 2 and abs(x1 - b[2]) < 2 for b in boxes):
            continue  # duplicata (máscaras/camadas)
        boxes.append((x0, top, x1, bottom))
    for k, box in enumerate(sorted(boxes, key=lambda b: (round(b[1] / 20), b[0])), start=1):
        name = f"p{pno:03d}_img{k}.png"
        page.crop(box).to_image(resolution=CROP_DPI).save(out_dir / name)
        saved.append(name)
    return saved


def convert(pdf: Path, draft_dir: Path, pages_dir: Path) -> dict:
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("A entrada PDF requer pdfplumber (pip install pdfplumber).") from exc
    for d in (draft_dir, pages_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    img_dir = draft_dir / "imagens"
    img_dir.mkdir()

    blocks, report_pages = [], []
    capa = None
    with pdfplumber.open(str(pdf)) as doc:
        n = len(doc.pages)
        for pno, page in enumerate(doc.pages, start=1):
            page.to_image(resolution=RENDER_DPI).save(pages_dir / f"pagina-{pno:03d}.png")
            lines = _lines(page)
            has_text = bool(lines)
            fragments = sum(1 for l in lines if re.fullmatch(r"[A-Za-zα-ωΑ-Ω]", l["text"].strip()))
            math = (any(MATH_FONT_RE.search(c.get("fontname", "")) for c in page.chars)
                    or any(MATH_TEXT_RE.search(l["text"]) for l in lines) or fragments >= 3)
            title, t_idx = _title(lines, page.height) if has_text else ("", None)
            body_lines = [l for i, l in enumerate(lines) if i != t_idx and l["text"] not in title.split("\n")]
            # remove linhas que já fazem parte do título em duas linhas
            if title:
                body_lines = [l for l in body_lines if l["text"] not in title]
            imgs = _images(page, pno, img_dir)
            all_text = " ".join(l["text"] for l in lines)

            kind = "conteudo"
            if pno == 1:
                kind = "possivel_capa"
            elif pno == n and THANKS_RE.search(all_text) and len(all_text) < 600:
                kind = "possivel_agradecimentos"
            elif has_text and len(lines) <= 3 and not imgs:
                kind = "possivel_divisor"

            conferir = []
            if not has_text:
                conferir.append("página sem camada de texto (escaneada/imagem): transcreva lendo o render")
            if math:
                conferir.append("há equações: transcreva em LaTeX ($$...$$) a partir do render e confirme com o usuário")
            if has_text and has_vector_figure(page):
                conferir.append("possível gráfico/figura vetorial: recorte do render da página se for necessário")

            md = [f"<!-- origem: pagina {pno} ({kind}) -->"]
            if conferir:
                md.append(f"<!-- conferir: {'; '.join(conferir)} -->")
            heading = "#" if kind == "possivel_divisor" else "##"
            md.append(f"{heading} {title or f'[sem título — página {pno}]'}")
            md.append("")
            last_top = None
            for l in body_lines:  # ordem do fluxo do PDF (em decks exportados, caixa a caixa)
                text = BULLET_RE.sub("- ", l["text"]).strip()
                if re.fullmatch(r"\d{1,3}", text):  # número de página
                    continue
                if last_top is not None and not (0 < l["top"] - last_top <= l["size"] * 1.8):
                    md.append("")
                md.append(text)
                last_top = l["top"]
            for name in imgs:
                md += ["", f"![](imagens/{name})"]
            blocks.append("\n".join(md).rstrip())

            if pno == 1:
                ordered = sorted(lines, key=lambda l: -l["size"])
                capa = {"titulo_provavel": title,
                        "demais_linhas": [l["text"] for l in sorted(lines, key=lambda l: l["top"]) if l["text"] not in title][:12],
                        "maior_fonte_pt": round(ordered[0]["size"], 1) if ordered else None}
            report_pages.append({"pagina": pno, "tipo_provavel": kind, "titulo": title, "texto": has_text,
                                 "equacoes": math, "imagens": imgs})

    header = ("<!-- RASCUNHO gerado a partir de PDF. Revise antes de usar: estrutura, títulos, "
              "ordem do texto, equações (LaTeX) e o front matter da capa (confirmar com o usuário). -->\n\n")
    (draft_dir / "apresentacao.md").write_text(header + "\n\n---\n\n".join(blocks) + "\n", encoding="utf-8")
    return {
        "rascunho_md": str(draft_dir / "apresentacao.md"),
        "paginas_renderizadas": str(pages_dir),
        "paginas": report_pages,
        "capa_sugerida": capa,
        "paginas_sem_texto": [p["pagina"] for p in report_pages if not p["texto"]],
        "paginas_com_equacoes": [p["pagina"] for p in report_pages if p["equacoes"]],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("rascunho_dir")
    ap.add_argument("paginas_dir")
    args = ap.parse_args()
    print(json.dumps(convert(Path(args.pdf), Path(args.rascunho_dir), Path(args.paginas_dir)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

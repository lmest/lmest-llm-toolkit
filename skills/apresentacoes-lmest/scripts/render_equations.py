#!/usr/bin/env python3
"""Renderiza as equações LaTeX de um Markdown em PNGs de 300 dpi.

    python3 scripts/render_equations.py apresentacao.md work/equacoes [--sem-inline]
        [--pt-display 20] [--pt-inline 16]

Cada equação é compilada já no tamanho de fonte final (``--pt-*``). O
``equations_manifest.json`` informa ``largura_in``/``altura_in``: inserir a
imagem exatamente nesse tamanho garante que todas as equações do deck tenham o
mesmo corpo de letra. Não reescale equações individualmente.

Ignora blocos de código, código inline, comentários HTML e valores monetários
(``R$ 70``, ``$5 e $10``). Se alguma equação falhar, as demais são
renderizadas, a falha é registrada no manifesto com o log do pdflatex e o
script termina com código 1. Nunca troque uma equação que falhou por texto.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lmest_markdown import (  # noqa: E402
    MATH_ENVS, MarkdownBlockquoteError, find_math, slide_for_line, split_front_matter, split_slides,
)


DPI = 300
PAD_PX = 12
ENV_START_RE = re.compile(r"^\\begin\{" + MATH_ENVS + r"\}")


def check_command(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(
            f"Comando '{name}' não encontrado. Instale TeX Live (pdflatex, pacotes lm/amsmath/"
            f"mathtools/standalone) e Poppler (pdftocairo). Ex. Debian/Ubuntu: "
            f"apt-get install texlive-latex-extra texlive-fonts-recommended lmodern poppler-utils"
        )


def detect_fonts() -> tuple[str, str]:
    """Latin Modern quando disponível; senão Computer Modern (mesmo desenho matemático)."""
    kpse = shutil.which("kpsewhich")
    if kpse and subprocess.run([kpse, "lmodern.sty"], stdout=subprocess.PIPE, text=True).stdout.strip():
        return "\\usepackage[T1]{fontenc}\n\\usepackage{lmodern}", "Latin Modern"
    return "% lmodern.sty indisponível: Computer Modern padrão", "Computer Modern"


FONT_PREAMBLE, FONT_NAME = "", ""


def make_document(latex: str, kind: str, pt: float) -> str:
    if ENV_START_RE.match(latex):
        body = latex
    elif kind == "inline":
        body = rf"${latex}$"
    else:
        body = rf"\[{latex}\]"
    lead = pt * 1.2
    fonts = FONT_PREAMBLE
    return rf"""\RequirePackage{{fix-cm}}
\documentclass[preview,border=1pt]{{standalone}}
{fonts}
\usepackage{{amsmath,amssymb,mathtools,bm}}
\begin{{document}}
\fontsize{{{pt}}}{{{lead}}}\selectfont
{body}
\end{{document}}
"""


def crop_transparent(path: Path) -> tuple[int, int]:
    image = Image.open(path).convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("imagem vazia")
    box = (max(0, bbox[0] - PAD_PX), max(0, bbox[1] - PAD_PX),
           min(image.width, bbox[2] + PAD_PX), min(image.height, bbox[3] + PAD_PX))
    cropped = image.crop(box)
    cropped.save(path, dpi=(DPI, DPI))
    return cropped.size


def render_one(latex: str, kind: str, pt: float, out_path: Path, work: Path, stem: str) -> tuple[int, int]:
    tex = work / f"{stem}.tex"
    tex.write_text(make_document(latex, kind, pt), encoding="utf-8")
    proc = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
         f"-output-directory={work}", str(tex)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False, timeout=120,
    )
    pdf = work / f"{stem}.pdf"
    if proc.returncode != 0 or not pdf.exists():
        errs = [ln for ln in proc.stdout.splitlines() if ln.startswith("!") or ":" in ln and "error" in ln.lower()]
        raise RuntimeError("\n".join(errs[-8:]) or proc.stdout[-2000:])
    subprocess.run(["pdftocairo", "-png", "-singlefile", "-r", str(DPI), "-transp", str(pdf), str(work / stem)],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, timeout=120)
    png = work / f"{stem}.png"
    size = crop_transparent(png)
    shutil.copy2(png, out_path)
    return size


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("markdown")
    ap.add_argument("output_dir")
    ap.add_argument("--sem-inline", action="store_true",
                    help="não renderizar matemática inline ($...$)")
    ap.add_argument("--pt-display", type=float, default=20.0, help="corpo das equações display (padrão 20 pt)")
    ap.add_argument("--pt-inline", type=float, default=16.0, help="corpo das fórmulas inline (padrão 16 pt)")
    args = ap.parse_args()

    md = Path(args.markdown).resolve()
    out = Path(args.output_dir).resolve()
    text = md.read_text(encoding="utf-8-sig")
    _, body, consumed, _ = split_front_matter(text)
    try:
        slides = split_slides(body, line_offset=consumed)
    except MarkdownBlockquoteError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 6

    check_command("pdflatex")
    check_command("pdftocairo")
    global FONT_PREAMBLE, FONT_NAME
    FONT_PREAMBLE, FONT_NAME = detect_fonts()
    out.mkdir(parents=True, exist_ok=True)
    items = find_math(text, include_inline=not args.sem_inline)

    entries, failures = [], 0
    with tempfile.TemporaryDirectory(prefix="lmest_eq_") as tmp:
        work = Path(tmp)
        for i, it in enumerate(items, start=1):
            stem = f"equation_{i:03d}"
            pt = args.pt_display if it.kind == "display" else args.pt_inline
            s = slide_for_line(slides, it.line)
            entry = {"index": i, "kind": it.kind, "latex": it.latex, "line": it.line,
                     "slide": s.index if s else None, "slide_titulo": s.title if s else None, "pt": pt}
            try:
                w, h = render_one(it.latex, it.kind, pt, out / f"{stem}.png", work, stem)
                entry.update({"image": f"{stem}.png", "largura_px": w, "altura_px": h,
                              "largura_in": round(w / DPI, 4), "altura_in": round(h / DPI, 4)})
            except Exception as exc:  # registra e segue com as demais
                failures += 1
                failed = out / "falhas"
                failed.mkdir(exist_ok=True)
                shutil.copy2(work / f"{stem}.tex", failed / f"{stem}.tex")
                entry.update({"image": None, "erro": str(exc)})
            entries.append(entry)

    manifest = {"markdown": str(md), "dpi": DPI, "fonte": FONT_NAME, "equations": entries, "falhas": failures}
    (out / "equations_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "equations"} |
                     {"renderizadas": len(entries) - failures}, ensure_ascii=False))
    for e in entries:
        status = e["image"] or "FALHOU"
        print(f"  #{e['index']:03d} {e['kind']:7s} slide {e['slide']} linha {e['line']}: {status}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

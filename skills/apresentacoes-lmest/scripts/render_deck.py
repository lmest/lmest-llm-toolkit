#!/usr/bin/env python3
"""Converte o .pptx em PDF e em PNGs 1920 × 1080 (um por slide).

    python3 scripts/render_deck.py work/deck.pptx work/render [--paginas 3,5]

Saída: ``work/render/<deck>.pdf`` e ``work/render/slide-001.png`` …

LibreOffice: usa, nesta ordem, ``$LMEST_SOFFICE``; o wrapper da skill pública
de pptx (``/mnt/skills/public/pptx/scripts/office/soffice.py``, necessário no
sandbox do claude.ai, onde ``soffice`` puro trava); ``soffice`` do PATH.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

WRAPPERS = [
    Path("/mnt/skills/public/pptx/scripts/office/soffice.py"),
]


def soffice_cmd() -> list[str]:
    env = os.environ.get("LMEST_SOFFICE")
    if env:
        return [sys.executable, env] if env.endswith(".py") else [env]
    for w in WRAPPERS:
        if w.exists():
            return [sys.executable, str(w)]
    for name in ("soffice", "libreoffice"):
        if shutil.which(name):
            return [name]
    raise SystemExit("LibreOffice não encontrado (soffice). Instale-o ou defina LMEST_SOFFICE.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx")
    ap.add_argument("saida")
    ap.add_argument("--paginas", help="lista de páginas para rasterizar, ex.: 1,3,7 (o PDF é sempre completo)")
    ap.add_argument("--preserve-aspect", action="store_true",
                    help="preserva a proporção original dos slides (útil para apresentações de origem)")
    args = ap.parse_args()

    if not shutil.which("pdftoppm"):
        raise SystemExit("pdftoppm (Poppler) não encontrado.")
    pptx = Path(args.pptx).resolve()
    out = Path(args.saida).resolve()
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / (pptx.stem + ".pdf")
    if pdf.exists():
        pdf.unlink()
    proc = subprocess.run(soffice_cmd() + ["--headless", "--convert-to", "pdf", "--outdir", str(out), str(pptx)],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    if not pdf.exists():
        print(proc.stdout[-3000:], file=sys.stderr)
        raise SystemExit("Falha na conversão para PDF.")

    pages = None
    if args.paginas:
        pages = sorted({int(p) for p in args.paginas.split(",") if p.strip()})
        for p in pages:
            old = out / f"slide-{p:03d}.png"
            if old.exists():
                old.unlink()
    else:
        for old in out.glob("slide-*.png"):
            old.unlink()

    tmp = out / "_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()
    ranges = [(p, p) for p in pages] if pages else [(None, None)]
    for first, last in ranges:
        cmd = ["pdftoppm", "-png"]
        if args.preserve_aspect:
            cmd += ["-scale-to", "1920"]
        else:
            cmd += ["-scale-to-x", "1920", "-scale-to-y", "1080"]
        if first:
            cmd += ["-f", str(first), "-l", str(last)]
        subprocess.run(cmd + [str(pdf), str(tmp / "p")], check=True, timeout=600)
    for f in tmp.glob("p-*.png"):
        n = int(f.stem.split("-")[-1])
        f.rename(out / f"slide-{n:03d}.png")
    shutil.rmtree(tmp, ignore_errors=True)

    files = sorted(out.glob("slide-*.png"))
    print(f"PDF: {pdf}")
    for f in files:
        print(f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

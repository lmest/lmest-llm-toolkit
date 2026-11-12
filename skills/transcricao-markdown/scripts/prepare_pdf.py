#!/usr/bin/env python3
"""Renderiza páginas do PDF em PNG, extrai o texto embutido (em ordem de leitura) e
registra em metadata.json as caixas de blocos de texto, legendas, imagens e desenhos
em coordenadas normalizadas [x0,y0,x1,y1], no mesmo sistema usado por crops.json."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
try:
    import pymupdf
except ImportError as exc:
    raise SystemExit("Dependência ausente: instale PyMuPDF>=1.24.3 (pip install PyMuPDF).") from exc

# Início de legenda: "Figure 3:", "Fig. 3.", "Figura 3 –", "Table 2:", "Tabela 2.", "TABLE II" etc.
# Exige pontuação (ou fim do bloco) logo após o número, para não confundir legendas com
# frases do texto corrido que começam citando a figura ("Figure 2 illustrates ...").
CAPTION_RE = re.compile(
    r"^\s*(fig(?:ure|ura)?\.?|tab(?:le|ela)\.?)\s*(\d+|[IVXLC]+)\s*(?:[:.|–—-]|$)", re.IGNORECASE)
SNIPPET = 80
MIN_DRAWING_AREA = 0.002  # fração da página; descarta traços soltos, fios de tabela curtos etc.


def norm(rect, page):
    """Converte um retângulo da página (sem rotação) para coordenadas normalizadas da imagem renderizada."""
    r = pymupdf.Rect(rect) * page.rotation_matrix
    w, h = page.rect.width, page.rect.height
    vals = [r.x0 / w, r.y0 / h, r.x1 / w, r.y1 / h]
    return [round(min(1.0, max(0.0, v)), 4) for v in vals]


def page_layout(page):
    text_blocks, captions, images = [], [], []
    for b in page.get_text("dict", sort=True)["blocks"]:
        if b.get("type") == 1:
            images.append({"bbox": norm(b["bbox"], page)})
            continue
        text = " ".join(
            "".join(s["text"] for s in line["spans"]) for line in b.get("lines", [])
        ).strip()
        if not text:
            continue
        item = {"bbox": norm(b["bbox"], page), "text": text[:SNIPPET]}
        text_blocks.append(item)
        m = CAPTION_RE.match(text)
        if m:
            kind = "table" if m.group(1).lower().startswith("tab") else "figure"
            captions.append({"kind": kind, "label": f"{m.group(1)} {m.group(2)}", **item})
    drawings = []
    if hasattr(page, "cluster_drawings"):
        area = page.rect.width * page.rect.height
        for r in page.cluster_drawings():
            if r.width * r.height >= MIN_DRAWING_AREA * area:
                drawings.append({"bbox": norm(r, page)})
    return {"text_blocks": text_blocks, "captions": captions,
            "image_blocks": images, "drawing_clusters": drawings}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pdf", type=Path); p.add_argument("output_dir", type=Path)
    p.add_argument("--dpi", type=int, default=200)
    a = p.parse_args()
    if not a.pdf.is_file(): p.error(f"PDF não encontrado: {a.pdf}")
    if not 36 <= a.dpi <= 1200: p.error("--dpi deve estar entre 36 e 1200")
    pages_dir = a.output_dir / "pages"; pages_dir.mkdir(parents=True, exist_ok=True)
    text, meta = [], []
    try: doc = pymupdf.open(a.pdf)
    except Exception as exc: raise SystemExit(f"Não foi possível abrir o PDF: {exc}") from exc
    with doc:
        for n, page in enumerate(doc, 1):
            name = f"page_{n:03d}.png"
            page.get_pixmap(dpi=a.dpi, alpha=False).save(str(pages_dir / name))
            extracted = page.get_text("text", sort=True) or ""
            text.append(f"--- Página {n} ---\n{extracted.rstrip()}\n")
            meta.append({"page": n, "image": f"pages/{name}",
                         "width_points": round(page.rect.width, 2), "height_points": round(page.rect.height, 2),
                         "rotation": page.rotation,
                         "extracted_text_characters": len(extracted.strip()),
                         "layout": page_layout(page)})
    (a.output_dir / "extracted_text.txt").write_text("\n".join(text), encoding="utf-8")
    (a.output_dir / "metadata.json").write_text(json.dumps({
        "source_pdf": a.pdf.name, "source_pdf_path": str(a.pdf.resolve()),
        "page_count": len(meta), "render_dpi": a.dpi,
        "bbox_format": "normalizado [x0,y0,x1,y1] em relação à imagem renderizada da página",
        "pages": meta}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n_caps = sum(len(m["layout"]["captions"]) for m in meta)
    print(f"Renderizadas {len(meta)} páginas em {pages_dir}")
    print(f"Legendas detectadas: {n_caps} (caixas em metadata.json, campo 'layout')")


if __name__ == "__main__":
    main()

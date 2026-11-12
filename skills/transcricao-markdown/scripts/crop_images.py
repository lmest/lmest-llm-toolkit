#!/usr/bin/env python3
"""Gera recortes de imagens a partir de um manifesto JSON."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Dependência ausente: instale Pillow (pip install Pillow).") from exc

GENERATED_LIST = "generated_files.json"
DEFAULT_FIGURE_DPI = 300


def open_pdf(pdf_arg, pages_dir):
    """Abre o PDF de origem (argumento --pdf ou metadata.json); devolve None se indisponível."""
    pdf = pdf_arg
    if pdf is None:
        meta = pages_dir.parent / "metadata.json"
        try:
            candidate = json.loads(meta.read_text(encoding="utf-8")).get("source_pdf_path")
            pdf = Path(candidate) if candidate else None
        except (OSError, json.JSONDecodeError):
            pdf = None
    if pdf is None or not pdf.is_file():
        if pdf_arg is not None:
            fail(f"PDF não encontrado: {pdf_arg}")
        return None
    try:
        import pymupdf
        return pymupdf.open(pdf)
    except ImportError:
        print("AVISO: PyMuPDF ausente; figuras serão recortadas da imagem da página.")
    except Exception as exc:
        print(f"AVISO: não foi possível abrir {pdf} ({exc}); figuras serão recortadas da imagem da página.")
    return None


def render_from_pdf(doc, page_number, bbox, dpi, out):
    """Renderiza só a região da figura direto do PDF, na resolução pedida."""
    import pymupdf
    page = doc[page_number - 1]
    w, h = page.rect.width, page.rect.height  # dimensões da página como exibida (com rotação)
    x0, y0, x1, y1 = bbox
    # get_pixmap interpreta 'clip' nas coordenadas da página exibida (já rotacionada).
    clip = pymupdf.Rect(x0*w, y0*h, x1*w, y1*h)
    page.get_pixmap(dpi=dpi, clip=clip, alpha=False).save(str(out))


def fail(msg):
    raise SystemExit(f"Erro: {msg}")


def safe_id(value, page, kind):
    if value is None or str(value).strip() == "":
        fail(f"toda entrada de '{kind}' precisa de um 'id' explícito (página {page})")
    clean = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value)).strip("_")
    if not clean:
        fail(f"id sem caracteres válidos em '{kind}' (página {page}): {value!r}")
    return clean


def get_bbox(region, page, rid):
    bbox = region.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(x, (int, float)) for x in bbox):
        fail(f"bbox inválida: página {page}, região {rid}")
    x0, y0, x1, y1 = bbox
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        fail(f"bbox fora do intervalo normalizado: página {page}, região {rid}")
    return bbox


def validate(pages):
    """Valida o manifesto inteiro antes de gravar qualquer arquivo."""
    seen_pages = set()
    for entry in pages:
        n = entry.get("page")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            fail("cada página precisa de um 'page' inteiro positivo")
        if n in seen_pages:
            fail(f"página {n} aparece mais de uma vez no manifesto")
        seen_pages.add(n)
        for kind in ("regions", "image_regions"):
            items = entry.get(kind, [])
            if not isinstance(items, list):
                fail(f"'{kind}' deve ser uma lista: página {n}")
            ids = {}
            for r in items:
                rid = safe_id(r.get("id"), n, kind)
                if rid in ids:
                    fail(f"id duplicado em '{kind}' na página {n}: {rid!r} "
                         f"(ids originais {ids[rid]!r} e {r.get('id')!r})")
                ids[rid] = r.get("id")
                get_bbox(r, n, rid)
                if kind == "regions":
                    parts = r.get("horizontal_parts", 1); overlap = r.get("overlap", 0.0)
                    if not isinstance(parts, int) or isinstance(parts, bool) or parts < 1:
                        fail(f"horizontal_parts deve ser inteiro positivo: página {n}, região {rid}")
                    if not isinstance(overlap, (int, float)) or not 0 <= overlap < 1:
                        fail(f"overlap deve estar em [0,1): página {n}, região {rid}")


def rel(path, base):
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--pages-dir", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--images-output-dir", type=Path,
                   help="Diretório para recortes de figuras (padrão: pasta irmã 'images' de --output-dir)")
    p.add_argument("--generated-list", type=Path,
                   help=f"Lista dos arquivos gerados (padrão: '{GENERATED_LIST}' na pasta-mãe de --output-dir)")
    p.add_argument("--pdf", type=Path,
                   help="PDF de origem para renderizar as figuras em alta resolução "
                        "(padrão: 'source_pdf_path' de metadata.json, ao lado de --pages-dir)")
    p.add_argument("--figure-dpi", type=int, default=DEFAULT_FIGURE_DPI,
                   help=f"Resolução das figuras renderizadas do PDF (padrão: {DEFAULT_FIGURE_DPI})")
    p.add_argument("--figures-from-pages", action="store_true",
                   help="Recorta as figuras da imagem da página em vez de renderizá-las do PDF")
    a = p.parse_args()
    if not 72 <= a.figure_dpi <= 1200:
        fail("--figure-dpi deve estar entre 72 e 1200")
    try:
        manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"não foi possível ler o manifesto {a.manifest}: {exc}")
    pages = manifest.get("pages")
    if not isinstance(pages, list):
        fail("o manifesto deve conter uma lista 'pages'")
    validate(pages)

    images_output_dir = a.images_output_dir or a.output_dir.parent / "images"
    list_path = a.generated_list or a.output_dir.parent / GENERATED_LIST
    base = list_path.parent
    a.output_dir.mkdir(parents=True, exist_ok=True)
    crops, images = [], []
    doc = None if a.figures_from_pages else open_pdf(a.pdf, a.pages_dir)
    if doc is not None:
        for entry in pages:
            if entry["page"] > doc.page_count:
                fail(f"página {entry['page']} não existe no PDF ({doc.page_count} páginas)")
    figure_source = f"pdf@{a.figure_dpi}dpi" if doc is not None else "page_png"

    for entry in pages:
        n = entry["page"]
        src = a.pages_dir / Path(entry.get("image", f"page_{n:03d}.png")).name
        if not src.is_file():
            fail(f"imagem não encontrada: {src}")
        with Image.open(src) as opened:
            im = opened.convert("RGB")
        w, h = im.size
        for r in entry.get("regions", []):
            rid = safe_id(r.get("id"), n, "regions"); x0, y0, x1, y1 = r["bbox"]
            crop = im.crop((round(x0*w), round(y0*h), round(x1*w), round(y1*h)))
            parts = r.get("horizontal_parts", 1); overlap = r.get("overlap", 0.0)
            cw, ch = crop.size
            if parts == 1:
                out = a.output_dir / f"p{n:03d}_{rid}.png"; crop.save(out); crops.append(out); continue
            # Faixas de mesma altura com a sobreposição pedida; a união cobre exatamente a região.
            nominal = ch/(parts-(parts-1)*overlap); step = nominal*(1-overlap)
            for i in range(parts):
                top = round(i*step); bottom = ch if i == parts-1 else min(ch, round(top+nominal))
                if bottom <= top:
                    fail(f"recorte vazio (página {n}, região {rid}); reduza a sobreposição ou o número de partes")
                out = a.output_dir / f"p{n:03d}_{rid}_part{i+1:02d}.png"
                crop.crop((0, top, cw, bottom)).save(out); crops.append(out)
        for r in entry.get("image_regions", []):
            rid = safe_id(r.get("id"), n, "image_regions"); x0, y0, x1, y1 = r["bbox"]
            images_output_dir.mkdir(parents=True, exist_ok=True)
            out = images_output_dir / f"p{n:03d}_{rid}.png"
            if doc is not None:
                render_from_pdf(doc, n, (x0, y0, x1, y1), a.figure_dpi, out)
            else:
                im.crop((round(x0*w), round(y0*h), round(x1*w), round(y1*h))).save(out)
            images.append(out)
    if doc is not None:
        doc.close()

    # Conta somente arquivos realmente presentes no disco, sem duplicatas.
    crops = sorted({c.resolve() for c in crops if c.is_file()})
    images = sorted({i.resolve() for i in images if i.is_file()})
    generated = set(crops) | set(images)

    # PNGs que sobraram de execuções anteriores e não foram gerados agora.
    stale = []
    for d in sorted({a.output_dir.resolve(), images_output_dir.resolve()}):
        if d.is_dir():
            stale += [f for f in sorted(d.glob("*.png")) if f.resolve() not in generated]

    list_path.parent.mkdir(parents=True, exist_ok=True)
    list_path.write_text(json.dumps({
        "manifest": rel(a.manifest, base),
        "crops": [rel(c, base) for c in crops],
        "images": [rel(i, base) for i in images],
        "figure_source": figure_source,
        "stale_files": [rel(s, base) for s in stale],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Criados {len(crops)} recorte(s) de leitura em {a.output_dir}")
    origem = (f"renderizadas do PDF a {a.figure_dpi} DPI" if doc is not None
              else "recortadas da imagem da página")
    print(f"Criados {len(images)} recorte(s) de figuras em {images_output_dir} ({origem})")
    print(f"Lista de arquivos gerados: {list_path}")
    if stale:
        print(f"AVISO: {len(stale)} arquivo(s) antigo(s) não pertencem a esta execução "
              f"(apague-os ou confira o manifesto):")
        for s in stale:
            print(f"  - {rel(s, base)}")


if __name__ == "__main__":
    main()

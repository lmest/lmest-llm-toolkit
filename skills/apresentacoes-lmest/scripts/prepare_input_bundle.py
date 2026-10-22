#!/usr/bin/env python3
"""Extrai, valida e inventaria a entrada de uma apresentação.

Entradas aceitas (nada é alterado na origem; tudo é copiado para ``<saida>``):

- PPTX a reconstruir no padrão LMEst: ``.pptx`` (inventário, mídia extraída e
  render de todos os slides para conferência);
- Markdown + imagens (preferida): ``.zip``, pasta ou ``.md`` solto. As imagens
  podem vir em um diretório/ZIP separado com ``--imagens``;
- PDF (alternativa, resultados piores): ``.pdf``, ou ZIP/pasta contendo só um
  PDF. Gera um rascunho de Markdown para revisão e sai com código 5.

    python3 scripts/prepare_input_bundle.py ENTRADA SAIDA [--imagens DIR_OU_ZIP]

Gera ``SAIDA/input_manifest.json`` e imprime o mesmo JSON.

Códigos de saída:
    0  tudo certo (avisos podem existir)
    2  imagens referenciadas ausentes ou fora do pacote
    3  dados da capa incompletos/ambíguos (front matter)
    4  pacote inválido/inseguro, Markdown principal ambíguo ou PPTX inválido/
       não renderizável
    5  entrada em PDF convertida em rascunho: revisar, completar o front matter
       e rodar de novo sobre a pasta do rascunho
    6  blockquote vazio ou fora da posição reservada para descrição
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_to_markdown import convert as pdf_convert  # noqa: E402
from extract_pptx_content import extract_pptx  # noqa: E402
from lmest_markdown import (  # noqa: E402
    MarkdownBlockquoteError, cover_data, find_images, find_math, line_of, slide_for_line,
    split_front_matter, split_slides,
)

SKILL_DIR = Path(__file__).resolve().parents[1]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".bmp", ".tif", ".tiff"}
MARKDOWN_CANDIDATES = ("apresentacao.md", "slides.md", "presentation.md", "deck.md")
MAX_UNCOMPRESSED = 1_000 * 1024 * 1024  # 1 GB
AVISO_PDF = ("A entrada é um PDF. A conversão é aproximada: equações precisam ser transcritas, "
             "gráficos vetoriais e a ordem do texto podem se perder e os dados da capa precisam ser "
             "confirmados. Um arquivo Markdown com um diretório de imagens é mais efetivo e gera "
             "resultados melhores.")


class BundleError(Exception):
    def __init__(self, code: int, msg: str):
        super().__init__(msg)
        self.code = code


def is_junk(rel: str) -> bool:
    parts = PurePosixPath(rel.replace("\\", "/")).parts
    return any(p == "__MACOSX" or p.startswith("._") or p in (".DS_Store", "Thumbs.db") for p in parts)


def safe_extract(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        total = 0
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if is_junk(name):
                continue
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or re.match(r"^[A-Za-z]:", name):
                raise BundleError(4, f"ZIP inseguro: caminho inválido '{info.filename}'.")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise BundleError(4, f"ZIP contém link simbólico: '{info.filename}'.")
            total += info.file_size
            if total > MAX_UNCOMPRESSED:
                raise BundleError(4, "ZIP excede 1 GB descompactado.")
            target = dest / p
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)


def copy_single_markdown(md: Path, dest: Path) -> None:
    shutil.copy2(md, dest / md.name)
    text = md.read_text(encoding="utf-8")
    for ref, _ in find_images(text):
        if re.match(r"^(https?:|data:)", ref, re.I) or ref.startswith("/"):
            continue
        src = (md.parent / ref).resolve()
        try:
            src.relative_to(md.parent.resolve())
        except ValueError:
            continue
        if src.is_file():
            target = dest / ref
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)


def find_markdown(root: Path) -> Path:
    files = sorted(p for p in root.rglob("*.md")
                   if p.is_file() and not is_junk(p.relative_to(root).as_posix()))
    if not files:
        raise BundleError(4, "Nenhum arquivo Markdown foi encontrado.")
    preferred = [p for p in files if p.name.lower() in MARKDOWN_CANDIDATES]
    if len(preferred) == 1:
        return preferred[0]
    if len(files) == 1:
        return files[0]
    names = ", ".join(p.relative_to(root).as_posix() for p in files)
    raise BundleError(4, f"Mais de um Markdown e nenhum principal inequívoco ({names}). "
                         "Renomeie o principal para apresentacao.md.")


def resolve_images(md: Path, root: Path, refs: list[tuple[str, int]]) -> tuple[list[dict], list[dict]]:
    found, missing = [], []
    for ref, line in refs:
        if re.match(r"^(https?:|data:)", ref, re.I):
            missing.append({"ref": ref, "line": line, "motivo": "imagem remota/data URI: inclua o arquivo no pacote"})
            continue
        target = (md.parent / ref).resolve()
        try:
            rel = target.relative_to(root.resolve()).as_posix()
        except ValueError:
            missing.append({"ref": ref, "line": line, "motivo": "caminho aponta para fora do pacote"})
            continue
        if not target.is_file():
            # tolera diferença de maiúsculas/minúsculas, comum em ZIPs feitos no Windows
            alt = [p for p in root.rglob("*") if p.is_file() and p.relative_to(root).as_posix().lower() == rel.lower()]
            if len(alt) == 1:
                found.append({"ref": ref, "line": line, "path": alt[0].relative_to(root).as_posix(),
                              "aviso": "maiúsculas/minúsculas diferentes"})
                continue
            # imagens enviadas soltas ou em diretório separado: casa pelo nome do arquivo
            same = [p for p in root.rglob("*") if p.is_file() and p.name.lower() == Path(ref).name.lower()
                    and not is_junk(p.relative_to(root).as_posix())]
            if len(same) == 1:
                found.append({"ref": ref, "line": line, "path": same[0].relative_to(root).as_posix(),
                              "aviso": "localizada pelo nome do arquivo"})
                continue
            motivo = "arquivo não encontrado" if not same else f"nome ambíguo ({len(same)} arquivos com esse nome)"
            missing.append({"ref": ref, "line": line, "motivo": motivo})
            continue
        found.append({"ref": ref, "line": line, "path": rel})
    return found, missing


def add_images(src: Path, extract: Path) -> None:
    """Copia um diretório/ZIP de imagens enviado à parte para dentro do pacote."""
    if not src.exists():
        raise BundleError(4, f"Diretório de imagens não encontrado: {src}")
    dest = extract / src.stem if src.suffix.lower() == ".zip" else extract / src.name
    if src.is_dir():
        for p in src.rglob("*"):
            rel = p.relative_to(src).as_posix()
            # só imagens: a pasta pode ser a de uploads, com o próprio .md ou outros arquivos
            if p.is_file() and not is_junk(rel) and p.suffix.lower() in IMAGE_EXTENSIONS:
                (dest / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest / rel)
    elif src.suffix.lower() == ".zip":
        dest.mkdir(parents=True, exist_ok=True)
        safe_extract(src, dest)
        for p in list(dest.rglob("*")):
            if p.is_file() and p.suffix.lower() not in IMAGE_EXTENSIONS:
                p.unlink()
    else:
        raise BundleError(4, "--imagens deve ser um diretório ou um .zip.")


def find_lone_pdf(root: Path) -> Path | None:
    """PDF é usado só quando não há Markdown no pacote."""
    files = [p for p in root.rglob("*") if p.is_file() and not is_junk(p.relative_to(root).as_posix())]
    if any(p.suffix.lower() in (".md", ".markdown") for p in files):
        return None
    pdfs = [p for p in files if p.suffix.lower() == ".pdf"]
    if len(pdfs) > 1:
        raise BundleError(4, "Mais de um PDF e nenhum Markdown: envie um único PDF de conteúdo.")
    return pdfs[0] if pdfs else None


def handle_pdf(pdf: Path, out: Path, report: dict) -> int:
    result = pdf_convert(pdf, out / "pdf_rascunho", out / "pdf_paginas")
    report.update({
        "origem": "pdf",
        "aviso_pdf": AVISO_PDF,
        "pdf": pdf.name,
        **result,
        "proximo_passo": ("Revise pdf_rascunho/apresentacao.md olhando pdf_paginas/, corrija estrutura e "
                          "texto, transcreva equações em LaTeX, adicione o front matter confirmado pelo "
                          "usuário e rode: prepare_input_bundle.py <saida>/pdf_rascunho <saida>"),
    })
    report["avisos"].append(AVISO_PDF)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    (out / "input_manifest.json").write_text(payload, encoding="utf-8")
    print(payload)
    return 5


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", help=".pptx, .zip, pasta, .md ou .pdf")
    ap.add_argument("saida", help="pasta de trabalho")
    ap.add_argument("--imagens", help="diretório ou .zip de imagens enviado separadamente do Markdown")
    args = ap.parse_args()

    src = Path(args.entrada).resolve()
    out = Path(args.saida).resolve()
    out.mkdir(parents=True, exist_ok=True)
    extract = out / "extracted"
    if extract.exists():
        shutil.rmtree(extract)
    extract.mkdir(parents=True)

    report: dict = {"entrada": str(src), "origem": "markdown", "extracted_dir": str(extract),
                    "erros": [], "avisos": []}
    code = 0
    if src.suffix.lower() == ".pptx":
        report["origem"] = "pptx"
        if args.imagens:
            report["erros"].append("A opção --imagens é exclusiva da entrada Markdown; as mídias do PPTX são extraídas automaticamente.")
            payload = json.dumps(report, ensure_ascii=False, indent=2)
            (out / "input_manifest.json").write_text(payload, encoding="utf-8")
            print(payload)
            return 4
        try:
            result = extract_pptx(src, out, extract)
            report.update(result)
            report["entrada"] = str(src)
            report["extracted_dir"] = str(extract)
        except (ValueError, RuntimeError, OSError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
            report["erros"].append(str(exc))
            code = 4
        payload = json.dumps(report, ensure_ascii=False, indent=2)
        (out / "input_manifest.json").write_text(payload, encoding="utf-8")
        print(payload)
        return code

    try:
        if src.is_dir():
            for p in src.rglob("*"):
                rel = p.relative_to(src).as_posix()
                if p.is_file() and not is_junk(rel):
                    (extract / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, extract / rel)
        elif src.suffix.lower() == ".zip":
            try:
                safe_extract(src, extract)
            except zipfile.BadZipFile as exc:
                raise BundleError(4, f"ZIP inválido: {exc}")
        elif src.suffix.lower() in (".md", ".markdown"):
            copy_single_markdown(src, extract)
        elif src.suffix.lower() == ".pdf":
            shutil.copy2(src, extract / src.name)
        else:
            raise BundleError(4, "Entrada deve ser .pptx, .md, pasta, .zip ou .pdf.")
        if args.imagens:
            add_images(Path(args.imagens).resolve(), extract)
        pdf = find_lone_pdf(extract)
        if pdf is not None:
            return handle_pdf(pdf, out, report)
        md = find_markdown(extract)
    except BundleError as exc:
        report["erros"].append(str(exc))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        (out / "input_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return exc.code

    text = md.read_text(encoding="utf-8-sig")
    if "RASCUNHO gerado a partir de PDF" in text:
        report["origem"] = "pdf_revisado"
        report["avisos"].append(AVISO_PDF)
        pend = [line_of(text, m.start()) for m in re.finditer(r"<!--\s*conferir:", text)]
        if pend:
            report["avisos"].append(f"Rascunho do PDF ainda tem {len(pend)} marcação(ões) 'conferir' "
                                    f"(linhas {pend}): resolva e apague antes de gerar o deck.")
        sem = [line_of(text, m.start()) for m in re.finditer(r"\[sem título", text)]
        if sem:
            report["avisos"].append(f"Slides sem título definido no rascunho (linhas {sem}).")
    front, body, consumed, fm_error = split_front_matter(text)
    try:
        slides = split_slides(body, line_offset=consumed)
    except MarkdownBlockquoteError as exc:
        report["markdown"] = md.relative_to(extract).as_posix()
        report["erros"].append(str(exc))
        payload = json.dumps(report, ensure_ascii=False, indent=2)
        (out / "input_manifest.json").write_text(payload, encoding="utf-8")
        print(payload)
        return 6
    math = find_math(text, include_inline=True)
    images, missing = resolve_images(md, extract, find_images(text))

    cover, cover_errors, cover_warnings = cover_data(front)
    if fm_error:
        cover_errors.insert(0, fm_error)
    if not front and not fm_error:
        cover_errors = ["O Markdown não tem front matter YAML com titulo/autores "
                            "(veja docs/entrada_markdown.md)."]
    report["avisos"].extend(cover_warnings)

    for s in slides:
        if not s.title:
            report["avisos"].append(f"Slide {s.index} (linha {s.start_line}) sem título.")

    all_files = sorted(p.relative_to(extract).as_posix() for p in extract.rglob("*") if p.is_file())
    image_files = [f for f in all_files if Path(f).suffix.lower() in IMAGE_EXTENSIONS]
    used = {i["path"] for i in images}
    unused = [f for f in image_files if f not in used]
    if unused:
        report["avisos"].append(f"{len(unused)} imagem(ns) no pacote não referenciada(s) no Markdown.")

    eq_entries = []
    for m in math:
        s = slide_for_line(slides, m.line)
        eq_entries.append({"kind": m.kind, "line": m.line, "slide": s.index if s else None, "latex": m.latex})

    report.update({
        "markdown": md.relative_to(extract).as_posix(),
        "capa": cover,
        "slides": [{
            "index": s.index, "tipo": s.kind, "titulo": s.title,
            "linhas": [s.start_line, s.end_line],
            "description": s.description,
            "literal": s.literal, "notas": s.notes,
            "imagens": [{"ref": r, "path": next((i["path"] for i in images if i["ref"] == r), None)}
                        for r in s.images],
            "equacoes": sum(1 for e in eq_entries if e["slide"] == s.index),
        } for s in slides],
        "imagens_no_pacote": image_files,
        "imagens_referenciadas": images,
        "imagens_ausentes": missing,
        "imagens_nao_usadas": unused,
        "equacoes": eq_entries,
        "resumo": {
            "slides": len(slides), "divisores": sum(1 for s in slides if s.kind == "divisor"),
            "imagens_no_pacote": len(image_files), "imagens_referenciadas": len(images),
            "imagens_ausentes": len(missing),
            "equacoes_display": sum(1 for e in eq_entries if e["kind"] == "display"),
            "equacoes_inline": sum(1 for e in eq_entries if e["kind"] == "inline"),
        },
    })
    if missing:
        report["erros"].append(f"{len(missing)} imagem(ns) referenciada(s) indisponível(is).")
        code = 2
    if cover_errors:
        report["erros"].extend(cover_errors)
        code = code or 3

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    (out / "input_manifest.json").write_text(payload, encoding="utf-8")
    print(payload)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

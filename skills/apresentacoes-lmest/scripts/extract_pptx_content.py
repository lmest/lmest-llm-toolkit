#!/usr/bin/env python3
"""Inventaria conteúdo visível de um PPTX e renderiza todos os slides.

Uso direto:
    python3 scripts/extract_pptx_content.py origem.pptx work

O manifesto resultante é um inventário assistido, não uma transcrição
garantida. Conferir cada elemento contra ``source_render/slide-NNN.png`` antes
de reconstruir o deck, sobretudo equações, diagramas e objetos incorporados.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from lxml import etree

SKILL_DIR = Path(__file__).resolve().parents[1]
RENDER_SCRIPT = Path(__file__).resolve().with_name("render_deck.py")
MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
MATH_TEXT_RE = re.compile(r"(?:\\(?:frac|sum|int|sqrt|lim|begin\{|alpha|beta|omega|theta)|[=<>±×÷∑∫√∞]|_[{\w]|\^[{\w])")


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _bbox(shape: Any, coordinate_space: str) -> dict[str, Any]:
    result: dict[str, Any] = {"unidade": "EMU", "referencial": coordinate_space}
    for key, attr in (("x", "left"), ("y", "top"), ("largura", "width"), ("altura", "height")):
        try:
            result[key] = int(getattr(shape, attr))
        except (AttributeError, TypeError, ValueError):
            result[key] = None
    return result


def _color(color: Any) -> dict[str, str] | None:
    try:
        if color.type is None:
            return None
        if color.rgb is not None:
            return {"rgb": str(color.rgb)}
    except (AttributeError, TypeError, ValueError):
        pass
    try:
        if color.theme_color is not None:
            return {"tema": str(color.theme_color)}
    except (AttributeError, TypeError, ValueError):
        pass
    return None


def _shape_style(shape: Any) -> dict[str, Any]:
    style: dict[str, Any] = {}
    try:
        fill = shape.fill
        style["preenchimento"] = {"tipo": str(fill.type), "cor": _color(fill.fore_color)}
    except (AttributeError, TypeError, ValueError):
        pass
    try:
        line = shape.line
        style["linha"] = {"cor": _color(line.color), "largura_emu": int(line.width) if line.width else None}
    except (AttributeError, TypeError, ValueError):
        pass
    return style


def _text(shape: Any) -> str | None:
    try:
        if shape.has_text_frame:
            text = shape.text.strip()
            return text or None
    except (AttributeError, TypeError, ValueError):
        pass
    return None


def _math_nodes(shape: Any) -> list[str]:
    found: list[str] = []
    try:
        root = shape._element
        for node in root.iter():
            qname = etree.QName(node)
            if qname.namespace == MATH_NS and qname.localname in {"oMath", "oMathPara"}:
                found.append(etree.tostring(node, encoding="unicode"))
    except (AttributeError, TypeError, ValueError):
        pass
    return found


def _chart_data(chart: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"tipo": str(chart.chart_type), "series": []}
    try:
        if chart.has_title:
            data["titulo"] = chart.chart_title.text_frame.text.strip()
    except (AttributeError, TypeError, ValueError):
        pass
    axes = {}
    for key, attr in (("x", "category_axis"), ("y", "value_axis")):
        try:
            axis = getattr(chart, attr)
            if axis.has_title:
                axes[key] = axis.axis_title.text_frame.text.strip()
        except (AttributeError, TypeError, ValueError):
            continue
    if axes:
        data["eixos"] = axes
    try:
        plots = list(chart.plots)
        if plots:
            cats = []
            try:
                for cat in plots[0].categories:
                    cats.append(_json_value(getattr(cat, "label", cat)))
            except (AttributeError, TypeError, ValueError, KeyError):
                pass
            if cats:
                data["categorias"] = cats
    except (AttributeError, TypeError, ValueError):
        plots = []
    try:
        for series in chart.series:
            row: dict[str, Any] = {"nome": _json_value(getattr(series, "name", None))}
            try:
                row["valores"] = [_json_value(v) for v in series.values]
            except (AttributeError, TypeError, ValueError):
                pass
            try:
                row["x"] = [_json_value(v) for v in series.x_values]
            except (AttributeError, TypeError, ValueError):
                pass
            data["series"].append(row)
    except (AttributeError, TypeError, ValueError, KeyError) as exc:
        data["erro_extracao"] = str(exc)
    return data


def _table_data(table: Any) -> dict[str, Any]:
    rows = [[cell.text for cell in row.cells] for row in table.rows]
    return {
        "linhas": rows,
        "larguras_colunas_emu": [int(col.width) for col in table.columns],
        "alturas_linhas_emu": [int(row.height) for row in table.rows],
    }


def _connector_data(shape: Any) -> dict[str, Any]:
    info: dict[str, Any] = {}
    try:
        info["flip_h"] = bool(shape.flip_h)
        info["flip_v"] = bool(shape.flip_v)
    except (AttributeError, TypeError, ValueError):
        pass
    try:
        endpoints = []
        for node in shape._element.iter():
            name = etree.QName(node).localname
            if name in {"stCxn", "endCxn"}:
                endpoints.append({
                    "extremidade": "inicio" if name == "stCxn" else "fim",
                    "shape_id": node.get("id"), "site": node.get("idx"),
                })
        if endpoints:
            info["conexoes"] = endpoints
    except (AttributeError, TypeError, ValueError):
        pass
    return info


def _placeholder(shape: Any) -> str | None:
    try:
        if shape.is_placeholder:
            return str(shape.placeholder_format.type)
    except (AttributeError, TypeError, ValueError):
        pass
    return None


def _extract_slide(slide: Any, slide_index: int, media_dir: Path) -> tuple[dict[str, Any], list[str]]:
    elements: list[dict[str, Any]] = []
    warnings: list[str] = []
    media_dir.mkdir(parents=True, exist_ok=True)
    counter = 0

    def visit(shapes: Any, parent_id: int | None = None, coordinate_space: str = "slide") -> None:
        nonlocal counter
        for shape in shapes:
            counter += 1
            element_id = counter
            shape_type = getattr(shape, "shape_type", None)
            shape_type_name = str(shape_type) if shape_type is not None else "unknown"
            try:
                shape_name = shape.name
            except (AttributeError, TypeError, ValueError):
                shape_name = f"shape-{element_id}"

            text = _text(shape)
            has_table = bool(getattr(shape, "has_table", False))
            has_chart = bool(getattr(shape, "has_chart", False))
            is_picture = shape_type_name.startswith(("PICTURE", "LINKED_PICTURE"))
            is_connector = shape_type_name.startswith("LINE") or "cxnSp" in getattr(shape, "_element", object()).tag
            is_group = shape_type_name.startswith("GROUP")
            if has_table:
                kind = "tabela"
            elif has_chart:
                kind = "grafico"
            elif is_picture:
                kind = "imagem"
            elif is_connector:
                kind = "conector"
            elif is_group:
                kind = "grupo"
            elif text:
                kind = "texto"
            elif shape_type_name.startswith(("DIAGRAM", "IGX_GRAPHIC")):
                kind = "diagrama_nao_estruturado"
            elif shape_type_name.startswith(("EMBEDDED_OLE", "LINKED_OLE", "MEDIA", "WEB_VIDEO")):
                kind = "objeto_incorporado"
            else:
                kind = "forma"

            item: dict[str, Any] = {
                "id": element_id,
                "kind": kind,
                "nome": shape_name,
                "tipo_powerpoint": shape_type_name,
                "posicao": _bbox(shape, coordinate_space),
                "estilo": _shape_style(shape),
            }
            if parent_id is not None:
                item["grupo_pai"] = parent_id
            placeholder = _placeholder(shape)
            if placeholder:
                item["placeholder"] = placeholder
            if text:
                item["texto"] = text
            if has_table:
                try:
                    item["dados"] = _table_data(shape.table)
                except (AttributeError, TypeError, ValueError, IndexError) as exc:
                    item["erro_extracao"] = f"tabela: {exc}"
                    warnings.append(f"Elemento {element_id}: não foi possível extrair todos os dados da tabela.")
            if has_chart:
                try:
                    item["dados"] = _chart_data(shape.chart)
                    if item["dados"].get("erro_extracao"):
                        warnings.append(f"Elemento {element_id}: dados de gráfico incompletos; conferir a renderização.")
                except (AttributeError, TypeError, ValueError, KeyError) as exc:
                    item["erro_extracao"] = f"gráfico: {exc}"
                    warnings.append(f"Elemento {element_id}: não foi possível extrair os dados do gráfico.")
            if is_picture:
                try:
                    image = shape.image
                    ext = re.sub(r"[^a-zA-Z0-9]", "", image.ext.lower()) or "bin"
                    rel = Path("extracted") / "pptx_media" / f"slide-{slide_index:03d}-element-{element_id:03d}.{ext}"
                    dest = media_dir / rel.name
                    dest.write_bytes(image.blob)
                    item["midia"] = {"path": rel.as_posix(), "extensao": ext, "content_type": image.content_type}
                    try:
                        item["recorte"] = {"esquerda": shape.crop_left, "direita": shape.crop_right,
                                            "topo": shape.crop_top, "base": shape.crop_bottom}
                    except (AttributeError, TypeError, ValueError):
                        pass
                except (AttributeError, TypeError, ValueError, OSError) as exc:
                    item["erro_extracao"] = f"imagem: {exc}"
                    warnings.append(f"Elemento {element_id}: não foi possível extrair a mídia da imagem.")
            if is_connector:
                item["conector"] = _connector_data(shape)
            math_nodes = _math_nodes(shape)
            if math_nodes:
                item["candidato_equacao"] = {"deteccao": "OMML", "omml": math_nodes}
            elif text and MATH_TEXT_RE.search(text):
                item["candidato_equacao"] = {"deteccao": "heuristica_textual", "texto": text}
            if is_group:
                try:
                    item["filhos"] = []
                    elements.append(item)
                    start = len(elements)
                    visit(shape.shapes, element_id, "grupo")
                    item["filhos"] = [el["id"] for el in elements[start:]]
                    continue
                except (AttributeError, TypeError, ValueError):
                    warnings.append(f"Grupo {element_id}: conteúdo interno não totalmente acessível pelo extrator.")
            if kind in {"diagrama_nao_estruturado", "objeto_incorporado"}:
                warnings.append(f"Elemento {element_id} ({kind}): conferir visualmente e reconstruir ou preservar como figura.")
            elements.append(item)

    visit(slide.shapes)

    title = None
    title_source = None
    for shape in slide.shapes:
        text = _text(shape)
        placeholder = (_placeholder(shape) or "").upper()
        if text and ("TITLE" in placeholder or "CENTER_TITLE" in placeholder):
            title, title_source = text.splitlines()[0], "placeholder_titulo"
            break
    if title is None:
        for element in elements:
            text = element.get("texto")
            if text and text.strip():
                title, title_source = text.splitlines()[0].strip(), "primeiro_texto"
                break
    if not title:
        title_source = "ausente"
    return {"index": slide_index, "titulo": title, "titulo_origem": title_source,
            "elementos": elements, "render": f"source_render/slide-{slide_index:03d}.png",
            "avisos": warnings}, warnings


def extract_pptx(pptx_path: Path, work_dir: Path, extract_dir: Path | None = None) -> dict[str, Any]:
    """Extract structured slide content and source renders into work_dir."""
    pptx_path = pptx_path.resolve()
    work_dir = work_dir.resolve()
    extract_dir = (extract_dir or work_dir / "extracted").resolve()
    if not pptx_path.is_file() or pptx_path.suffix.lower() != ".pptx":
        raise ValueError(f"Arquivo PPTX não encontrado: {pptx_path}")
    extract_dir.mkdir(parents=True, exist_ok=True)
    render_dir = work_dir / "source_render"
    shutil.rmtree(render_dir, ignore_errors=True)
    copy_path = extract_dir / "origem.pptx"
    if pptx_path != copy_path.resolve():
        shutil.copy2(pptx_path, copy_path)
    media_dir = extract_dir / "pptx_media"
    shutil.rmtree(media_dir, ignore_errors=True)
    media_dir.mkdir(parents=True, exist_ok=True)

    try:
        from pptx import Presentation
        prs = Presentation(str(copy_path))
    except Exception as exc:
        raise ValueError(f"Não foi possível abrir o PPTX '{pptx_path.name}': {exc}") from exc
    if not prs.slides:
        raise ValueError("O PPTX não contém slides.")

    slides: list[dict[str, Any]] = []
    for index, slide in enumerate(prs.slides, start=1):
        slide_info, _ = _extract_slide(slide, index, media_dir)
        slides.append(slide_info)

    proc = subprocess.run([sys.executable, str(RENDER_SCRIPT), str(copy_path), str(render_dir), "--preserve-aspect"],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=1200)
    if proc.returncode != 0:
        raise RuntimeError("Falha ao renderizar os slides do PPTX de origem. " + proc.stdout[-3000:])
    missing_renders = [s["render"] for s in slides if not (work_dir / s["render"]).is_file()]
    if missing_renders:
        raise RuntimeError("A renderização não gerou todas as páginas: " + ", ".join(missing_renders))

    warnings = [warning for slide in slides for warning in slide["avisos"]]
    return {
        "origem": "pptx",
        "pptx": "extracted/origem.pptx",
        "slides": slides,
        "tamanho_emu": [int(prs.slide_width), int(prs.slide_height)],
        "render_dir": "source_render",
        "resumo": {
            "slides": len(slides),
            "elementos": sum(len(s["elementos"]) for s in slides),
            "candidatos_equacao": sum(1 for s in slides for e in s["elementos"] if e.get("candidato_equacao")),
            "imagens_extraidas": sum(1 for s in slides for e in s["elementos"] if e.get("midia")),
        },
        "avisos": warnings,
        "revisao_visual_obrigatoria": True,
        "slides_candidatos_capa_agradecimentos": {"abertura": 1, "encerramento": len(slides)},
        "confirmar_dados_capa_agradecimentos": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", help="arquivo de origem .pptx")
    parser.add_argument("saida", help="diretório de trabalho para inventário e renders")
    args = parser.parse_args()
    out = Path(args.saida).resolve()
    out.mkdir(parents=True, exist_ok=True)
    try:
        result = extract_pptx(Path(args.pptx), out)
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
        payload = {"entrada": str(Path(args.pptx).resolve()), "origem": "pptx", "erros": [str(exc)]}
        (out / "input_manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 4
    result["entrada"] = str(Path(args.pptx).resolve())
    (out / "input_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verifica invariantes do deck renderizado e gera pares para inspeção visual.

    python3 scripts/evaluate_render.py work/render --plano work/deck_plan.json \
      --referencias work/reference_render

Cada comparação coloca o slide final ao lado da referência indicada por
``source_slide``. As diferenças de conteúdo são esperadas; aprovação visual é
responsabilidade do agente, que inspeciona cada render em tamanho completo.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

W, H = 1920, 1080
MANDATORY_FIRST = 1
MANDATORY_LAST = 19


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("render_dir", help="diretório com slide-NNN.png do deck final")
    ap.add_argument("--plano", required=True, help="deck_plan.json de assemble_deck.py")
    ap.add_argument("--referencias", required=True, help="renders temporários do PPTX-base")
    ap.add_argument("--entrada-pptx-render", help="renders dos slides PPTX de origem para comparar conteúdo reconstruído")
    args = ap.parse_args()

    render = Path(args.render_dir)
    refs = Path(args.referencias)
    plan = json.loads(Path(args.plano).read_text(encoding="utf-8"))["slides"]
    comparisons = render / "comparacoes"
    comparisons.mkdir(parents=True, exist_ok=True)
    rendered = {int(f.stem.split("-")[-1]): f for f in render.glob("slide-*.png")
                if f.stem.split("-")[-1].isdigit()}
    expected_numbers = set(range(1, len(plan) + 1))
    errors: list[str] = []
    results = []

    if len(plan) < 2 or plan[0].get("source_slide") != MANDATORY_FIRST:
        errors.append("A primeira página do plano precisa usar a capa, source_slide 1.")
    if len(plan) < 2 or plan[-1].get("source_slide") != MANDATORY_LAST:
        errors.append("A última página do plano precisa usar agradecimentos, source_slide 19.")
    source_indices = [entry.get("source_slide") for entry in plan]
    if source_indices.count(MANDATORY_FIRST) != 1 or source_indices.count(MANDATORY_LAST) != 1:
        errors.append("Capa e agradecimentos precisam aparecer uma única vez.")
    for field, label in (("md_slide", "Markdown"), ("input_slide", "PPTX de origem")):
        indices = [entry.get(field) for entry in plan if field in entry]
        if any(not isinstance(i, int) or isinstance(i, bool) or i < 1 for i in indices):
            errors.append(f"Índices {field} devem ser inteiros positivos.")
        if indices != sorted(indices):
            errors.append(f"Os slides de {label} aparecem fora da ordem original no plano.")
    input_indices = [entry["input_slide"] for entry in plan if isinstance(entry.get("input_slide"), int)]
    source_renders = Path(args.entrada_pptx_render) if args.entrada_pptx_render else None
    if input_indices and source_renders is None:
        errors.append("O plano contém input_slide; informe --entrada-pptx-render para comparar com a fonte.")
    if set(rendered) != expected_numbers:
        errors.append(f"Renders encontrados {sorted(rendered)}; esperados {sorted(expected_numbers)}.")

    for entry in plan:
        number = entry.get("slide")
        source = entry.get("source_slide")
        output_path = rendered.get(number)
        reference_path = refs / f"slide-{source:03d}.png" if isinstance(source, int) else None
        item = {"slide": number, "source_slide": source, "status": "OK", "detalhes": []}
        input_source = entry.get("input_slide")
        if isinstance(input_source, int) and not isinstance(input_source, bool):
            item["input_slide"] = input_source
        if output_path is None or not output_path.exists():
            item["status"] = "FALHA"
            item["detalhes"].append("imagem renderizada ausente")
        else:
            with Image.open(output_path) as im:
                if abs(im.width / im.height - 16 / 9) > 0.01:
                    item["status"] = "FALHA"
                    item["detalhes"].append(f"proporção inesperada: {im.width}x{im.height}")
        if reference_path is None or not reference_path.exists():
            item["status"] = "FALHA"
            item["detalhes"].append(f"prévia de referência ausente: {reference_path}")
        elif output_path and output_path.exists():
            with Image.open(output_path) as out_im, Image.open(reference_path) as ref_im:
                out_im = out_im.convert("RGB").resize((960, 540))
                ref_im = ref_im.convert("RGB").resize((960, 540))
                pair = Image.new("RGB", (1920, 570), "white")
                pair.paste(ref_im, (0, 30))
                pair.paste(out_im, (960, 30))
                draw = ImageDraw.Draw(pair)
                draw.text((12, 8), f"Referência {source}", fill="#152536")
                draw.text((972, 8), f"Slide final {number}", fill="#152536")
                pair.save(comparisons / f"slide-{number:03d}.png")
                item["comparacao"] = str(comparisons / f"slide-{number:03d}.png")
        if isinstance(input_source, int) and not isinstance(input_source, bool) and source_renders is not None:
            origin_path = source_renders / f"slide-{input_source:03d}.png"
            if not origin_path.exists():
                item["status"] = "FALHA"
                item["detalhes"].append(f"render do slide de origem ausente: {origin_path}")
            elif output_path is not None and output_path.exists():
                with Image.open(origin_path) as origin_im, Image.open(output_path) as out_im:
                    def fit(image: Image.Image) -> Image.Image:
                        image = image.convert("RGB")
                        image.thumbnail((960, 540))
                        canvas = Image.new("RGB", (960, 540), "white")
                        canvas.paste(image, ((960 - image.width) // 2, (540 - image.height) // 2))
                        return canvas
                    pair = Image.new("RGB", (1920, 570), "white")
                    pair.paste(fit(origin_im), (0, 30))
                    pair.paste(fit(out_im), (960, 30))
                    draw = ImageDraw.Draw(pair)
                    draw.text((12, 8), f"Origem {input_source}", fill="#152536")
                    draw.text((972, 8), f"Slide final {number}", fill="#152536")
                    comparison_path = comparisons / f"origem-slide-{number:03d}.png"
                    pair.save(comparison_path)
                    item["comparacao_origem"] = str(comparison_path)
        if item["status"] != "OK":
            errors.extend(f"slide {number}: {detail}" for detail in item["detalhes"])
        results.append(item)

    payload = {
        "status": "FALHA" if errors else "RENDERS_PRONTOS_PARA_INSPECAO",
        "slides": results,
        "inspecao_visual_obrigatoria": True,
        "erros": errors,
    }
    (render / "avaliacao.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in results:
        print(f"slide {item['slide']:3} → referência {item['source_slide']}: {item['status']}" +
              (f" ({item['comparacao']})" if item.get("comparacao") else ""))
    print(f"\n{len(results)} slides; {len(errors)} falha(s) estrutural(is). Inspeção visual manual obrigatória.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Monta um deck copiando slides numerados da referência editável.

Exemplo de ``plano.json``:

    {"slides": [
        {"source_slide": 1, "papel": "capa"},
        {"source_slide": 5, "input_slide": 1, "papel": "transicao"},
        {"source_slide": 2, "input_slide": 2, "clean": true},
        {"source_slide": 19, "papel": "agradecimentos"}
    ]}

Slides são referenciados pelo índice 1-based do arquivo-base. Reutilizar um
índice duplica a página sem achatar seus objetos editáveis.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lmest_ooxml import Package  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = SKILL_DIR / "assets" / "references" / "referencia_base.pptx"
MANDATORY_FIRST = 1
MANDATORY_LAST = 19


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plano", help="JSON com source_slide para cada página final")
    ap.add_argument("saida")
    ap.add_argument("--referencia", default=str(DEFAULT_REFERENCE))
    args = ap.parse_args()

    plan_path = Path(args.plano)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    entries = plan["slides"] if isinstance(plan, dict) else plan
    if len(entries) < 2:
        ap.error("O deck precisa conter pelo menos capa e agradecimentos.")
    indices = [e.get("source_slide") for e in entries]
    if any(not isinstance(i, int) or isinstance(i, bool) or i < 1 or i > MANDATORY_LAST for i in indices):
        ap.error("Cada entrada precisa de source_slide inteiro entre 1 e 19.")
    if indices[0] != MANDATORY_FIRST:
        ap.error("A capa (source_slide 1) precisa ser o primeiro slide.")
    if indices[-1] != MANDATORY_LAST:
        ap.error("Agradecimentos (source_slide 19) precisa ser o último slide.")
    if indices.count(MANDATORY_FIRST) != 1 or indices.count(MANDATORY_LAST) != 1:
        ap.error("Capa e agradecimentos devem aparecer uma única vez.")
    for field, label in (("md_slide", "Markdown"), ("input_slide", "PPTX de origem")):
        source_indices = [e.get(field) for e in entries if field in e]
        if any(not isinstance(i, int) or isinstance(i, bool) or i < 1 for i in source_indices):
            ap.error(f"{field} precisa conter índices inteiros positivos.")
        if source_indices != sorted(source_indices):
            ap.error(f"Os slides de {label} precisam permanecer em ordem não decrescente no plano.")

    reference = Path(args.referencia).resolve()
    out = Path(args.saida).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Package.from_pptx(reference, Path(tmp) / "unpacked")
        original_order = pkg.slide_order()
        if len(original_order) < MANDATORY_LAST:
            ap.error(f"A referência tem {len(original_order)} slides; são necessários 19.")
        used: set[str] = set()
        order: list[str] = []
        for entry, source_index in zip(entries, indices):
            rid, part = original_order[source_index - 1]
            if rid in used:
                rid, _ = pkg.duplicate_slide(part)
            used.add(rid)
            order.append(rid)
        pkg.set_order(order)
        pkg.remove_unlisted_slides()
        pkg.remove_orphan_media()
        out.parent.mkdir(parents=True, exist_ok=True)
        pkg.to_pptx(out)

    clean_positions = [i for i, entry in enumerate(entries) if entry.get("clean")]
    if clean_positions:
        from pptx import Presentation
        from lmest_pptx import clear_body

        prs = Presentation(str(out))
        for position in clean_positions:
            clear_body(prs.slides[position])
        prs.save(str(out))

    deck_plan = [{"slide": i, **entry} for i, entry in enumerate(entries, start=1)]
    plan_out = out.with_name("deck_plan.json")
    plan_out.write_text(json.dumps({"deck": str(out), "reference": str(reference), "slides": deck_plan},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Deck montado: {out} ({len(entries)} slides). Plano: {plan_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Exemplo completo de geração: serve de modelo para o script de cada deck.

    SKILL=<pasta da skill>
    python3 $SKILL/scripts/prepare_input_bundle.py $SKILL/examples/input_bundle work
    python3 $SKILL/scripts/render_equations.py work/extracted/apresentacao.md work/equacoes
    python3 $SKILL/examples/gerar_exemplo.py work
    python3 $SKILL/scripts/render_deck.py work/deck.pptx work/render
    python3 $SKILL/scripts/evaluate_render.py work/render --plano work/deck_plan.json

Estrutura de qualquer script de geração:
1. ler input_manifest.json e equations_manifest.json;
2. escolher slides de referência por índice e rodar assemble_deck.py;
3. preencher slide a slide com lmest_pptx;
4. renumber + audit + salvar.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import lmest_pptx as L  # noqa: E402

work = Path(sys.argv[1] if len(sys.argv) > 1 else "work").resolve()
inp = json.loads((work / "input_manifest.json").read_text(encoding="utf-8"))
eqs = json.loads((work / "equacoes" / "equations_manifest.json").read_text(encoding="utf-8"))["equations"]
src = Path(inp["extracted_dir"])

# 1. plano: capa + slides do Markdown + agradecimentos -------------------------
plano = {"slides": [
    {"source_slide": 1, "papel": "capa"},
    {"source_slide": 5, "md_slide": 1, "papel": "transicao"},
    {"source_slide": 2, "md_slide": 2, "clean": True},
    {"source_slide": 11, "md_slide": 3, "clean": True},
    {"source_slide": 19, "papel": "agradecimentos"},
]}
(work / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")
subprocess.run([sys.executable, str(SKILL / "scripts" / "assemble_deck.py"),
                str(work / "plano.json"), str(work / "deck.pptx")], check=True)

prs = L.open_deck(work / "deck.pptx")
capa, divisor, s_eq, s_fig, agr = prs.slides

# 2. slides rígidos -----------------------------------------------------------
L.fill_cover(capa, inp["capa"])
L.fill_divider(divisor, 1, "Fundamentos", "Modelo do atuador e da malha de controle")
L.fill_thanks(agr, inp["capa"]["agradecimentos"])

# 3. slide de composição limpa com equações -----------------------------------
# O campo `description` do input_manifest orienta a composição; não o copie como texto.
X, W = L.MARGEM_X, L.LARGURA_UTIL
L.set_title(s_eq, "Modelo linearizado do atuador")
it = {"italic": True}
sub = {"baseline": "sub"}
L.add_text(s_eq, X, L.TOPO_CONTEUDO, W, 600000, [[
    "A força magnética é linearizada em torno do ponto de operação, com rigidez de posição ",
    ("k", it), ("s", sub), " e ganho de corrente ", ("k", it), ("i", sub), ".",
]], size=16, name="texto:intro")

display = [e for e in eqs if e["slide"] == 2 and e["kind"] == "display"]
EMU_IN = 914400
alturas = [int(e["altura_in"] * EMU_IN) for e in display]
ponte_h, gap, pad = 300000, 280000, 420000
bloco = alturas[0] + gap + ponte_h + gap + alturas[1]
card_y = 1950000
card_h = bloco + 2 * pad
L.add_card(s_eq, X, card_y, W, card_h, fill=L.COR["superficie"], border=None, radius_px=10,
           name="card:equacoes")
centro = X + W // 2
y = card_y + pad
L.add_equation(s_eq, display[0], work / "equacoes", centro, y, max_w=W - 600000)
y += alturas[0] + gap
L.add_text(s_eq, X, y, W, ponte_h, "O rotor segue a equação de movimento clássica:", size=15,
           color=L.COR["texto_suave"], align="ctr", anchor="ctr", name="texto:ponte")
y += ponte_h + gap
L.add_equation(s_eq, display[1], work / "equacoes", centro, y, max_w=W - 600000)
notas = next(s["notas"] for s in inp["slides"] if s["index"] == 2)
L.set_notes(s_eq, notas)

# 4. slide texto + figura -----------------------------------------------------
L.set_title(s_fig, "Resposta em frequência")
col = int(W * 0.38)
L.add_text(s_fig, X, L.TOPO_CONTEUDO, col, 900000,
           "Com sensor e atuador em planos diferentes, surge um modo com fase invertida perto de 70 Hz.",
           size=16, name="texto:intro")
L.add_text(s_fig, X, 2250000, col, 2000000, [
    [("Colocado: ", {"bold": True}), "modo bem amortecido em 60 Hz"],
    [("Não colocado: ", {"bold": True, "color": L.COR["vermelho"]}), "pico estreito e margem de fase reduzida"],
    [("Orçamento: ", {"bold": True}), "R$ 15 mil para o novo sensor"],
], size=15, bullets=True, space_after_pt=10, name="texto:bullets")
fx = X + col + 400000
fw = W - col - 400000
fh = int(fw * 4.5 / 8)
figura = next(s for s in inp["slides"] if s["index"] == 3)["imagens"][0]["path"]  # caminho já resolvido
L.add_picture(s_fig, src / figura, fx, L.TOPO_CONTEUDO, fw, fh,
              mode="contain", radius_px=0, name="fig:resposta", descr="Resposta em frequência")
L.add_text(s_fig, fx, L.TOPO_CONTEUDO + fh + 80000, fw, 250000,
           "Magnitude da FRF para as configurações colocada e não colocada", size=11,
           color=L.COR["texto_suave"], name="legenda:resposta")

# 5. fechamento ---------------------------------------------------------------
L.renumber(prs)
problemas = L.audit(prs) + L.leftovers(prs)
prs.save(work / "deck.pptx")
print("audit:", problemas or "sem problemas")

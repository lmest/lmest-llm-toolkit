#!/usr/bin/env python3
"""Funções para preencher o deck montado por ``assemble_deck.py``.

Importe em um script de geração:

    import sys; sys.path.insert(0, "<skill>/scripts")
    import lmest_pptx as L

    prs = L.open_deck("work/deck.pptx")
    L.fill_cover(prs.slides[0], manifest["capa"])
    L.set_title(prs.slides[2], "Mancais magnéticos ativos")
    ...
    L.renumber(prs)
    prs.save("work/deck.pptx")
    print(L.audit(prs))

Princípios:
- O texto é trocado run a run, clonando a formatação do template (nunca
  ``text_frame.text = ...``, que apaga a formatação).
- Capa, divisor e agradecimentos têm as regras rígidas codificadas aqui:
  quando o texto não cabe, levanta ``LayoutError`` em vez de mexer no design.
- Medidas de texto usam a métrica do Calibri (via Carlito, que tem as mesmas
  larguras). Sem Carlito, cai para uma estimativa conservadora.
"""

from __future__ import annotations

import io
import shutil
import subprocess
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

from lxml import etree
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

# ------------------------------------------------------------------ tokens
# Valores extraídos de assets/references/referencia_base.pptx (fonte visual).
COR = {
    "navy": "152536",          # fundo do cabeçalho, blocos de destaque
    "texto": "1B2B3A",         # texto principal sobre fundo claro
    "texto_suave": "5B6B7C",   # legendas, descrições
    "azul": "1E88C7",          # destaques, números de slide, valores de tabela
    "azul_medio": "2F6690",    # ícones, títulos de bloco secundários
    "ciano_kicker": "49A9E1",  # kicker/rótulos sobre fundo escuro
    "vermelho": "C41E2A",      # linha do cabeçalho, estado crítico/ativo
    "laranja": "E08A1E",       # ressalvas pontuais (ex.: "a partir de 2027")
    "borda": "D6DEE6",
    "superficie": "F3F5F8",    # cards claros
    "superficie_azul": "EAF4FB",
    "branco": "FFFFFF",
    "texto_sobre_escuro_suave": "B4D0DC",
}
FONTE = "Calibri"
SLIDE_W, SLIDE_H = 12192000, 6858000
PX = 6350                     # 1 px no canvas lógico 1920 × 1080
MARGEM_X = 566928             # margem lateral (≈ 89 px)
TOPO_CONTEUDO = 1143000       # primeira linha útil abaixo do cabeçalho (1,25 in)
BASE_CONTEUDO = 6400800       # limite inferior do conteúdo (acima do número)
LARGURA_UTIL = SLIDE_W - 2 * MARGEM_X


class LayoutError(Exception):
    """O conteúdo não cabe sem violar o template. Informe o usuário."""


# ------------------------------------------------------------------ básicos
def open_deck(path) -> Presentation:
    return Presentation(str(path))


def shape(slide, name: str):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    raise KeyError(f"Forma '{name}' não encontrada no slide '{slide.name}'.")


def has_shape(slide, name: str) -> bool:
    return any(sh.name == name for sh in slide.shapes)


def delete(sh) -> None:
    sh._element.getparent().remove(sh._element)


def clear_body(slide, keep_prefixes=None) -> None:
    """Limpa o corpo e preserva a faixa superior e o rodapé do slide-base.

    Passe ``keep_prefixes`` apenas para compatibilidade com uma composição
    nomeada explicitamente; por padrão os elementos fixos são reconhecidos
    pela posição no canvas de 16:9.
    """
    for sh in list(slide.shapes):
        if keep_prefixes is not None:
            keep = sh.name.startswith(tuple(keep_prefixes))
        else:
            if sh.top < 960000:
                keep = True
            elif sh.top >= 6300000:
                keep = True
                if sh.has_text_frame:
                    text = sh.text_frame.text.strip()
                    if text and text != "@lmest.ufu" and not text.isdigit():
                        set_text(sh, "")
            else:
                keep = False
        if not keep:
            delete(sh)


_NOTES_BODY = (
    '<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
    '<p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
    '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
    '<p:spPr><a:xfrm><a:off x="685800" y="4400550"/><a:ext cx="5486400" cy="3600450"/></a:xfrm></p:spPr>'
    '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>'
)


def set_notes(slide, text: str) -> None:
    """Notas do apresentador (o notes master do template não tem placeholder de corpo)."""
    ns = slide.notes_slide
    if ns.notes_text_frame is None:
        ns.shapes._spTree.append(etree.fromstring(_NOTES_BODY))
    ns.notes_text_frame.text = text


def roman(n: int) -> str:
    vals = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


# --------------------------------------------------------------- medição
_FONT_DIRS = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts",
              Path("/Library/Fonts"), Path("C:/Windows/Fonts")]


@lru_cache(maxsize=4)
def _font_file(bold: bool) -> str | None:
    wanted = (["Carlito-Bold.ttf", "calibrib.ttf"] if bold else ["Carlito-Regular.ttf", "calibri.ttf"])
    for d in _FONT_DIRS:
        if d.exists():
            for name in wanted:
                hits = list(d.rglob(name))
                if hits:
                    return str(hits[0])
    return None


@lru_cache(maxsize=4)
def _pil_font(bold: bool):
    f = _font_file(bold)
    return ImageFont.truetype(f, 200) if f else None


def metric_font_available() -> bool:
    return _font_file(False) is not None


def text_width_pt(text: str, pt: float, bold: bool = False) -> float:
    font = _pil_font(bold)
    if font is None:  # estimativa conservadora (Calibri ≈ 0,50 em; negrito ≈ 0,53 em)
        return len(text) * pt * (0.53 if bold else 0.50)
    return font.getlength(text) * pt / 200.0


def count_lines(text: str, pt: float, width_emu: int, bold: bool = False) -> int:
    width_pt = width_emu / 12700
    total = 0
    for para in text.split("\n"):
        words = para.split(" ")
        lines, current = 1, ""
        for w in words:
            trial = (current + " " + w) if current else w
            if text_width_pt(trial, pt, bold) <= width_pt or not current:
                current = trial
            else:
                lines += 1
                current = w
        total += lines
    return total


def inner_width(sh) -> int:
    body = sh.text_frame._txBody.find(qn("a:bodyPr"))
    l_ins = int(body.get("lIns", 91440)) if body is not None else 91440
    r_ins = int(body.get("rIns", 91440)) if body is not None else 91440
    return int(sh.width) - l_ins - r_ins


def check_fit(sh, text: str, pt: float, bold: bool, max_lines: int, what: str) -> int:
    n = count_lines(text, pt, inner_width(sh), bold)
    if n > max_lines:
        raise LayoutError(f"{what} ocupa {n} linha(s) e o template comporta {max_lines}: \"{text}\". "
                          "Encurte o texto ou peça uma quebra de linha explícita ao usuário.")
    return n


# ------------------------------------------------------------- texto
def _make_run_from_end(p):
    end = p.find(qn("a:endParaRPr"))
    r = etree.SubElement(p, qn("a:r"))
    rpr = deepcopy(end) if end is not None else etree.Element(qn("a:rPr"))
    rpr.tag = qn("a:rPr")
    r.append(rpr)
    etree.SubElement(r, qn("a:t"))
    p.remove(r)
    return r


def _apply_overrides(r, over: dict) -> None:
    rpr = r.find(qn("a:rPr"))
    if rpr is None:
        rpr = etree.Element(qn("a:rPr"))
        r.insert(0, rpr)
    if "bold" in over:
        rpr.set("b", "1" if over["bold"] else "0")
    if "italic" in over:
        rpr.set("i", "1" if over["italic"] else "0")
    if "size" in over:
        rpr.set("sz", str(int(round(over["size"] * 100))))
    if "baseline" in over:  # "sub" | "sup" | None
        rpr.set("baseline", {"sub": "-25000", "sup": "30000"}.get(over["baseline"], "0"))
    if "color" in over:
        for f in rpr.findall(qn("a:solidFill")):
            rpr.remove(f)
        fill = etree.Element(qn("a:solidFill"))
        etree.SubElement(fill, qn("a:srgbClr")).set("val", over["color"])
        # solidFill deve vir antes de latin/ea/cs
        anchor = next((c for c in rpr if etree.QName(c).localname in ("latin", "ea", "cs", "sym", "hlinkClick")), None)
        if anchor is not None:
            anchor.addprevious(fill)
        else:
            rpr.append(fill)
    for attr in ("err", "dirty"):
        rpr.attrib.pop(attr, None)


def set_paragraphs(sh, paragraphs) -> None:
    """Substitui o texto preservando a formatação do template.

    ``paragraphs``: lista em que cada item é uma string (um run) ou uma lista de
    runs; cada run é ``"texto"`` ou ``("texto", {"bold": True, "color": "C41E2A", "size": 14})``.
    O parágrafo i herda o estilo do parágrafo i do template (ou do último);
    o run j herda o estilo do run j desse parágrafo (ou do último).
    """
    body = sh.text_frame._txBody
    templates = body.findall(qn("a:p"))
    for p in templates:
        body.remove(p)
    if not paragraphs:
        paragraphs = [""]
    for i, item in enumerate(paragraphs):
        tp = templates[min(i, len(templates) - 1)]
        newp = deepcopy(tp)
        truns = [deepcopy(r) for r in newp.findall(qn("a:r"))] or [_make_run_from_end(newp)]
        for child in list(newp):
            if etree.QName(child).localname in ("r", "br", "fld"):
                newp.remove(child)
        end = newp.find(qn("a:endParaRPr"))
        runs = [item] if isinstance(item, (str, tuple)) else list(item)
        for j, run in enumerate(runs):
            text, over = (run, {}) if isinstance(run, str) else run
            r = deepcopy(truns[min(j, len(truns) - 1)])
            r.find(qn("a:t")).text = text
            _apply_overrides(r, over)
            if end is not None:
                end.addprevious(r)
            else:
                newp.append(r)
        body.append(newp)


def set_text(sh, text: str) -> None:
    set_paragraphs(sh, text.split("\n"))


def first_run_size(sh, default: float = 18.0) -> float:
    for r in sh.text_frame._txBody.iter(qn("a:rPr")):
        if r.get("sz"):
            return int(r.get("sz")) / 100
    return default


# ------------------------------------------------------- slides fixos
def set_title(slide, text: str) -> None:
    """Atualiza o título existente do cabeçalho de um slide de conteúdo."""
    sh = getattr(slide.shapes, "title", None)
    if sh is None or not sh.has_text_frame:
        candidates = [s for s in slide.shapes if s.has_text_frame and s.top < 800000
                      and s.width >= 3_000_000 and s.text_frame.text.strip()]
        if not candidates:
            raise KeyError("Não foi possível identificar o título de conteúdo na referência selecionada.")
        sh = max(candidates, key=lambda s: (s.width, -s.top))
    check_fit(sh, text, first_run_size(sh, 28), True, 1, "Título do slide")
    set_text(sh, text)


def renumber(prs, start_at: int = 1) -> None:
    """Atualiza números em objetos pequenos no canto inferior direito."""
    for idx, slide in enumerate(prs.slides, start=start_at):
        for sh in slide.shapes:
            if (sh.has_text_frame and sh.left > 10_000_000 and sh.top > 6_200_000
                    and sh.width < 800_000 and sh.text_frame.text.strip().isdigit()):
                set_text(sh, str(idx))


def fill_cover(slide, capa: dict) -> None:
    """Preenche a capa. Só título, autor(es)/cargo e contatos mudam.

    ``capa`` = bloco "capa" do input_manifest.json:
    {"titulo": str, "autores": [{"nome", "cargo", "contatos": [...], "apresentador"}]}
    """
    titulo = capa["titulo"]
    t = shape(slide, "Text 1")
    check_fit(t, titulo, 44, True, 2, "Título da capa")
    set_paragraphs(t, [titulo.replace("\n", " ")] if "\n" not in titulo else titulo.split("\n")[:2])

    autores = capa["autores"]
    a = shape(slide, "Text 3")
    if len(autores) == 1:
        nome, cargo = autores[0]["nome"], autores[0].get("cargo")
        runs = [nome] + ([f"  ·  {cargo}"] if cargo else [])
        linha = nome + (f"  ·  {cargo}" if cargo else "")
        largura = text_width_pt(nome, 17, True) + (text_width_pt(f"  ·  {cargo}", 13) if cargo else 0)
    else:  # vários autores: nomes na mesma linha, sem cargos
        linha = "  ·  ".join(x["nome"] for x in autores)
        runs = [linha]
        largura = text_width_pt(linha, 17, True)
    if largura > inner_width(a) / 12700:
        raise LayoutError(f"Bloco de autoria não cabe em uma linha: \"{linha}\". "
                          "Abrevie nomes (ex.: iniciais do meio) ou confirme com o usuário.")
    set_paragraphs(a, [runs])

    apresentador = next((x for x in autores if x.get("apresentador")), autores[0])
    contatos = "   ·   ".join(apresentador.get("contatos", []))
    c = shape(slide, "Text 4")
    if contatos:
        check_fit(c, contatos, 12, False, 1, "Linha de contatos da capa")
    set_text(c, contatos)


def fill_divider(slide, parte: int | str, titulo: str, subtitulo: str | None) -> None:
    rotulo = f"PARTE {roman(parte)}" if isinstance(parte, int) else str(parte).upper()
    set_text(shape(slide, "Text 8"), rotulo)
    t = shape(slide, "Text 9")
    check_fit(t, titulo, 40, True, 1, "Título do divisor")
    set_text(t, titulo)
    s = shape(slide, "Text 10")
    if subtitulo:
        check_fit(s, subtitulo, 16, False, 1, "Subtítulo do divisor")
    set_text(s, subtitulo or "")


def fill_thanks(slide, agr: dict) -> None:
    """Agradecimentos: nome, cargo e até 3 linhas de contato (telefone/e-mail).

    Ícones: telefone usa o ícone da linha 1 do template (WhatsApp); e-mail usa o
    da linha 2. Linhas não usadas são removidas sem mover as demais. O painel de
    logos, o 'Obrigado' e o @lmest.ufu são fixos.
    """
    nome = shape(slide, "Text 7")
    check_fit(nome, agr["nome"], 19, True, 1, "Nome nos agradecimentos")
    set_text(nome, agr["nome"])
    cargo = shape(slide, "Text 187")
    if agr.get("cargo"):
        check_fit(cargo, agr["cargo"], 14, False, 1, "Cargo nos agradecimentos")
        set_text(cargo, agr["cargo"])
    else:
        set_text(cargo, "")

    contatos = [c for c in agr.get("contatos", []) if c]
    # mesma ordem da referência: telefone(s) primeiro, depois e-mail(s)
    contatos = [c for c in contatos if "@" not in c] + [c for c in contatos if "@" in c]
    if len(contatos) > 3:
        raise LayoutError("Agradecimentos comportam no máximo 3 contatos (telefone/e-mail).")
    icon_shapes = [shape(slide, name) for name in ("Image 3", "Image 4", "Image 5")]
    text_shapes = [shape(slide, name) for name in ("Text 208", "Text 227", "Text 243")]
    phone_blob, mail_blob = icon_shapes[0].image.blob, icon_shapes[1].image.blob
    for i, (ic, tx) in enumerate(zip(icon_shapes, text_shapes)):
        valor = contatos[i] if i < len(contatos) else ""
        if valor:
            check_fit(tx, valor, 14.5, False, 1, f"Contato {i + 1} nos agradecimentos")
            desired_blob = mail_blob if "@" in valor else phone_blob
            if ic.image.blob != desired_blob:
                _swap_blob(ic, desired_blob)
        else:
            delete(ic)
        set_text(tx, valor)


# --------------------------------------------------------------- imagens
RASTER_OK = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}


def ensure_raster(path, workdir=None) -> Path:
    """Converte SVG/WEBP/GIF para PNG (o python-pptx não insere esses formatos)."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg", ".png", ".bmp"):
        return path
    out_dir = Path(workdir) if workdir else path.parent
    out = out_dir / (path.stem + ".png")
    if suffix == ".svg":
        if shutil.which("rsvg-convert"):
            subprocess.run(["rsvg-convert", "-d", "300", "-p", "300", "-o", str(out), str(path)], check=True)
        else:
            try:
                import cairosvg  # type: ignore
                cairosvg.svg2png(url=str(path), write_to=str(out), dpi=300)
            except ImportError as exc:
                raise RuntimeError("Para SVG instale rsvg-convert (librsvg2-bin) ou cairosvg.") from exc
    else:
        Image.open(path).save(out)
    return out


def _swap_blob(pic, blob: bytes) -> None:
    _, rid = pic.part.get_or_add_image_part(io.BytesIO(blob))
    pic._element.find(".//" + qn("a:blip")).set(qn("r:embed"), rid)


def _crop_cover(pic, img_w: int, img_h: int) -> None:
    frame = pic.width / pic.height
    img = img_w / img_h
    pic.crop_left = pic.crop_right = pic.crop_top = pic.crop_bottom = 0
    if img > frame:
        excess = (1 - frame / img) / 2
        pic.crop_left = pic.crop_right = excess
    elif img < frame:
        excess = (1 - img / frame) / 2
        pic.crop_top = pic.crop_bottom = excess


def _round(pic, radius_px: float) -> None:
    if radius_px <= 0:
        return
    pic.auto_shape_type = MSO_SHAPE.ROUNDED_RECTANGLE
    geom = pic._element.spPr.find(qn("a:prstGeom"))
    av = geom.find(qn("a:avLst"))
    if av is None:
        av = etree.SubElement(geom, qn("a:avLst"))
    for gd in list(av):
        av.remove(gd)
    adj = int(min(50000, radius_px * PX / min(pic.width, pic.height) * 100000))
    gd = etree.SubElement(av, qn("a:gd"))
    gd.set("name", "adj")
    gd.set("fmla", f"val {adj}")


def replace_image(pic, path, mode: str = "cover") -> None:
    """Troca a imagem de uma foto do template mantendo moldura, raio e posição."""
    path = ensure_raster(path)
    _, rid = pic.part.get_or_add_image_part(str(path))
    pic._element.find(".//" + qn("a:blip")).set(qn("r:embed"), rid)
    w, h = Image.open(path).size
    if mode == "cover":
        _crop_cover(pic, w, h)
    else:
        pic.crop_left = pic.crop_right = pic.crop_top = pic.crop_bottom = 0
        x, y, bw, bh = pic.left, pic.top, pic.width, pic.height
        scale = min(bw / w, bh / h)
        pic.width, pic.height = int(w * scale), int(h * scale)
        pic.left, pic.top = int(x + (bw - pic.width) / 2), int(y + (bh - pic.height) / 2)


def add_picture(slide, path, x, y, w, h, mode: str = "cover", radius_px: float = 8,
                name: str | None = None, descr: str | None = None):
    """Insere foto na caixa (x, y, w, h) em EMU. ``cover`` recorta; ``contain`` encaixa."""
    path = ensure_raster(path)
    iw, ih = Image.open(path).size
    if mode == "contain":
        s = min(w / iw, h / ih)
        pw, ph = int(iw * s), int(ih * s)
        pic = slide.shapes.add_picture(str(path), int(x + (w - pw) / 2), int(y + (h - ph) / 2), pw, ph)
    else:
        pic = slide.shapes.add_picture(str(path), int(x), int(y), int(w), int(h))
        _crop_cover(pic, iw, ih)
    _round(pic, radius_px)
    if name:
        pic.name = name
    if descr:
        pic._element.find(".//" + qn("p:cNvPr")).set("descr", descr)
    return pic


def add_equation(slide, entry: dict, eq_dir, x, y, align: str = "center", max_w: int | None = None):
    """Insere a PNG da equação no tamanho nativo (mesmo corpo de letra no deck todo).

    ``x`` é a borda esquerda (align='left') ou o centro (align='center').
    Se ``max_w`` for dado e a equação não couber, levanta LayoutError: divida a
    equação, mude o layout ou renderize com --pt-display menor para o deck inteiro.
    """
    if not entry.get("image"):
        raise LayoutError(f"Equação {entry.get('index')} não foi renderizada: {entry.get('erro')}")
    w = int(entry["largura_in"] * 914400)
    h = int(entry["altura_in"] * 914400)
    if max_w and w > max_w:
        raise LayoutError(f"Equação {entry['index']} tem {w / 914400:.2f} in e o espaço disponível é "
                          f"{max_w / 914400:.2f} in.")
    left = int(x - w / 2) if align == "center" else int(x)
    pic = slide.shapes.add_picture(str(Path(eq_dir) / entry["image"]), left, int(y), w, h)
    pic.name = f"eq:{entry['index']:03d}"
    pic._element.find(".//" + qn("p:cNvPr")).set("descr", entry["latex"])
    return pic


# --------------------------------------------------------- formas e texto
def _set_font(run_rpr, size, color, bold, italic=False):
    run_rpr.set("lang", "pt-BR")
    run_rpr.set("sz", str(int(round(size * 100))))
    run_rpr.set("b", "1" if bold else "0")
    if italic:
        run_rpr.set("i", "1")
    fill = etree.SubElement(run_rpr, qn("a:solidFill"))
    etree.SubElement(fill, qn("a:srgbClr")).set("val", color)
    for tag in ("a:latin", "a:ea", "a:cs"):
        etree.SubElement(run_rpr, qn(tag)).set("typeface", FONTE)


def add_text(slide, x, y, w, h, paragraphs, size: float = 15, color: str = COR["texto"],
             bold: bool = False, align: str = "l", anchor: str = "t", name: str | None = None,
             line_spacing: float = 1.0, space_after_pt: float = 0, bullets: bool = False):
    """Caixa de texto sem margens internas, Calibri, sem autoajuste.

    ``paragraphs``: como em set_paragraphs (str ou lista de runs com overrides).
    Overrides aceitos: size, color, bold, italic, baseline ("sub"/"sup").
    Variáveis no meio do texto (k_s) vão como runs: ("k", {"italic": True}),
    ("s", {"baseline": "sub"}) — não como imagem.
    """
    tb = slide.shapes.add_textbox(int(x), int(y), int(w), int(h))
    if name:
        tb.name = name
    body = tb.text_frame._txBody
    bp = body.find(qn("a:bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(k, "0")
    bp.set("wrap", "square")
    bp.set("anchor", anchor)
    for c in list(bp):
        bp.remove(c)
    for p in body.findall(qn("a:p")):
        body.remove(p)
    paragraphs = [paragraphs] if isinstance(paragraphs, str) else paragraphs
    for item in paragraphs:
        p = etree.SubElement(body, qn("a:p"))
        ppr = etree.SubElement(p, qn("a:pPr"))
        ppr.set("algn", align)
        if bullets:
            ppr.set("marL", "228600")
            ppr.set("indent", "-228600")
        else:
            ppr.set("marL", "0")
            ppr.set("indent", "0")
        ln = etree.SubElement(etree.SubElement(ppr, qn("a:lnSpc")), qn("a:spcPct"))
        ln.set("val", str(int(line_spacing * 100000)))
        if space_after_pt:
            etree.SubElement(etree.SubElement(ppr, qn("a:spcAft")), qn("a:spcPts")).set("val", str(int(space_after_pt * 100)))
        if bullets:
            bf = etree.SubElement(ppr, qn("a:buClr"))
            etree.SubElement(bf, qn("a:srgbClr")).set("val", COR["azul"])
            etree.SubElement(ppr, qn("a:buFont")).set("typeface", "Arial")
            etree.SubElement(ppr, qn("a:buChar")).set("char", "•")
        else:
            etree.SubElement(ppr, qn("a:buNone"))
        runs = [item] if isinstance(item, (str, tuple)) else list(item)
        for run in runs:
            text, over = (run, {}) if isinstance(run, str) else run
            r = etree.SubElement(p, qn("a:r"))
            rpr = etree.SubElement(r, qn("a:rPr"))
            _set_font(rpr, over.get("size", size), over.get("color", color), over.get("bold", bold), over.get("italic", False))
            if over.get("baseline"):
                rpr.set("baseline", {"sub": "-25000", "sup": "30000"}[over["baseline"]])
            etree.SubElement(r, qn("a:t")).text = text
    return tb


def add_card(slide, x, y, w, h, fill: str = COR["superficie"], border: str | None = COR["borda"],
             radius_px: float = 10, name: str | None = None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, int(x), int(y), int(w), int(h))
    sh.adjustments[0] = min(0.5, radius_px * PX / min(int(w), int(h)))
    sh.fill.solid()
    sh.fill.fore_color.rgb = RGBColor.from_string(fill)
    if border:
        sh.line.color.rgb = RGBColor.from_string(border)
        sh.line.width = Emu(12700)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    if sh.has_text_frame:
        sh.text_frame.text = ""
    if name:
        sh.name = name
    return sh


def add_table(slide, x, y, w, h, headers, rows, column_widths=None,
              numeric_columns=(), font_size: float = 12, name: str | None = None):
    """Insere uma tabela nativa editável.

    ``column_widths`` aceita larguras absolutas em EMU cuja soma seja ``w``.
    ``numeric_columns`` contém índices de coluna baseados em zero.
    """
    headers = list(headers)
    rows = [list(row) for row in rows]
    if not headers:
        raise ValueError("A tabela precisa de pelo menos uma coluna.")
    if any(len(row) != len(headers) for row in rows):
        raise ValueError("Todas as linhas da tabela precisam ter o mesmo número de colunas do cabeçalho.")
    frame = slide.shapes.add_table(len(rows) + 1, len(headers), int(x), int(y), int(w), int(h))
    if name:
        frame.name = name
    table = frame.table
    if column_widths is not None:
        widths = [int(value) for value in column_widths]
        if len(widths) != len(headers) or sum(widths) != int(w):
            raise ValueError("column_widths precisa ter uma largura por coluna e somar a w informada.")
        for col, width in zip(table.columns, widths):
            col.width = width
    numeric_columns = set(numeric_columns)
    for r, values in enumerate([headers] + rows):
        for c, value in enumerate(values):
            cell = table.cell(r, c)
            cell.text = str(value)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = cell.margin_right = 68580
            cell.margin_top = cell.margin_bottom = 22860
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = RGBColor.from_string(COR["navy"])
            else:
                cell.fill.fore_color.rgb = RGBColor.from_string(
                    COR["superficie"] if r % 2 == 0 else COR["branco"])
            for paragraph in cell.text_frame.paragraphs:
                paragraph.alignment = PP_ALIGN.RIGHT if c in numeric_columns else PP_ALIGN.LEFT
                for run in paragraph.runs:
                    run.font.name = FONTE
                    run.font.size = Pt(font_size if r else max(font_size, 11))
                    run.font.bold = (r == 0) or (c in numeric_columns and r > 0)
                    run.font.color.rgb = RGBColor.from_string(
                        COR["branco"] if r == 0 else COR["azul"] if c in numeric_columns else COR["texto"])
    return frame


def add_chart(slide, x, y, w, h, chart_type: str, series, categories=None,
              show_legend: bool | None = None, name: str | None = None):
    """Insere um gráfico nativo editável: bar, column, line ou scatter.

    Para bar/column/line, ``series`` é uma lista de ``{"name": ..., "values": [...]}``
    e ``categories`` contém um rótulo por valor. Para scatter, cada série contém
    ``x`` e ``values`` (ou ``y``) com pares numéricos.
    """
    kinds = {
        "bar": XL_CHART_TYPE.BAR_CLUSTERED,
        "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "line": XL_CHART_TYPE.LINE_MARKERS,
        "scatter": XL_CHART_TYPE.XY_SCATTER,
    }
    kind = chart_type.lower()
    if kind not in kinds:
        raise ValueError(f"Tipo de gráfico inválido: {chart_type}. Use {', '.join(kinds)}.")
    if not series:
        raise ValueError("O gráfico precisa de pelo menos uma série de dados.")
    if kind == "scatter":
        data = XyChartData()
        for item in series:
            xs = item.get("x", [])
            ys = item.get("values", item.get("y", []))
            if len(xs) != len(ys):
                raise ValueError(f"A série '{item.get('name', '')}' precisa ter vetores x e y do mesmo tamanho.")
            target = data.add_series(item.get("name", "Série"))
            for x_value, y_value in zip(xs, ys):
                target.add_data_point(float(x_value), float(y_value))
    else:
        if categories is None:
            raise ValueError("Gráficos bar, column e line precisam de categories.")
        data = CategoryChartData()
        data.categories = list(categories)
        for item in series:
            if len(item.get("values", [])) != len(categories):
                raise ValueError(f"A série '{item.get('name', '')}' precisa ter um valor por categoria.")
            data.add_series(item.get("name", "Série"), item["values"])
    frame = slide.shapes.add_chart(kinds[kind], int(x), int(y), int(w), int(h), data)
    if name:
        frame.name = name
    chart = frame.chart
    chart.has_title = False
    chart.has_legend = (len(series) > 1) if show_legend is None else bool(show_legend)
    if chart.has_legend:
        chart.legend.font.name = FONTE
        chart.legend.font.size = Pt(10)
    palette = [COR["azul"], COR["navy"], COR["vermelho"], COR["azul_medio"], COR["laranja"]]
    for i, chart_series in enumerate(chart.series):
        color = RGBColor.from_string(palette[i % len(palette)])
        if kind in ("bar", "column"):
            chart_series.format.fill.solid()
            chart_series.format.fill.fore_color.rgb = color
            chart_series.format.line.color.rgb = color
        else:
            chart_series.format.line.color.rgb = color
            chart_series.format.line.width = Pt(2)
            if kind in ("line", "scatter"):
                chart_series.marker.style = XL_MARKER_STYLE.CIRCLE
                chart_series.marker.size = 6
                chart_series.marker.format.fill.solid()
                chart_series.marker.format.fill.fore_color.rgb = color
                chart_series.marker.format.line.color.rgb = color
    for axis_name in ("category_axis", "value_axis"):
        try:
            axis = getattr(chart, axis_name)
            axis.tick_labels.font.name = FONTE
            axis.tick_labels.font.size = Pt(10)
        except (AttributeError, ValueError):
            pass
    try:
        chart.value_axis.has_major_gridlines = True
        chart.value_axis.major_gridlines.format.line.color.rgb = RGBColor.from_string(COR["borda"])
    except (AttributeError, ValueError):
        pass
    return chart


def add_connector(slide, begin, end, kind: str = "straight", color: str = COR["navy"],
                  width_pt: float = 1.5, begin_shape=None, end_shape=None,
                  begin_connection: int = 0, end_connection: int = 0, name: str | None = None):
    """Insere conector reto/ortogonal usando coordenadas ou formas conectadas.

    ``begin`` e ``end`` são pares (x, y) em EMU. Se uma forma for informada,
    a ponta correspondente é conectada ao índice de conexão solicitado.
    """
    kinds = {"straight": MSO_CONNECTOR.STRAIGHT, "elbow": MSO_CONNECTOR.ELBOW,
             "orthogonal": MSO_CONNECTOR.ELBOW}
    connector_kind = kinds.get(kind.lower())
    if connector_kind is None:
        raise ValueError("kind deve ser 'straight' ou 'elbow'/'orthogonal'.")
    connector = slide.shapes.add_connector(connector_kind, int(begin[0]), int(begin[1]),
                                           int(end[0]), int(end[1]))
    connector.line.color.rgb = RGBColor.from_string(color)
    connector.line.width = Pt(width_pt)
    if name:
        connector.name = name
    if begin_shape is not None:
        connector.begin_connect(begin_shape, int(begin_connection))
    if end_shape is not None:
        connector.end_connect(end_shape, int(end_connection))
    return connector


# ------------------------------------------------------------------ QA
def audit(prs) -> list[str]:
    """Verificações objetivas antes de renderizar.

    - texto que provavelmente estoura a caixa (estimativa por métrica Calibri);
    - formas fora da área do slide;
    - números de página divergentes da posição real;
    - texto de exemplo do template que sobrou sem querer (heurística por slide).
    """
    problems = []
    for idx, slide in enumerate(prs.slides, start=1):
        for sh in slide.shapes:
            if sh.left is not None and (sh.left < 0 or sh.top < 0 or sh.left + sh.width > SLIDE_W + 1
                                        or sh.top + sh.height > SLIDE_H + 1):
                problems.append(f"slide {idx}: '{sh.name}' sai da área do slide")
            if (sh.has_text_frame and sh.left > 10_000_000 and sh.top > 6_200_000
                    and sh.width < 800_000 and sh.text_frame.text.strip().isdigit()
                    and sh.text_frame.text.strip() != str(idx)):
                problems.append(f"slide {idx}: número de página '{sh.text_frame.text}' (rode renumber)")
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            bp = sh.text_frame._txBody.find(qn("a:bodyPr"))
            if bp is not None and (bp.find(qn("a:normAutofit")) is not None or bp.find(qn("a:spAutoFit")) is not None):
                continue
            needed = 0.0
            width = inner_width(sh)
            if width <= 0:
                continue
            for p in sh.text_frame.paragraphs:
                text = "".join(r.text for r in p.runs)
                size = next((r.font.size.pt for r in p.runs if r.font.size), 18.0)
                bold = any(r.font.bold for r in p.runs)
                lines = count_lines(text, size, width, bold) if text else 1
                needed += lines * size * 1.2
            avail = (int(sh.height) - int(bp.get("tIns", 45720)) - int(bp.get("bIns", 45720))) / 12700 if bp is not None else int(sh.height) / 12700
            if needed > avail * 1.15 + 2:
                problems.append(f"slide {idx}: '{sh.name}' pode estourar ({needed:.0f} pt de texto para {avail:.0f} pt de caixa)")
    return problems


TEXTO_FIXO_REFERENCIA = {
    "LMEST-UFU  ·  PESQUISA, DESENVOLVIMENTO E INOVAÇÃO",
    "AGRADECIMENTOS", "Obrigado", "@lmest.ufu",
}
OBJETOS_FIXOS = {1: {"Text 0", "Text 2"}, 19: {"Text 5", "Text 6", "Text 261"}}
REFERENCIA_PADRAO = Path(__file__).resolve().parents[1] / "assets" / "references" / "referencia_base.pptx"


def leftovers(prs, reference=REFERENCIA_PADRAO) -> list[str]:
    """Detecta textos de exemplo ainda presentes, preservando a marca institucional."""
    amostras = set()
    for source_index, s in enumerate(Presentation(str(reference)).slides, start=1):
        for sh in s.shapes:
            if sh.has_text_frame and sh.name not in OBJETOS_FIXOS.get(source_index, set()):
                for p in sh.text_frame.paragraphs:
                    t = "".join(r.text for r in p.runs).strip()
                    if len(t) >= 6 and t not in TEXTO_FIXO_REFERENCIA and not t.startswith("PARTE "):
                        amostras.add(t)
    achados = []
    for idx, slide in enumerate(prs.slides, start=1):
        fixed_names = OBJETOS_FIXOS.get(1 if idx == 1 else 19 if idx == len(prs.slides) else -1, set())
        for sh in slide.shapes:
            if sh.has_text_frame and sh.name not in fixed_names:
                for p in sh.text_frame.paragraphs:
                    t = "".join(r.text for r in p.runs).strip()
                    if t and t in amostras and t not in TEXTO_FIXO_REFERENCIA and not t.startswith("PARTE "):
                        achados.append(f"slide {idx}: '{sh.name}' ainda contém texto do template: \"{t[:60]}\"")
    return achados


__all__ = [n for n in dir() if not n.startswith("_")]

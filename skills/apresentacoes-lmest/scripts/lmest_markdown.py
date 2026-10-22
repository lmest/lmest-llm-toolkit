#!/usr/bin/env python3
"""Leitura do Markdown de entrada: front matter, slides, imagens e equações.

Fonte única da lógica de parsing, usada por ``prepare_input_bundle.py`` e
``render_equations.py`` (antes cada script tinha seus próprios regex, com
resultados diferentes).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import unquote

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

MATH_ENVS = r"(?:equation|align|gather|multline|alignat|flalign|eqnarray)\*?"

FENCE_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>[^\n]*)$", re.M)
DOLLAR_DISPLAY_RE = re.compile(r"(?<!\\)\$\$(.+?)(?<!\\)\$\$", re.S)
BRACKET_DISPLAY_RE = re.compile(r"\\\[(.+?)\\\]", re.S)
ENV_RE = re.compile(r"\\begin\{(" + MATH_ENVS + r")\}.*?\\end\{\1\}", re.S)
# Matemática inline no estilo Pandoc, endurecida para textos em português:
# - o $ de abertura não pode vir colado a letra/número (R$ 70, US$ 5) nem a \ ou $;
# - logo após a abertura não pode haver espaço; antes do fechamento também não;
# - o $ de fechamento não pode ser seguido de letra/número ($5 e $10 não é math);
# - não atravessa quebras de linha.
INLINE_RE = re.compile(r"(?<![\\$\w])\$(?![\s$])([^$\n]*?[^\s\\$])\$(?![\w$])")
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1", re.S)
IMAGE_MD_RE = re.compile(r"!\[([^\]]*)\]\(\s*(<[^>]+>|[^)\s]+)(?:\s+[\"'(][^)]*[\"')])?\s*\)")
IMAGE_HTML_RE = re.compile(r"<img\b[^>]*?\bsrc\s*=\s*[\"']([^\"']+)[\"']", re.I)
LITERAL_RE = re.compile(r"<!--\s*literal\s*-->", re.I)
NOTES_RE = re.compile(r"<!--\s*notas\s*:\s*(.*?)-->", re.I | re.S)
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t#]*$", re.M)
SEPARATOR_RE = re.compile(r"^-{3,}[ \t]*$", re.M)
BLOCKQUOTE_LINE_RE = re.compile(r"^[ \t]{0,3}>[ \t]?(?P<content>.*)$")


# --------------------------------------------------------------------- utils
def _blank(text: str, start: int, end: int) -> str:
    """Substitui text[start:end] por espaços, preservando quebras de linha."""
    chunk = re.sub(r"[^\n]", " ", text[start:end])
    return text[:start] + chunk + text[end:]


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


# ------------------------------------------------------------- front matter
def split_front_matter(text: str) -> tuple[dict, str, int, str | None]:
    """Retorna (dados, corpo, linhas_consumidas, erro)."""
    if not text.startswith("---"):
        return {}, text, 0, None
    m = re.match(r"^---[ \t]*\n(.*?)\n(?:---|\.\.\.)[ \t]*(?:\n|$)", text, re.S)
    if not m:
        return {}, text, 0, "Front matter iniciado com '---' mas sem fechamento."
    raw = m.group(1)
    consumed = text[: m.end()].count("\n")
    if yaml is None:
        return {}, text[m.end():], consumed, "PyYAML não está instalado; instale com pip install pyyaml."
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        return {}, text[m.end():], consumed, f"Front matter YAML inválido: {exc}"
    if not isinstance(data, dict):
        return {}, text[m.end():], consumed, "Front matter deve ser um mapeamento YAML."
    return data, text[m.end():], consumed, None


# ------------------------------------------------------------------ código
@dataclass
class Fence:
    start: int
    end: int
    info: str
    body_start: int
    body_end: int


def find_fences(text: str) -> list[Fence]:
    fences: list[Fence] = []
    pos = 0
    while True:
        m = FENCE_RE.search(text, pos)
        if not m:
            break
        marker = m.group("fence")
        close_re = re.compile(r"^[ \t]{0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}[ \t]*$", re.M)
        body_start = m.end() + 1
        c = close_re.search(text, body_start)
        end = c.end() if c else len(text)
        body_end = c.start() if c else len(text)
        fences.append(Fence(m.start(), end, m.group("info").strip().lower(), body_start, max(body_start, body_end)))
        pos = end
    return fences


def mask_code(text: str) -> str:
    """Apaga blocos de código e código inline (mantendo posições e linhas)."""
    for f in reversed(find_fences(text)):
        text = _blank(text, f.start, f.end)
    for m in reversed(list(INLINE_CODE_RE.finditer(text))):
        text = _blank(text, m.start(), m.end())
    return text


def mask_comments(text: str) -> str:
    for m in reversed(list(re.finditer(r"<!--.*?-->", text, re.S))):
        text = _blank(text, m.start(), m.end())
    return text


@dataclass
class Blockquote:
    start: int
    end: int
    text: str
    line: int


class MarkdownBlockquoteError(ValueError):
    """Blockquote inválido ou fora da posição reservada para descrição."""

    def __init__(self, line: int, reason: str):
        self.line = line
        super().__init__(f"Blockquote inválido na linha {line}: {reason}")


def find_blockquotes(text: str) -> list[Blockquote]:
    """Localiza blocos Markdown ``>`` fora de código e comentários HTML."""
    visible = mask_comments(mask_code(text))
    blocks: list[Blockquote] = []
    offset = 0
    active_start: int | None = None
    active_end = 0
    active_lines: list[str] = []

    def finish() -> None:
        nonlocal active_start, active_end, active_lines
        if active_start is not None:
            blocks.append(Blockquote(active_start, active_end, "\n".join(active_lines).strip(),
                                     line_of(text, active_start)))
        active_start = None
        active_end = 0
        active_lines = []

    for line in visible.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        match = BLOCKQUOTE_LINE_RE.match(content)
        if match:
            if active_start is None:
                active_start = offset
            active_end = offset + len(line)
            active_lines.append(match.group("content"))
        else:
            finish()
        offset += len(line)
    finish()
    return blocks


def mask_blockquotes(text: str) -> str:
    """Apaga blockquotes, preservando offsets e quebras de linha."""
    for block in reversed(find_blockquotes(text)):
        text = _blank(text, block.start, block.end)
    return text


# ---------------------------------------------------------------- equações
@dataclass
class MathItem:
    kind: str  # "display" | "inline"
    latex: str
    start: int
    end: int
    line: int


def find_math(text: str, include_inline: bool = True) -> list[MathItem]:
    """Localiza equações em ordem de aparição.

    Blocos ```math/```latex contam como display. Qualquer outro bloco de código,
    código inline, comentários HTML e blockquotes são ignorados.
    """
    items: list[MathItem] = []
    source = mask_blockquotes(text)
    work = source
    for f in find_fences(source):
        if f.info.split()[:1] in (["math"], ["latex"], ["tex"]):
            body = source[f.body_start:f.body_end].strip("\n")
            items.append(MathItem("display", body.strip(), f.start, f.end, line_of(text, f.start)))
    work = mask_comments(mask_code(work))

    for regex, kind, group in ((DOLLAR_DISPLAY_RE, "display", 1), (BRACKET_DISPLAY_RE, "display", 1), (ENV_RE, "display", 0)):
        for m in list(regex.finditer(work)):
            items.append(MathItem(kind, m.group(group).strip(), m.start(), m.end(), line_of(text, m.start())))
            work = _blank(work, m.start(), m.end())

    if include_inline:
        for m in INLINE_RE.finditer(work):
            items.append(MathItem("inline", m.group(1).strip(), m.start(), m.end(), line_of(text, m.start())))

    items.sort(key=lambda it: it.start)
    return items


# ----------------------------------------------------------------- imagens
def normalize_image_ref(raw: str) -> str:
    ref = raw.strip()
    if ref.startswith("<") and ref.endswith(">"):
        ref = ref[1:-1].strip()
    return unquote(ref)


def find_images(text: str) -> list[tuple[str, int]]:
    """Retorna [(caminho, linha)] para imagens Markdown/HTML fora de código e blockquotes."""
    work = mask_code(mask_blockquotes(text))
    out = []
    for m in IMAGE_MD_RE.finditer(work):
        out.append((normalize_image_ref(m.group(2)), line_of(text, m.start())))
    for m in IMAGE_HTML_RE.finditer(work):
        out.append((normalize_image_ref(m.group(1)), line_of(text, m.start())))
    out.sort(key=lambda x: x[1])
    return out


# ------------------------------------------------------------------ slides
@dataclass
class Slide:
    index: int
    kind: str  # "divisor" | "conteudo"
    title: str
    start_line: int
    end_line: int
    text: str
    description: str | None = None
    literal: bool = False
    notes: str | None = None
    images: list[str] = field(default_factory=list)


def split_slides(body: str, line_offset: int = 0) -> list[Slide]:
    """Divide o corpo em slides.

    Se houver separadores ``---`` (fora de código), eles delimitam os slides.
    Caso contrário, cada ``#`` abre um divisor de seção e cada ``##`` um slide.
    Um blockquote não vazio imediatamente após esse heading vira ``description``
    e é removido do texto do slide; outros blockquotes são inválidos.
    """
    masked = mask_code(body)
    chunks: list[tuple[int, int]] = []
    seps = list(SEPARATOR_RE.finditer(masked))
    if seps:
        pos = 0
        for s in seps:
            chunks.append((pos, s.start()))
            pos = s.end()
        chunks.append((pos, len(body)))
    else:
        starts = [m.start() for m in HEADING_RE.finditer(masked) if len(m.group(1)) <= 2]
        if not starts or starts[0] != 0:
            starts = [0] + starts
        for i, st in enumerate(starts):
            chunks.append((st, starts[i + 1] if i + 1 < len(starts) else len(body)))

    slides: list[Slide] = []
    for start, end in chunks:
        chunk = body[start:end]
        visible_chunk = mask_comments(mask_code(chunk))
        if not visible_chunk.strip() and not NOTES_RE.search(chunk):
            continue
        heads = list(HEADING_RE.finditer(visible_chunk))
        level = len(heads[0].group(1)) if heads else 2
        title = heads[0].group(2).strip() if heads else ""
        quote_blocks = find_blockquotes(chunk)
        description = None
        description_block: Blockquote | None = None
        for block in quote_blocks:
            absolute_line = line_of(body, start + block.start) + line_offset
            if not heads:
                raise MarkdownBlockquoteError(
                    absolute_line,
                    "blockquotes são reservados para descrever um slide e devem vir logo após um heading # ou ##.",
                )
            if len(heads[0].group(1)) not in (1, 2):
                raise MarkdownBlockquoteError(
                    absolute_line,
                    "a descrição deve vir após o heading # ou ## que inicia o slide.",
                )
            heading_end = heads[0].end()
            if description_block is not None:
                raise MarkdownBlockquoteError(
                    absolute_line,
                    "use um único bloco de descrição logo após o heading; blockquotes no corpo do slide não são permitidos.",
                )
            if block.start < heading_end or chunk[heading_end:block.start].strip():
                raise MarkdownBlockquoteError(
                    absolute_line,
                    "o bloco de descrição deve vir logo após o heading # ou ##, antes do conteúdo do slide.",
                )
            if not block.text:
                raise MarkdownBlockquoteError(absolute_line, "a descrição do slide não pode estar vazia.")
            description = block.text
            description_block = block

        content_chunk = chunk
        if description_block is not None:
            content_chunk = _blank(chunk, description_block.start, description_block.end)
        notes = NOTES_RE.search(content_chunk)
        slides.append(Slide(
            index=len(slides) + 1,
            kind="divisor" if level == 1 else "conteudo",
            title=title,
            start_line=line_of(body, start) + line_offset,
            end_line=line_of(body, max(start, end - 1)) + line_offset,
            text=content_chunk.strip("\n"),
            description=description,
            literal=bool(LITERAL_RE.search(content_chunk)),
            notes=notes.group(1).strip() if notes else None,
            images=[p for p, _ in find_images(content_chunk)],
        ))
    return slides


def slide_for_line(slides: list[Slide], line: int) -> Slide | None:
    for s in slides:
        if s.start_line <= line <= s.end_line:
            return s
    return None


# ------------------------------------------------------- dados da capa
def cover_data(front: dict) -> tuple[dict, list[str], list[str]]:
    """Normaliza o bloco da capa/agradecimentos. Retorna (dados, erros, avisos)."""
    errors: list[str] = []
    warnings: list[str] = []
    titulo = front.get("titulo") or front.get("title")
    if not titulo or not str(titulo).strip():
        errors.append("Front matter sem 'titulo'.")
    autores_raw = front.get("autores") or front.get("authors") or []
    if isinstance(autores_raw, (str, dict)):
        autores_raw = [autores_raw]
    autores = []
    for a in autores_raw:
        if isinstance(a, str):
            a = {"nome": a}
        if not isinstance(a, dict) or not a.get("nome"):
            errors.append(f"Autor sem 'nome': {a!r}")
            continue
        contatos = a.get("contatos") or []
        if isinstance(contatos, str):
            contatos = [contatos]
        autores.append({
            "nome": str(a["nome"]).strip(),
            "cargo": (str(a["cargo"]).strip() if a.get("cargo") else None),
            "contatos": [str(c).strip() for c in contatos if str(c).strip()],
            "apresentador": bool(a.get("apresentador", False)),
        })
    if not autores:
        errors.append("Front matter sem 'autores'.")
    presenters = [a for a in autores if a["apresentador"]]
    if len(presenters) > 1:
        errors.append("Mais de um autor marcado com 'apresentador: true'.")
    if autores and not presenters:
        autores[0]["apresentador"] = True
        if len(autores) > 1:
            warnings.append("Nenhum autor marcado como apresentador; o primeiro foi usado para contatos e agradecimentos.")
    data = {"titulo": str(titulo).strip() if titulo else None, "autores": autores}

    agr = front.get("agradecimentos")
    presenter = next((a for a in autores if a["apresentador"]), None)
    if agr is False:
        errors.append("O slide de agradecimentos é obrigatório; remova 'agradecimentos: false'.")
    agr = agr if isinstance(agr, dict) else {}
    base = presenter or {}
    contatos = agr.get("contatos")
    if contatos is None:
        contatos = base.get("contatos", [])
    if isinstance(contatos, str):
        contatos = [contatos]
    data["agradecimentos"] = {
        "nome": agr.get("nome") or base.get("nome"),
        "cargo": agr.get("cargo", base.get("cargo")),
        "contatos": [str(c).strip() for c in contatos],
    }
    return data, errors, warnings

#!/usr/bin/env python3
"""Verifica uma transcrição gerada pela skill: figuras, legendas, títulos, equações e
arquivos gerados. Sai com código 1 se houver erros."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
IMG_LINE_RE = re.compile(r"^\s*(?:!\[[^\]]*\]\([^)\s]+\)\s*)+$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
NUMBERING_RE = re.compile(r"^(?:[\dIVXLC]+(?:\.\d+)*\.?|[A-Z]\.)\s+")
LABEL_RE = re.compile(r"^\s*([^\W\d_]+\.?)\s*(\d+)", re.UNICODE)
DESCRIPTION_RE = re.compile(r"^\s*\[(?:fig(?:ure|ura)?\.?|imagem|image)\b", re.IGNORECASE)
TABLE_ALT_RE = re.compile(r"^\s*tab(?:le|ela)\b", re.IGNORECASE)
WORK_DIR_RE = re.compile(r"^_transcricao_em_andamento(?:_\d+)?$")
MAX_NAME_BYTES = 200


class Report:
    def __init__(self):
        self.errors, self.warnings, self.info = [], [], []

    def error(self, msg): self.errors.append(msg)
    def warn(self, msg): self.warnings.append(msg)
    def note(self, msg): self.info.append(msg)


def content_lines(text):
    """Devolve (número da linha, linha) ignorando blocos de código cercados."""
    out, fenced = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if not fenced:
            out.append((i, line))
    return out


def is_all_caps_heading(title):
    title = NUMBERING_RE.sub("", title)
    title = re.sub(r"[*_`]", "", title)
    words = [w for w in re.findall(r"[^\W\d_]+", title, re.UNICODE)]
    upper = [w for w in words if len(w) >= 3 and w.isupper()]
    long_words = [w for w in words if len(w) >= 3]
    if not long_words or len(upper) != len(long_words):
        return False
    # Uma sigla isolada curta (ex.: "FFT") é aceitável; palavra longa ou várias palavras não.
    return len(upper) >= 2 or len(upper[0]) >= 6


def check_name(d, md, rep):
    name = d.name
    if WORK_DIR_RE.match(name):
        rep.warn(f"o diretório ainda tem o nome provisório '{name}'; renomeie-o para o título do documento (passo 7 do SKILL.md)")
    if len(name.encode("utf-8")) > MAX_NAME_BYTES:
        rep.error(f"nome do diretório tem {len(name.encode('utf-8'))} bytes (máximo {MAX_NAME_BYTES}); trunque com '…'")
    if name != name.rstrip(" ."):
        rep.error("o nome do diretório termina com espaço ou ponto")
    bad = set('/\\:*?"<>|') & set(name)
    if bad:
        rep.error(f"o nome do diretório contém caracteres proibidos: {''.join(sorted(bad))}")
    if md is not None and md.stem != name and not WORK_DIR_RE.match(name):
        rep.error(f"o arquivo Markdown '{md.name}' deveria se chamar '{name}.md'")


def find_markdown(d, rep):
    expected = d / f"{d.name}.md"
    if expected.is_file():
        return expected
    mds = sorted(d.glob("*.md"))
    if len(mds) == 1:
        return mds[0]
    if not mds:
        rep.error(f"nenhum arquivo .md encontrado em {d}")
    else:
        rep.error(f"vários .md em {d} e nenhum se chama '{d.name}.md': {', '.join(m.name for m in mds)}")
    return None


def check_markdown(d, md, rep):
    text = md.read_text(encoding="utf-8")
    lines = content_lines(text)
    by_number = dict(lines)
    referenced = set()

    for n, line in lines:
        m = HEADING_RE.match(line)
        if m and is_all_caps_heading(m.group(2)):
            rep.error(f"linha {n}: título em caixa alta: {m.group(2)!r}")
        if DESCRIPTION_RE.match(line):
            rep.error(f"linha {n}: descrição de figura entre colchetes não é permitida: {line.strip()[:60]!r}")

        imgs = IMG_RE.findall(line)
        for alt, target in imgs:
            path = (d / target).resolve()
            referenced.add(path)
            if not target.startswith("images/"):
                rep.warn(f"linha {n}: imagem fora de 'images/': {target}")
            if not path.is_file():
                rep.error(f"linha {n}: imagem referenciada não existe: {target}")
            if TABLE_ALT_RE.match(alt):
                rep.error(f"linha {n}: tabela inserida como imagem ({alt!r}); transcreva-a em Markdown/HTML")
        if not imgs:
            continue
        if not IMG_LINE_RE.match(line):
            rep.error(f"linha {n}: a linha da figura deve conter apenas a(s) imagem(ns)")
            continue
        # Formato: imagem(ns) / linha em branco / **legenda**
        blank, caption = by_number.get(n + 1), by_number.get(n + 2)
        if blank is None or blank.strip():
            rep.error(f"linha {n}: falta uma linha em branco entre a imagem e a legenda")
            continue
        if caption is None or not caption.strip():
            rep.error(f"linha {n}: figura sem legenda logo abaixo")
            continue
        cap = caption.strip()
        if cap.startswith(">"):
            rep.error(f"linha {n + 2}: legenda em citação ('>'); use parágrafo em negrito")
            continue
        if not (cap.startswith("**") and cap.endswith("**")):
            rep.error(f"linha {n + 2}: a legenda deve estar inteira em negrito (**...**)")
            continue
        alt_label, cap_label = LABEL_RE.match(imgs[0][0]), LABEL_RE.match(cap.strip("*"))
        if alt_label and cap_label:
            if alt_label.group(1).rstrip(".").lower() != cap_label.group(1).rstrip(".").lower():
                rep.error(f"linha {n}: texto alternativo {imgs[0][0]!r} não está no mesmo idioma/rótulo da legenda")
            elif alt_label.group(2) != cap_label.group(2):
                rep.error(f"linha {n}: número da figura no texto alternativo ({alt_label.group(2)}) "
                          f"difere da legenda ({cap_label.group(2)})")

    # Equações: blocos $$ devem estar balanceados.
    body = "\n".join(l for _, l in lines)
    if body.count("$$") % 2:
        rep.error("número ímpar de delimitadores '$$': há bloco de equação não fechado")

    # Notas de rodapé: toda chamada precisa de definição.
    calls = set(re.findall(r"\[\^([^\]]+)\](?!:)", body))
    defs = set(re.findall(r"^\[\^([^\]]+)\]:", body, re.MULTILINE))
    for c in sorted(calls - defs):
        rep.error(f"nota de rodapé [^{c}] sem definição")
    for c in sorted(defs - calls):
        rep.warn(f"nota de rodapé [^{c}] definida mas não chamada no texto")

    unreadable = len(re.findall(r"\[ilegível\]", body)); uncertain = len(re.findall(r"\[incerto:", body))
    if unreadable or uncertain:
        rep.note(f"marcações de incerteza: {unreadable} [ilegível], {uncertain} [incerto: ...]")
    return referenced


def check_images(d, referenced, rep):
    images_dir = d / "images"
    files = {p.resolve() for p in images_dir.glob("*.png")} if images_dir.is_dir() else set()
    for f in sorted(files - referenced):
        rep.error(f"recorte não referenciado no Markdown: images/{f.name}")
    if not files:
        rep.warn("nenhuma figura em 'images/'; confirme que o documento não tem figuras e declare isso no relatório")
    else:
        rep.note(f"{len(files)} recorte(s) de figura em images/")

    gen = d / "generated_files.json"
    if not gen.is_file():
        rep.warn("generated_files.json não encontrado; execute crop_images.py")
        return
    try:
        data = json.loads(gen.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.error(f"generated_files.json inválido: {exc}")
        return
    for s in data.get("stale_files", []):
        rep.error(f"arquivo antigo de execução anterior: {s} (apague-o e regenere)")
    listed = {(d / p).resolve() for p in data.get("images", [])}
    for f in sorted(files - listed):
        rep.error(f"images/{f.name} não foi gerado pelo último crop_images.py (arquivo antigo?)")
    for f in sorted(listed - files):
        rep.error(f"{f.name} consta em generated_files.json mas não existe em images/")
    if data.get("figure_source") == "page_png" and files:
        rep.warn("figuras recortadas da imagem da página; prefira renderizá-las do PDF (alta resolução)")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path, help="Diretório da transcrição")
    a = p.parse_args()
    d = a.directory.resolve()
    if not d.is_dir():
        raise SystemExit(f"Erro: diretório não encontrado: {a.directory}")
    rep = Report()
    md = find_markdown(d, rep)
    check_name(d, md, rep)
    referenced = check_markdown(d, md, rep) if md else set()
    check_images(d, referenced, rep)

    for title, items in (("ERROS", rep.errors), ("AVISOS", rep.warnings), ("INFORMAÇÕES", rep.info)):
        if items:
            print(f"{title} ({len(items)}):")
            for i in items:
                print(f"  - {i}")
    if not rep.errors:
        print("Verificação concluída sem erros." + (" Revise os avisos." if rep.warnings else ""))
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()

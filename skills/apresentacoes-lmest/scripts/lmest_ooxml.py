#!/usr/bin/env python3
"""Operações estruturais em pacotes PPTX descompactados.

Usado por ``assemble_deck.py``.
Faz apenas trabalho estrutural (duplicar, ordenar, remover slides e mídia
órfã). A edição de conteúdo fica em ``lmest_pptx.py`` (python-pptx).

Usa lxml, que preserva prefixos de namespace (ElementTree corrompe OOXML).
"""

from __future__ import annotations

import posixpath
import re
import shutil
import zipfile
from pathlib import Path

from lxml import etree

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
}
R_ID = f"{{{NS['r']}}}id"
SLIDE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
NOTES_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
SLIDE_CT = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
MEDIA_REL_SUFFIXES = ("/video", "/media", "/audio")


def _parse(path: Path) -> etree._ElementTree:
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    return etree.parse(str(path), parser)


def _write(tree: etree._ElementTree, path: Path) -> None:
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone=True)


def rels_path_for(part: Path) -> Path:
    return part.parent / "_rels" / (part.name + ".rels")


class Package:
    """Pacote PPTX descompactado em ``root``."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.ct_path = self.root / "[Content_Types].xml"
        self.pres_path = self.root / "ppt" / "presentation.xml"
        self.pres_rels_path = rels_path_for(self.pres_path)
        self.ct = _parse(self.ct_path)
        self.pres = _parse(self.pres_path)
        self.pres_rels = _parse(self.pres_rels_path)

    # ------------------------------------------------------------ abrir/salvar
    @classmethod
    def from_pptx(cls, pptx: Path, workdir: Path) -> "Package":
        workdir = Path(workdir)
        if workdir.exists():
            shutil.rmtree(workdir)
        workdir.mkdir(parents=True)
        with zipfile.ZipFile(pptx) as zf:
            zf.extractall(workdir)
        return cls(workdir)

    def save(self) -> None:
        _write(self.ct, self.ct_path)
        _write(self.pres, self.pres_path)
        _write(self.pres_rels, self.pres_rels_path)

    def to_pptx(self, out: Path) -> None:
        self.save()
        self._update_app_slide_count()
        out = Path(out)
        if out.exists():
            out.unlink()
        files = sorted(p for p in self.root.rglob("*") if p.is_file())
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(self.ct_path, "[Content_Types].xml")
            for f in files:
                arc = f.relative_to(self.root).as_posix()
                if arc == "[Content_Types].xml":
                    continue
                zf.write(f, arc)

    def _update_app_slide_count(self) -> None:
        app = self.root / "docProps" / "app.xml"
        if not app.exists():
            return
        text = app.read_text(encoding="utf-8")
        text = re.sub(r"<Slides>\d+</Slides>", f"<Slides>{len(self.slide_order())}</Slides>", text)
        app.write_text(text, encoding="utf-8")

    # ------------------------------------------------------------ consultas
    def _rel_by_id(self, rid: str):
        for rel in self.pres_rels.getroot():
            if rel.get("Id") == rid:
                return rel
        return None

    def slide_order(self) -> list[tuple[str, str]]:
        """Lista ``(rId, 'ppt/slides/slideN.xml')`` na ordem de exibição."""
        out = []
        lst = self.pres.getroot().find("p:sldIdLst", NS)
        if lst is None:
            return out
        for sid in lst:
            rid = sid.get(R_ID)
            rel = self._rel_by_id(rid)
            target = posixpath.normpath(posixpath.join("ppt", rel.get("Target")))
            out.append((rid, target))
        return out

    # ------------------------------------------------------------ edição
    def _next_rid(self) -> str:
        used = {int(r.get("Id")[3:]) for r in self.pres_rels.getroot() if r.get("Id", "").startswith("rId") and r.get("Id")[3:].isdigit()}
        return f"rId{max(used, default=0) + 1}"

    def _next_slide_number(self) -> int:
        nums = [int(m.group(1)) for p in (self.root / "ppt" / "slides").glob("slide*.xml")
                if (m := re.match(r"slide(\d+)\.xml$", p.name))]
        return max(nums, default=0) + 1

    def duplicate_slide(self, src_part: str) -> tuple[str, str]:
        """Duplica um slide. Retorna ``(rId, part)`` do novo slide (fora da ordem)."""
        src = self.root / src_part
        n = self._next_slide_number()
        new_part = f"ppt/slides/slide{n}.xml"
        dst = self.root / new_part
        shutil.copy2(src, dst)
        src_rels = rels_path_for(src)
        if src_rels.exists():
            tree = _parse(src_rels)
            for rel in list(tree.getroot()):
                if rel.get("Type") == NOTES_REL:  # notas não são clonadas
                    tree.getroot().remove(rel)
            _write(tree, rels_path_for(dst))
        override = etree.SubElement(self.ct.getroot(), f"{{{NS['ct']}}}Override")
        override.set("PartName", "/" + new_part)
        override.set("ContentType", SLIDE_CT)
        rid = self._next_rid()
        rel = etree.SubElement(self.pres_rels.getroot(), f"{{{NS['rel']}}}Relationship")
        rel.set("Id", rid)
        rel.set("Type", SLIDE_REL)
        rel.set("Target", f"slides/slide{n}.xml")
        return rid, new_part

    def set_order(self, rids: list[str]) -> None:
        root = self.pres.getroot()
        lst = root.find("p:sldIdLst", NS)
        old = {sid.get(R_ID): sid.get("id") for sid in lst} if lst is not None else {}
        used = {int(v) for v in old.values()}
        for sid in list(lst):
            lst.remove(sid)
        next_id = max(used | {255}) + 1
        for rid in rids:
            sid = etree.SubElement(lst, f"{{{NS['p']}}}sldId")
            if rid in old:
                sid.set("id", old.pop(rid))
            else:
                sid.set("id", str(next_id))
                next_id += 1
            sid.set(R_ID, rid)

    def remove_unlisted_slides(self) -> list[str]:
        listed = {rid for rid, _ in self.slide_order()}
        removed = []
        for rel in list(self.pres_rels.getroot()):
            if rel.get("Type") != SLIDE_REL or rel.get("Id") in listed:
                continue
            part = posixpath.normpath(posixpath.join("ppt", rel.get("Target")))
            self._delete_part(part, follow_notes=True)
            self.pres_rels.getroot().remove(rel)
            removed.append(part)
        return removed

    def _delete_part(self, part: str, follow_notes: bool = False) -> None:
        path = self.root / part
        rels = rels_path_for(path)
        if follow_notes and rels.exists():
            for rel in _parse(rels).getroot():
                if rel.get("Type") == NOTES_REL:
                    notes = posixpath.normpath(posixpath.join(posixpath.dirname(part), rel.get("Target")))
                    self._delete_part(notes)
        if path.exists():
            path.unlink()
        if rels.exists():
            rels.unlink()
        for ov in list(self.ct.getroot()):
            if ov.get("PartName") == "/" + part:
                self.ct.getroot().remove(ov)

    def remove_orphan_media(self) -> list[str]:
        referenced = set()
        for rels in self.root.rglob("*.rels"):
            base = rels.parent.parent.relative_to(self.root).as_posix()
            for rel in _parse(rels).getroot():
                if rel.get("TargetMode") == "External":
                    continue
                tgt = rel.get("Target", "")
                full = posixpath.normpath(posixpath.join(base, tgt)) if not tgt.startswith("/") else tgt.lstrip("/")
                referenced.add(full)
        removed = []
        media = self.root / "ppt" / "media"
        if media.exists():
            for f in media.iterdir():
                arc = f.relative_to(self.root).as_posix()
                if arc not in referenced:
                    f.unlink()
                    removed.append(arc)
        return removed

    # ------------------------------------------------------------ vídeos
    def strip_media_from_slide(self, part: str) -> int:
        """Converte vídeos/áudios embutidos em imagens estáticas (quadro de capa)."""
        path = self.root / part
        tree = _parse(path)
        count = 0
        for nvpr in tree.iter(f"{{{NS['p']}}}nvPr"):
            media_children = [c for c in nvpr if etree.QName(c).localname in ("videoFile", "audioFile", "extLst")]
            if any(etree.QName(c).localname in ("videoFile", "audioFile") for c in media_children):
                for c in media_children:
                    nvpr.remove(c)
                count += 1
        for h in list(tree.iter(f"{{{NS['a']}}}hlinkClick")):
            if "media" in (h.get("action") or ""):
                h.getparent().remove(h)
        timing = tree.getroot().find("p:timing", NS)
        if timing is not None and count:
            tree.getroot().remove(timing)
        _write(tree, path)
        rels = rels_path_for(path)
        if rels.exists():
            rt = _parse(rels)
            for rel in list(rt.getroot()):
                if rel.get("Type", "").endswith(MEDIA_REL_SUFFIXES):
                    rt.getroot().remove(rel)
            _write(rt, rels)
        return count

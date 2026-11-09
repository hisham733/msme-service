"""harvest.py — pull every usable picture out of what MSME actually sends.

Why: the receive stage only collects files already named `*.jpg/png/…`. But release packs usually hide
the pictures inside the attachment — the logo sits in the PDF letterhead, the ceremony photo sits in
the .docx. Measured 2026-10-23 on 30 published pairs: of the 17 articles where TARGET's featured image
matched no loose image file, **10 had that very picture (or the same logo artwork) embedded in a
supplied .pdf/.docx** — e.g. the ACCCIM, SME Malaysia and MICSEA logos were literally cropped out of
the PDF header, and TP-Link's MoU photo came from `word/media/image2.png`.

Nothing here writes into a release folder: harvested files land in a derived folder the selector reads.

Run:  python -m pipeline.harvest --folder "<EXACT NAME>"      # one release folder
      python -m pipeline.harvest --all                      # every folder (survey)
Out:  Files_from_MSME\\_harvest\\<release-slug>\\<source>_<nn>.<ext>   with harvest.json beside it
      (a SHORT derived path on purpose: a 100-character release folder plus the file name would pass
      the Windows 260-character limit, the reason D-009 moved the rendered pages to DLW\\)
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

MIN_BYTES = 2_000          # only a stub gate — a legitimate flat logo can be 2.4 KB
MIN_SIDE = 160             # a usable asset is at least this wide and tall
DOC_EXT = {".docx", ".pdf"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff"}
from msme import paths

HARVEST_ROOT = paths.DATA / "repurpose" / "harvest"


def slug_for(folder: Path) -> str:
    """A short, stable, filesystem-safe key for a release folder."""
    base = re.sub(r"[^A-Za-z0-9]+", "-", Path(folder).name).strip("-")[:56]
    tail = hashlib.sha1(Path(folder).name.encode("utf-8")).hexdigest()[:6]
    return f"{base}-{tail}"



def _keep(path: Path, w: int, h: int) -> bool:
    return w >= MIN_SIDE and h >= MIN_SIDE and w * h >= 40_000


def _save(folder: Path, stem: str, data: bytes, ext: str, harvest: Path, rows: list) -> None:
    from PIL import Image
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except Exception:  # noqa: BLE001
        pass
    if len(data) < MIN_BYTES:
        return
    try:
        with Image.open(io.BytesIO(data)) as im:
            w, h = im.size
            if not _keep(Path(stem), w, h):
                return
            im = im.convert("RGB")
    except Exception:  # noqa: BLE001 — not a decodable picture (wmf/emf/vector)
        return
    ext = ".jpg" if ext.lower() in (".wmf", ".emf", ".tif", ".tiff") else ext.lower()
    name = f"{stem}{ext}"
    harvest.mkdir(parents=True, exist_ok=True)
    dest = harvest / name
    n = 2
    while dest.exists():
        dest = harvest / f"{stem}-{n}{ext}"
        n += 1
    out = io.BytesIO()
    im.save(out, "JPEG", quality=92) if ext == ".jpg" else None
    if ext == ".jpg":
        dest.write_bytes(out.getvalue())
    else:
        dest.write_bytes(data)
    origin = ("pdf-header" if stem.endswith("_header")
              else "pdf-media" if stem.startswith("pdf_")
              else "docx-media" if stem.startswith("docx_") else "asset")
    rows.append({"file": dest.name, "source": stem.split("_")[0], "origin": origin,
                 "w": w, "h": h, "bytes": dest.stat().st_size})


def from_docx(path: Path, harvest: Path, rows: list) -> None:
    try:
        with zipfile.ZipFile(path) as z:
            for n in sorted(z.namelist()):
                if not n.startswith("word/media/"):
                    continue
                ext = Path(n).suffix
                if ext.lower() not in IMG_EXT | {".wmf", ".emf"}:
                    continue
                _save(path.parent, f"docx_{Path(path).stem[:18]}_{Path(n).stem}", z.read(n), ext,
                      harvest, rows)
    except Exception:  # noqa: BLE001
        pass


def from_pdf(path: Path, harvest: Path, rows: list) -> None:
    try:
        import pymupdf
    except Exception:  # noqa: BLE001 — pymupdf is optional; PDFs are skipped without it
        return
    try:
        doc = pymupdf.open(path)
    except Exception:  # noqa: BLE001
        return
    try:
        for pno in range(min(len(doc), 4)):          # media kits sit in the first pages
            page = doc[pno]
            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    data = doc.extract_image(xref)["image"]
                except Exception:  # noqa: BLE001
                    continue
                _save(path.parent, f"pdf_{path.stem[:18]}_p{pno + 1}x{xref}", data, ".jpg",
                      harvest, rows)
            # vector logos never appear in get_images(): render the header band and offer it too
            if pno == 0:
                try:
                    r = page.rect
                    band = pymupdf.Rect(r.x0, r.y0, r.x1, r.y0 + r.height * 0.18)
                    pix = page.get_pixmap(dpi=200, clip=band)
                    _save(path.parent, f"pdf_{path.stem[:18]}_header", pix.tobytes("png"), ".png",
                          harvest, rows)
                except Exception:  # noqa: BLE001
                    pass
    finally:
        doc.close()


def harvest_folder(folder: Path, force: bool = False, out_root: Path | None = None) -> dict:
    """Extract the embedded pictures of one release folder into the short derived root."""
    folder = Path(folder)
    harvest = Path(out_root or HARVEST_ROOT) / slug_for(folder)
    manifest = harvest / "harvest.json"
    if manifest.exists() and not force:
        try:
            return json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    rows: list = []
    docs = [p for p in sorted(folder.rglob("*"))
            if p.is_file() and p.suffix.lower() in DOC_EXT and "_harvest" not in p.parts]
    for d in docs:
        if d.suffix.lower() == ".docx":
            from_docx(d, harvest, rows)
        else:
            from_pdf(d, harvest, rows)
    result = {"folder": folder.name, "slug": slug_for(folder), "harvest_dir": str(harvest),
              "documents": [d.name for d in docs], "assets": rows, "count": len(rows)}
    if rows or docs:
        harvest.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result


def harvest_all(root: Path, force: bool = False) -> list:
    out = []
    for d in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        r = harvest_folder(d, force=force)
        if r.get("count"):
            out.append(r)
    return out


if __name__ == "__main__":
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    from .config import load_config
    cfg = load_config()
    root = Path(cfg["email_articles_root"])
    if "--all" in sys.argv:
        res = harvest_all(root)
        for r in res:
            print(f"{r['count']:>3} assets  {r['folder'][:56]}  from {len(r['documents'])} doc(s)")
        print(f"folders with harvested assets: {len(res)}")
    else:
        name = sys.argv[sys.argv.index("--folder") + 1]
        print(json.dumps(harvest_folder(root / name), indent=1, ensure_ascii=False))

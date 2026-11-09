"""assets.py — one place that answers "where is this picture?".

The image skill may legitimately choose a file that is **not** inside the release folder:
`pipeline/harvest.py` mines the supplied `.pdf`/`.docx` into `Files_from_MSME/_harvest/<slug>/`.
Until now `validate.py` and `build_site.py` each searched only `images/`, `originals/` and the folder
root, so a real-but-harvested asset failed `FEATURED_EXISTS` and the page could not be built.

Live case (2026-10-24, MG's dashboard test): *ACCCIMs PRESS STATEMENT ON THE NATIONAL BUDGET 2027*
reported `FEATURED_EXISTS — pdf_20261009  ACCCIM's_header.png` while that file was on disk, in the
harvest folder.

One resolver, used by every consumer, so this cannot drift again.
"""
from __future__ import annotations

from pathlib import Path

IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heif", ".heic"}


def harvest_dir(folder: Path) -> Path | None:
    """The harvest output folder for a release folder, if it exists."""
    try:
        from .harvest import HARVEST_ROOT, slug_for
    except Exception:  # noqa: BLE001
        return None
    d = Path(HARVEST_ROOT) / slug_for(Path(folder))
    return d if d.is_dir() else None


def search_roots(folder: Path) -> list[Path]:
    """Where an asset for this release may live, most-authoritative first."""
    folder = Path(folder)
    roots = [folder / "images", folder / "originals", folder]
    h = harvest_dir(folder)
    if h:
        roots.append(h)
    return roots


def resolve(folder: Path, *names: str) -> Path | None:
    """First existing file matching any of the given names, across every allowed root."""
    for name in names:
        if not name:
            continue
        name = name.strip().strip("`")
        p = Path(name)
        if p.is_absolute() and p.exists():
            return p
        for root in search_roots(folder):
            cand = root / p.name
            if cand.exists() and cand.is_file():
                return cand
    return None


def origin_of(folder: Path, path: Path | None) -> str:
    """`folder` (supplied loose file) · `harvest` (mined out of an attachment) · `external`."""
    if path is None:
        return "none"
    h = harvest_dir(folder)
    try:
        if h and Path(path).resolve().parent == Path(h).resolve():
            return "harvest"
    except OSError:
        pass
    return "folder"


def is_document_crop(folder: Path, path: Path | None) -> bool:
    """True when the file was rendered out of a document header (a crop, not supplied artwork).

    A header band is a picture of a *page*, not of a logo: it can carry the letterhead, a rule line and
    the first line of body text. Decision D-C: such a crop is never published automatically — it is
    raised for a human to confirm.
    """
    if path is None:
        return False
    return origin_of(folder, path) == "harvest" and path.name.endswith("_header.png")

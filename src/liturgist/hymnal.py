"""
Hymnal score loading for liturgist.

Loads hymn scores from a directory of PDFs indexed by hymn number or title
and converts them to base64 data URIs for embedding in templates. Each score
is a list of sheets (one per page).

PDF naming convention:
  {number}_{title}.pdf  e.g. 344_O-Sacred-Head.pdf  → number=344, title="O Sacred Head"
  {number}.pdf          e.g. 344.pdf                 → number=344, title=None
  {title}.pdf           e.g. O-Sacred-Head.pdf       → number=None, title="O Sacred Head"

Underscore delimits the number segment; hyphens stand in for spaces within titles.
"""

import base64
import re
from dataclasses import dataclass
from pathlib import Path

import fitz  # pymupdf


@dataclass
class HymnRef:
    number: int | None = None
    title: str | None = None


def _png_data_uri(png_bytes: bytes) -> str:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


def parse_hymn_ref(hymn_string: str) -> HymnRef:
    """Extract number and title from a schedule hymn string.

    The leading ``Hymn`` is optional.

    Examples::

        "Hymn 552 - Rejoice, All Ye Believers" → HymnRef(number=552, title="Rejoice, All Ye Believers")
        "552 - Rejoice, All Ye Believers"      → HymnRef(number=552, title="Rejoice, All Ye Believers")
        "Hymn 552"                             → HymnRef(number=552, title=None)
        "552"                                  → HymnRef(number=552, title=None)
        "Doxology"                             → HymnRef(number=None, title="Doxology")
        ""                                     → HymnRef(number=None, title=None)
    """
    hymn_string = hymn_string.strip()
    match = re.fullmatch(r"(?i)(?:Hymn\s+)?(\d+)(?:\s*-\s*(.+))?", hymn_string)
    if match:
        title = match.group(2)
        return HymnRef(
            number=int(match.group(1)), title=title.strip() if title else None
        )

    return HymnRef(title=hymn_string or None)


def parse_hymn_number(hymn_string: str) -> int | None:
    """Extract hymn number from a string like 'Hymn 552 - Rejoice, All Ye Believers'."""
    return parse_hymn_ref(hymn_string).number


def _parse_score_filename(stem: str) -> HymnRef:
    """Parse a PDF filename stem into number and title.

    Examples::

        "344_O-Sacred-Head" → HymnRef(number=344, title="O Sacred Head")
        "344"               → HymnRef(number=344, title=None)
        "O-Sacred-Head"     → HymnRef(number=None, title="O Sacred Head")
        "100-Songs"         → HymnRef(number=None, title="100 Songs")
    """
    match = re.match(r"^(\d+)_(.+)$", stem)
    if match:
        return HymnRef(
            number=int(match.group(1)), title=match.group(2).replace("-", " ")
        )

    if re.match(r"^\d+$", stem):
        return HymnRef(number=int(stem))

    return HymnRef(title=stem.replace("-", " "))


def _normalize_title(title: str) -> str:
    """Fold a title for matching: lowercase, collapse non-alphanumerics to single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _rasterize_pdf(pdf_path: Path, dpi: int = 300) -> list[str]:
    pages = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pixmap = page.get_pixmap(dpi=dpi)
            pages.append(_png_data_uri(pixmap.tobytes("png")))
    return pages


def _build_hymnal_index(hymnal_dir: Path) -> tuple[dict[int, str], dict[str, str]]:
    """Scan hymnal_dir for PDFs and return (by_number, by_title) stem dicts."""
    by_number: dict[int, str] = {}
    by_title: dict[str, str] = {}

    for path in sorted(hymnal_dir.glob("*.pdf")):
        stem = path.stem
        ref = _parse_score_filename(stem)
        if ref.number is not None and ref.number not in by_number:
            by_number[ref.number] = stem
        if ref.title is not None:
            by_title.setdefault(_normalize_title(ref.title), stem)

    return by_number, by_title


def load_hymn_images(stem: str, hymnal_dir: Path) -> list[str]:
    """Load sheets for a hymn PDF identified by its filename stem."""
    pdf_path = hymnal_dir / f"{stem}.pdf"
    return _rasterize_pdf(pdf_path) if pdf_path.is_file() else []


def load_hymnal_scores(hymns: str | list[str], hymnal_dir: Path) -> list[dict | None]:
    """Load scores for a list of hymns.

    Args:
        hymns: Single hymn string or list of hymn strings
              (e.g., "Hymn 552 - Rejoice, All Ye Believers")
        hymnal_dir: Directory containing PDFs named by number and/or title

    Returns:
        List parallel to hymns. Each entry is ``None`` (no matching file found)
        or ``{"number": int | None, "title": str | None, "sheets": list[str]}``.
        CSV string title takes precedence over the filename-derived title.
    """
    if isinstance(hymns, str):
        hymns = [hymns]

    by_number, by_title = _build_hymnal_index(hymnal_dir)

    scores = []
    for hymn_str in hymns:
        ref = parse_hymn_ref(hymn_str)

        stem = None
        if ref.number is not None:
            stem = by_number.get(ref.number)
        if stem is None and ref.title is not None:
            stem = by_title.get(_normalize_title(ref.title))

        if stem is None:
            scores.append(None)
            continue

        sheets = load_hymn_images(stem, hymnal_dir)
        if not sheets:
            scores.append(None)
            continue

        stem_ref = _parse_score_filename(stem)
        scores.append(
            {
                "number": ref.number if ref.number is not None else stem_ref.number,
                "title": ref.title if ref.title is not None else stem_ref.title,
                "sheets": sheets,
            }
        )

    return scores

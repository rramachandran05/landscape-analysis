"""Identifier normalization and BibTeX generation.

Canonical-ID assignment (FR-3) prefers, in order: arXiv ID, DOI, ``owner/repo``,
then a source-native fallback. Normalization here is what makes dedup (FR-4)
deterministic across sources.
"""

from __future__ import annotations

import re
from typing import Optional


_ARXIV_RE = re.compile(
    r"(?:arxiv:)?(?P<id>\d{4}\.\d{4,5})(?:v\d+)?", re.IGNORECASE
)
_OLD_ARXIV_RE = re.compile(
    r"(?:arxiv:)?(?P<id>[a-z\-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?", re.IGNORECASE
)


def normalize_arxiv_id(value: Optional[str]) -> Optional[str]:
    """Return a bare arXiv id (no version, no ``arXiv:`` prefix, no URL) or None.

    Accepts full URLs, ``arXiv:2301.00001v2``, old-style ``cs.AI/0701001`` etc.
    """
    if not value:
        return None
    v = value.strip()
    m = _ARXIV_RE.search(v)
    if m:
        return m.group("id")
    m = _OLD_ARXIV_RE.search(v)
    if m:
        return m.group("id").lower()
    return None


def normalize_doi(value: Optional[str]) -> Optional[str]:
    """Return a lowercase bare DOI (``10.x/...``) stripped of any URL prefix."""
    if not value:
        return None
    v = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "https://dx.doi.org/"):
        if v.startswith(prefix):
            v = v[len(prefix):]
            break
    v = v.strip()
    if not v.startswith("10."):
        # find an embedded DOI if present
        m = re.search(r"10\.\d{4,9}/\S+", v)
        if m:
            return m.group(0)
        return None
    return v


def normalize_repo(value: Optional[str]) -> Optional[str]:
    """Return ``owner/repo`` (lowercased) from a full name or GitHub URL."""
    if not value:
        return None
    v = value.strip()
    v = re.sub(r"^https?://github\.com/", "", v, flags=re.IGNORECASE)
    v = v.rstrip("/")
    v = re.sub(r"\.git$", "", v)
    parts = v.split("/")
    if len(parts) >= 2 and parts[0] and parts[1]:
        return f"{parts[0]}/{parts[1]}".lower()
    return None


def canonical_id(
    *,
    arxiv_id: Optional[str] = None,
    doi: Optional[str] = None,
    repo: Optional[str] = None,
    source: str = "",
    source_native_id: str = "",
) -> str:
    """Assign a canonical ID using the FR-3 precedence.

    Returned IDs are *type-prefixed* so the same artifact always collapses to
    one key and different artifact kinds never collide:
    ``arXiv:<id>`` / ``doi:<doi>`` / ``github:<owner/repo>`` / ``<source>:<native>``.
    """
    ax = normalize_arxiv_id(arxiv_id)
    if ax:
        return f"arXiv:{ax}"
    d = normalize_doi(doi)
    if d:
        return f"doi:{d}"
    r = normalize_repo(repo)
    if r:
        return f"github:{r}"
    native = (source_native_id or "").strip()
    src = (source or "unknown").strip()
    return f"{src}:{native}" if native else f"{src}:unknown"


# --- BibTeX ----------------------------------------------------------------- #
def _bibtex_key(authors: list[str], year: Optional[int], title: str) -> str:
    first = ""
    if authors:
        first = re.sub(r"[^A-Za-z]", "", authors[0].split()[-1]) if authors[0].split() else ""
    yr = str(year) if year else "n.d."
    word = ""
    for tok in re.findall(r"[A-Za-z]+", title):
        if len(tok) > 3:
            word = tok.lower()
            break
    key = f"{first}{yr}{word}".strip()
    return key or "ref"


def _escape_bibtex(s: str) -> str:
    return (s or "").replace("{", "").replace("}", "").replace("\n", " ").strip()


def make_bibtex(
    *,
    entry_type: str,
    authors: list[str],
    year: Optional[int],
    title: str,
    venue_or_repo: str = "",
    doi: Optional[str] = None,
    url: str = "",
    arxiv_id: Optional[str] = None,
) -> str:
    """Generate a minimal, deterministic BibTeX entry from objective metadata."""
    key = _bibtex_key(authors, year, title)
    fields = []
    if authors:
        fields.append(("author", " and ".join(_escape_bibtex(a) for a in authors)))
    fields.append(("title", _escape_bibtex(title)))
    if year:
        fields.append(("year", str(year)))
    if venue_or_repo:
        field_name = "journal" if entry_type == "article" else "howpublished"
        fields.append((field_name, _escape_bibtex(venue_or_repo)))
    if arxiv_id:
        fields.append(("eprint", arxiv_id))
        fields.append(("archivePrefix", "arXiv"))
    if doi:
        fields.append(("doi", doi))
    if url:
        fields.append(("url", url))
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields)
    return f"@{entry_type}{{{key},\n{body}\n}}"

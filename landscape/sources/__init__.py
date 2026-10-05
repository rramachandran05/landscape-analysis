"""Source adapters. Each exposes ``search(query, date_window) -> [RawHit]`` and
``normalize(RawHit) -> Record`` (FR-1, FR-2).

``get_adapter(name, client)`` is the registry the pipeline uses to instantiate
adapters by their CLI name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import SourceAdapter, SourceError
from .arxiv import ArxivAdapter
from .github import GitHubAdapter
from .openalex import OpenAlexAdapter
from .semanticscholar import SemanticScholarAdapter

if TYPE_CHECKING:
    from ..http import HttpClient

_REGISTRY = {
    "arxiv": ArxivAdapter,
    "github": GitHubAdapter,
    "openalex": OpenAlexAdapter,
    "semanticscholar": SemanticScholarAdapter,
}

# Sources run by default when the caller does not name any explicitly.
DEFAULT_SOURCES = ("arxiv", "github", "openalex")

ALL_SOURCES = tuple(_REGISTRY.keys())


def get_adapter(name: str, client: "HttpClient") -> SourceAdapter:
    key = name.strip().lower()
    if key not in _REGISTRY:
        raise KeyError(
            f"unknown source '{name}'. Known: {', '.join(sorted(_REGISTRY))}"
        )
    return _REGISTRY[key](client)


__all__ = [
    "SourceAdapter",
    "SourceError",
    "ArxivAdapter",
    "GitHubAdapter",
    "OpenAlexAdapter",
    "SemanticScholarAdapter",
    "get_adapter",
    "DEFAULT_SOURCES",
    "ALL_SOURCES",
]

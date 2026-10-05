"""Landscape Analysis — Phase A (deterministic collection tool).

This package implements the *tool* half of the Landscape Analysis capability:
the deterministic, re-runnable collection of scholarly + code artifacts from
named structured sources (arXiv, GitHub, OpenAlex, optionally Semantic Scholar)
into a single durable manifest (the source of truth).

The tool writes only objective fields. Agent-owned (judgment) fields are never
created or overwritten here — that is the contract that makes Update safe and
the two phases independently buildable. See ``MANIFEST_VERSION`` and
``landscape.models`` for the frozen schema.
"""

from .models import (
    MANIFEST_VERSION,
    AGENT_OWNED_FIELDS,
    TOOL_OWNED_FIELDS,
    DateWindow,
    RawHit,
    Record,
)

__all__ = [
    "MANIFEST_VERSION",
    "AGENT_OWNED_FIELDS",
    "TOOL_OWNED_FIELDS",
    "DateWindow",
    "RawHit",
    "Record",
]

__version__ = "0.1.0"

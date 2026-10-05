"""CLI entrypoint (FR-1 surface).

    python -m landscape collect --theme "GeoAI FMs" \\
        --query "geospatial foundation model" \\
        --since 2023-01 --sources arxiv,github,openalex [--update]

Per-source query overrides:
    --source-query arxiv="abs:foundation model AND cat:cs.CV"

Emits a machine-readable run summary (JSON) to stdout (FR-10).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .models import DateWindow
from .pipeline import collect
from .sources import ALL_SOURCES, DEFAULT_SOURCES


def _parse_source_query(values: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in values or []:
        if "=" not in item:
            raise argparse.ArgumentTypeError(
                f"--source-query expects NAME=QUERY, got {item!r}"
            )
        name, _, query = item.partition("=")
        out[name.strip().lower()] = query
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="landscape", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    c = sub.add_parser("collect", help="collect artifacts into a theme manifest")
    c.add_argument("--theme", required=True, help="research theme (manifest key)")
    c.add_argument("--query", default="", help="base query applied to every source")
    c.add_argument(
        "--source-query",
        action="append",
        default=[],
        metavar="NAME=QUERY",
        help="per-source query override (repeatable)",
    )
    c.add_argument("--since", default=None, help="start of date window (YYYY[-MM[-DD]])")
    c.add_argument("--until", default=None, help="end of date window (YYYY[-MM[-DD]])")
    c.add_argument(
        "--sources",
        default=",".join(DEFAULT_SOURCES),
        help=f"comma list; known: {','.join(ALL_SOURCES)}",
    )
    c.add_argument(
        "--update",
        action="store_true",
        help="Update mode: fetch only new canonical IDs; preserve agent fields",
    )
    c.add_argument("--base-dir", default=".", help="directory holding theme dirs")
    c.add_argument("--description", default="", help="theme description (objective)")
    c.add_argument("--mailto", default=None, help="contact email for polite API pools")
    c.add_argument("--max-results", type=int, default=200, help="cap per source")
    c.add_argument("--cache-dir", default=None, help="HTTP response cache dir")
    c.add_argument("-v", "--verbose", action="count", default=0, help="-v / -vv")
    return parser


def _resolve_queries(args, sources: list[str]) -> dict[str, str]:
    queries = _parse_source_query(args.source_query)
    if args.query:
        queries.setdefault("*", args.query)
    missing = [s for s in sources if not (queries.get(s) or queries.get("*"))]
    if missing:
        raise SystemExit(
            f"no query for source(s): {', '.join(missing)} "
            "(pass --query or --source-query NAME=...)"
        )
    return queries


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=[logging.WARNING, logging.INFO, logging.DEBUG][min(args.verbose, 2)],
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    if args.command != "collect":  # pragma: no cover - argparse enforces
        raise SystemExit(f"unknown command {args.command!r}")

    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in sources if s not in ALL_SOURCES]
    if unknown:
        raise SystemExit(f"unknown source(s): {', '.join(unknown)}")

    queries = _resolve_queries(args, sources)

    summary = collect(
        theme=args.theme,
        queries=queries,
        date_window=DateWindow(since=args.since, until=args.until),
        sources=sources,
        base_dir=Path(args.base_dir),
        mode="update" if args.update else "create",
        description=args.description,
        mailto=args.mailto,
        max_results=args.max_results,
        cache_dir=args.cache_dir,
    )

    json.dump(summary, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

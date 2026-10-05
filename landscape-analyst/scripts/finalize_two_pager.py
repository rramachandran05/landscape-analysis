#!/usr/bin/env python3
"""Finalize the 2-pager: collect cited papers and render a PDF.

Two deliverable-finishing steps the analyst runs after the 2-pager is written
and has passed `check_reports.py`:

  1. Copy the local PDF of every resource CITED in the 2-pager (by canonical
     [id]) from its manifest `local_path` into `{theme}/curated-papers/`, so the
     evidence behind the synthesis travels with the report. Metadata-only cited
     resources (no PDF) are reported, not invented.

  2. Render the 2-pager Markdown (synthesis + cluster profiles) to PDF next to
     the .md.
     Tries renderers in order until one works: weasyprint, xhtml2pdf, then the
     macOS `cupsfilter`. (Markdown -> HTML via the `markdown` package.)

Only reads the manifest (never writes it) and only touches files under the
theme dir — it honors the field-ownership contract by construction.

Usage:
    python finalize_two_pager.py {theme}/manifest.json --two-pager two_pager.md \
        [--papers-dir {theme}/curated-papers] [--pdf {theme}/two_pager.pdf] [--no-pdf]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ID_RE = re.compile(r"\[([A-Za-z][A-Za-z0-9]*:[^\]\s][^\]]*)\]")


def cited_ids(text: str) -> list[str]:
    seen, out = set(), []
    for m in ID_RE.finditer(text):
        cid = m.group(1).strip()
        if cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


def copy_cited_pdfs(by_id: dict, ids: list[str], papers_dir: Path) -> dict:
    papers_dir.mkdir(parents=True, exist_ok=True)
    copied, no_pdf, missing, unknown = [], [], [], []
    for cid in ids:
        r = by_id.get(cid)
        if r is None:
            unknown.append(cid)
            continue
        lp = r.get("local_path")
        if not (r.get("pdf_available") and lp):
            no_pdf.append(cid)
            continue
        src = Path(lp)
        if not src.exists():
            missing.append(cid)
            continue
        dst = papers_dir / src.name
        shutil.copy2(src, dst)
        copied.append(dst.name)
    return {"copied": copied, "no_pdf": no_pdf, "missing": missing, "unknown": unknown}


def md_to_html(md_text: str, title: str) -> str:
    import markdown  # ships with most Python installs; pip install markdown if absent
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
    css = """
      @page { size: Letter; margin: 1.6cm; }
      body { font-family: Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.4; color: #111; }
      h1 { font-size: 18pt; } h2 { font-size: 13pt; margin-top: 14pt; border-bottom: 1px solid #ccc; }
      h3 { font-size: 11pt; margin-top: 10pt; } code { font-family: monospace; font-size: 9pt; }
      table { border-collapse: collapse; width: 100%; font-size: 8pt; }
      th, td { border: 1px solid #bbb; padding: 3px 5px; text-align: left; vertical-align: top; }
      li { margin: 1px 0; } em { color: #444; }
    """
    return f"<html><head><meta charset='utf-8'><title>{title}</title><style>{css}</style></head><body>{body}</body></html>"


def render_pdf(md_path: Path, pdf_path: Path) -> str:
    md_text = md_path.read_text()
    html = md_to_html(md_text, md_path.stem)
    # backend 1: weasyprint (best fidelity, needs system libs)
    try:
        from weasyprint import HTML  # type: ignore
        HTML(string=html).write_pdf(str(pdf_path))
        return "weasyprint"
    except Exception:
        pass
    # backend 2: xhtml2pdf / pisa (pure python)
    try:
        from xhtml2pdf import pisa  # type: ignore
        with open(pdf_path, "wb") as fh:
            status = pisa.CreatePDF(html, dest=fh)
        if not status.err:
            return "xhtml2pdf"
    except Exception:
        pass
    # backend 3: macOS cupsfilter (html -> pdf)
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tf:
            tf.write(html)
            tmp_html = tf.name
        with open(pdf_path, "wb") as out:
            r = subprocess.run(["cupsfilter", "-i", "text/html", tmp_html],
                               stdout=out, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and pdf_path.exists() and pdf_path.stat().st_size > 0:
            return "cupsfilter"
    except Exception:
        pass
    return ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--two-pager", required=True)
    ap.add_argument("--papers-dir")
    ap.add_argument("--pdf")
    ap.add_argument("--no-pdf", action="store_true", help="skip PDF rendering")
    args = ap.parse_args(argv)

    manifest = json.loads(Path(args.manifest).read_text())
    by_id = {r["id"]: r for r in manifest.get("resources", [])}
    tp = Path(args.two_pager)
    theme_dir = Path(args.manifest).parent
    papers_dir = Path(args.papers_dir) if args.papers_dir else theme_dir / "curated-papers"
    pdf_path = Path(args.pdf) if args.pdf else tp.with_suffix(".pdf")

    ids = cited_ids(tp.read_text())
    res = copy_cited_pdfs(by_id, ids, papers_dir)
    print(f"cited resources: {len(ids)}")
    print(f"copied {len(res['copied'])} PDF(s) -> {papers_dir}")
    if res["no_pdf"]:
        print(f"  no PDF (metadata-only), not copied: {', '.join(res['no_pdf'])}")
    if res["missing"]:
        print(f"  WARN local_path missing on disk: {', '.join(res['missing'])}")
    if res["unknown"]:
        print(f"  WARN cited id not in manifest: {', '.join(res['unknown'])}")

    if not args.no_pdf:
        engine = render_pdf(tp, pdf_path)
        if engine:
            print(f"rendered PDF via {engine} -> {pdf_path}")
        else:
            print("WARN no PDF backend available (tried weasyprint, xhtml2pdf, cupsfilter); "
                  "install one, e.g. `pip install xhtml2pdf`", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

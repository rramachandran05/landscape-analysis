"""Offline end-to-end pipeline test (create -> agent curates -> update).

A fake adapter replaces network sources so the run flow, dedup, manifest
ownership and Update set-difference can be exercised without hitting any API.
"""

import copy
import json

import pytest

from landscape.models import DateWindow, Record
from landscape.pipeline import collect
from landscape.sources.base import SourceAdapter


class FakeAdapter(SourceAdapter):
    name = "fake"

    def __init__(self, client, records):
        super().__init__(client)
        self._records = records

    def search(self, query, date_window):  # pragma: no cover - unused
        return []

    def normalize(self, hit):  # pragma: no cover - unused
        raise NotImplementedError

    def collect(self, query, date_window):
        out = []
        for r in self._records:
            c = copy.deepcopy(r)
            c.query_that_found_it = query
            out.append(c)
        return out


def _install(monkeypatch, registry):
    def fake_get_adapter(name, client):
        return FakeAdapter(client, registry[name])

    monkeypatch.setattr("landscape.pipeline.get_adapter", fake_get_adapter)


def test_create_then_update_preserves_curation(tmp_path, monkeypatch):
    paperA = Record(source="arxiv", arxiv_id="2301.00001", title="Paper A", abstract="x")
    paperA_dup = Record(source="openalex", arxiv_id="2301.00001", doi="10.1/a", title="Paper A")
    paperB = Record(source="openalex", doi="10.2/b", title="Paper B")

    _install(monkeypatch, {"arxiv": [paperA], "openalex": [paperA_dup, paperB]})

    summary = collect(
        theme="GeoAI FMs",
        queries={"*": "geospatial foundation model"},
        date_window=DateWindow(since="2023-01"),
        sources=["arxiv", "openalex"],
        base_dir=tmp_path,
        mode="create",
    )

    assert summary["counts"]["queried"] == 3
    assert summary["counts"]["new"] == 2          # A (merged) + B
    assert summary["counts"]["duplicate"] == 1    # the A duplicate collapsed
    assert summary["total_resources"] == 2

    manifest_path = tmp_path / "geoai-fms" / "manifest.json"
    data = json.loads(manifest_path.read_text())
    ids = {r["id"] for r in data["resources"]}
    assert ids == {"arXiv:2301.00001", "doi:10.2/b"}
    # merged A carries DOI filled from the OpenAlex duplicate -> cross-linkable
    a = next(r for r in data["resources"] if r["id"] == "arXiv:2301.00001")
    assert a["doi"] == "10.1/a"
    assert a["status"] == "raw"

    # --- agent curates A in the manifest ---
    a["status"] = "curated"
    a["relevance_score"] = 0.95
    a["relevance_rationale"] = "directly on-theme"
    a["dimensions"] = {"modality": "satellite imagery"}
    a["cluster_id"] = "c1"
    manifest_path.write_text(json.dumps(data))

    # --- update: arXiv returns A again (dup), OpenAlex returns a new paper C ---
    paperC = Record(source="openalex", doi="10.3/c", title="Paper C")
    _install(monkeypatch, {"arxiv": [paperA], "openalex": [paperC]})

    summary2 = collect(
        theme="GeoAI FMs",
        queries={"*": "geospatial foundation model"},
        date_window=DateWindow(since="2023-01"),
        sources=["arxiv", "openalex"],
        base_dir=tmp_path,
        mode="update",
    )

    assert summary2["mode"] == "update"
    assert summary2["counts"]["new"] == 1         # only C
    assert summary2["counts"]["duplicate"] == 1   # A already present
    assert summary2["total_resources"] == 3

    data2 = json.loads(manifest_path.read_text())
    a2 = next(r for r in data2["resources"] if r["id"] == "arXiv:2301.00001")
    # Agent-owned fields survived the update untouched (FR-8).
    assert a2["status"] == "curated"
    assert a2["relevance_score"] == 0.95
    assert a2["dimensions"] == {"modality": "satellite imagery"}
    assert a2["cluster_id"] == "c1"
    # Two runs recorded.
    assert len(data2["runs"]) == 2
    assert [run["mode"] for run in data2["runs"]] == ["create", "update"]


def test_empty_results_is_valid_run(tmp_path, monkeypatch):
    _install(monkeypatch, {"arxiv": []})
    summary = collect(
        theme="Empty Theme",
        queries={"*": "nothing matches"},
        date_window=DateWindow(),
        sources=["arxiv"],
        base_dir=tmp_path,
        mode="create",
    )
    assert summary["counts"] == {
        "queried": 0, "new": 0, "duplicate": 0, "downloaded": 0, "metadata_only": 0,
    }
    assert summary["total_resources"] == 0
    assert (tmp_path / "empty-theme" / "manifest.json").exists()

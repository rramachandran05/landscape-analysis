import json

import pytest

from landscape.manifest import Manifest, ManifestError, assign_canonical_id
from landscape.models import Record


def _mk(**kw):
    r = Record(**kw)
    assign_canonical_id(r)
    return r


def test_init_and_save_roundtrip(tmp_path):
    m = Manifest.load_or_init(tmp_path / "geoai", "GeoAI FMs", "desc")
    m.add_resource(_mk(source="arxiv", arxiv_id="2301.00001", title="A"))
    m.add_run({"run_id": "r1", "timestamp": "t", "mode": "create", "sources": []})
    m.save()

    data = json.loads((tmp_path / "geoai" / "manifest.json").read_text())
    assert data["theme"] == "GeoAI FMs"
    assert data["manifest_version"] == "1.0"
    assert len(data["resources"]) == 1
    assert data["resources"][0]["status"] == "raw"


def test_partition_new(tmp_path):
    m = Manifest.load_or_init(tmp_path / "t", "T")
    m.add_resource(_mk(source="arxiv", arxiv_id="2301.00001", title="A"))
    incoming = [
        _mk(source="arxiv", arxiv_id="2301.00001", title="A"),  # dup
        _mk(source="arxiv", arxiv_id="2301.00002", title="B"),  # new
    ]
    new, dup = m.partition_new(incoming)
    assert [r.id for r in new] == ["arXiv:2301.00002"]
    assert [r.id for r in dup] == ["arXiv:2301.00001"]


def test_add_resource_refuses_overwrite(tmp_path):
    m = Manifest.load_or_init(tmp_path / "t", "T")
    m.add_resource(_mk(source="arxiv", arxiv_id="2301.00001", title="A"))
    with pytest.raises(ManifestError):
        m.add_resource(_mk(source="arxiv", arxiv_id="2301.00001", title="A again"))


def test_agent_fields_preserved_and_drift_guard(tmp_path):
    m = Manifest.load_or_init(tmp_path / "t", "T")
    m.add_resource(_mk(source="arxiv", arxiv_id="2301.00001", title="A"))
    m.save()

    # Simulate the agent curating the record.
    data = json.loads(m.path.read_text())
    rec = data["resources"][0]
    rec["status"] = "curated"
    rec["relevance_score"] = 0.9
    rec["dimensions"] = {"method": "transformer"}
    m.path.write_text(json.dumps(data))

    # Reload (as Update would) and snapshot.
    m2 = Manifest.load_or_init(tmp_path / "t", "T")
    snap = m2.snapshot_agent_fields()
    # Tool-only objective mutation: merge cross-links — allowed.
    m2.merge_cross_links("arXiv:2301.00001", ["doi:10.1/x"])
    m2.assert_no_agent_field_drift(snap)  # must not raise
    assert m2._index["arXiv:2301.00001"]["status"] == "curated"
    assert m2._index["arXiv:2301.00001"]["cross_links"] == ["doi:10.1/x"]


def test_incompatible_version_rejected(tmp_path):
    d = tmp_path / "t"
    d.mkdir()
    (d / "manifest.json").write_text(json.dumps({
        "manifest_version": "2.0", "theme": "T", "resources": [], "runs": [],
    }))
    with pytest.raises(ManifestError):
        Manifest.load_or_init(d, "T")

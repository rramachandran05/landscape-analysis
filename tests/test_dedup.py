from landscape import dedup
from landscape.manifest import assign_canonical_id
from landscape.models import Record


def _mk(**kw):
    r = Record(**kw)
    assign_canonical_id(r)
    return r


def test_merge_collapses_same_arxiv_across_sources():
    # Same paper from arXiv and OpenAlex (OpenAlex detected the arXiv id).
    a = _mk(source="arxiv", arxiv_id="2301.00001", title="Paper", abstract="long abstract")
    b = _mk(source="openalex", arxiv_id="2301.00001", doi="10.1/x", title="Paper",
            venue_or_repo="NeurIPS", year=2023)
    res = dedup.merge_duplicates([a, b])
    assert len(res.records) == 1
    assert res.duplicates_collapsed == 1
    merged = res.records[0]
    assert merged.id == "arXiv:2301.00001"
    assert merged.source == "arxiv"            # higher priority source kept as base
    assert merged.doi == "10.1/x"              # blank filled from openalex
    assert merged.venue_or_repo == "arXiv" or merged.venue_or_repo == "NeurIPS"
    assert merged.year == 2023


def test_cross_links_on_shared_doi_different_canonical():
    # arXiv record (canonical arXiv:..) and OpenAlex record (canonical doi:..)
    # share a DOI but no arXiv id overlap -> cross-link, not merge.
    a = _mk(source="arxiv", arxiv_id="2301.00002", doi="10.1/shared", title="A")
    b = _mk(source="openalex", doi="10.1/shared", title="A")
    assert a.id != b.id
    dedup.assign_cross_links([a, b])
    assert b.id in a.cross_links
    assert a.id in b.cross_links


def test_no_cross_link_without_shared_identifier():
    a = _mk(source="arxiv", arxiv_id="2301.00001", title="A")
    b = _mk(source="arxiv", arxiv_id="2301.00002", title="B")
    dedup.assign_cross_links([a, b])
    assert a.cross_links == []
    assert b.cross_links == []
